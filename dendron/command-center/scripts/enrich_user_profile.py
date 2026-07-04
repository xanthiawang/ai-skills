#!/usr/bin/env python3
"""
Enrich user.*.md with operational facts via LLM synthesis.

The static rolodex captures declarative facts (role, contact info, last
meeting). This script extracts *operational* facts: what someone optimizes
for, what they avoid, what register/cadence works with them, specific
phrasings that have landed. It does this by reading the existing profile
(plus optionally recent meet.*.md mentions) and asking Claude to synthesize.

Result is appended to the user.*.md under a clearly marked section, so the
change is fully reversible by deleting that section.

Usage:
    enrich_user_profile.py user.tony-wyss-coray             # DRY RUN by default
    enrich_user_profile.py user.tony-wyss-coray --run       # actually call API
    enrich_user_profile.py --all                            # batch dry-run
    enrich_user_profile.py --all --run --confirm            # batch live (needs --confirm)
    enrich_user_profile.py user.alice --include-meets 5     # add last 5 meeting mentions
    enrich_user_profile.py --estimate-cost                  # cost estimate over --all

Idempotent: skips profiles that already have a `## Operational Profile`
section dated within the last 90 days.

Requires `anthropic` SDK + `ANTHROPIC_API_KEY` for --run.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

VAULT = Path("/Users/A.Y/Documents/Manual Library/Dendron/notes")

MODEL = "claude-sonnet-4-5"  # cheaper than opus, good enough for synthesis
MAX_TOKENS_OUT = 800
TOKENS_PER_CHAR = 0.27  # rough estimate for English text
INPUT_PRICE_PER_MTOK = 3.0
OUTPUT_PRICE_PER_MTOK = 15.0

SECTION_HEADER_RE = re.compile(r"^## Operational Profile \(synthesized (\d{4}-\d{2}-\d{2})\)", re.M)

PROMPT_TEMPLATE = """You are reading a person profile that Albert (Kejun) Ying maintains in his Dendron knowledge vault. The profile mixes declarative facts (role, contact, last meetings) with raw interaction observations (email threads, chat snippets, decision notes).

Your task: synthesize *operational* facts an agent could use to interact more effectively with this person on Albert's behalf. Do NOT restate the declarative facts. Focus on what's *implicit* in the raw observations.

Read the profile + any meeting excerpts below. Produce a markdown section with exactly these subsections (omit any subsection if the source data doesn't support it — partial output is fine, fabrication is not):

### Optimizes for
What this person seems to be optimizing for in their work or in their interactions with Albert. 1-3 bullets, each grounded in a specific observation from the source.

### Avoids / friction points
What they push back on, ignore, or seem uncomfortable with. 1-3 bullets.

### What works
Specific framings, registers, cadences, or phrases that have landed well in past interactions. 1-3 bullets.

### Open operational threads
Anything implicit that's never been resolved — a question they keep returning to, an offer that's been left hanging, a topic that produces conflict. 0-2 bullets.

Rules:
- Cite the *specific evidence* from the source for each bullet (e.g., "based on the 4/24 email about X..."). Don't generalize beyond what's there.
- If the profile is mostly empty / generic, output `(insufficient signal — profile too thin for synthesis)` and stop. Don't pad.
- No sentences praising the person; this is for Albert's eyes, not theirs.
- No em-dashes (Albert's style rule).
- 200 words max total.

PROFILE
{profile}

{meetings_section}"""


def find_profile(slug_or_name: str) -> Path:
    """Accepts user.firstname-lastname or just firstname-lastname."""
    candidates = [
        VAULT / f"{slug_or_name}.md",
        VAULT / f"user.{slug_or_name}.md",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"No profile found matching {slug_or_name}")


def has_recent_synthesis(text: str, max_age_days: int = 90) -> bool:
    m = SECTION_HEADER_RE.search(text)
    if not m:
        return False
    try:
        dt = datetime.strptime(m.group(1), "%Y-%m-%d")
        age = (datetime.now() - dt).days
        return age < max_age_days
    except ValueError:
        return False


def gather_meeting_mentions(profile_path: Path, n: int) -> str:
    """Pull last N meet.*.md files mentioning this person's first/last name."""
    if n <= 0:
        return ""
    name_parts = profile_path.stem.replace("user.", "").split("-")
    if len(name_parts) < 2:
        return ""
    first, last = name_parts[0], name_parts[-1]
    pattern_terms = [first.capitalize(), last.capitalize(), f"user.{profile_path.stem.replace('user.', '')}"]

    meet_files = sorted(VAULT.glob("meet.*.md"), reverse=True)
    matches = []
    for fp in meet_files:
        if len(matches) >= n:
            break
        try:
            text = fp.read_text(errors="ignore")
        except Exception:
            continue
        if any(t in text for t in pattern_terms):
            matches.append((fp.name, text[:2500]))

    if not matches:
        return ""
    out = ["RECENT MEETING EXCERPTS"]
    for name, snippet in matches:
        out.append(f"\n--- {name} ---\n{snippet}")
    return "\n".join(out)


def build_prompt(profile_path: Path, include_meets: int) -> str:
    profile = profile_path.read_text(errors="ignore")
    meets = gather_meeting_mentions(profile_path, include_meets)
    return PROMPT_TEMPLATE.format(profile=profile, meetings_section=meets)


def estimate_cost(prompt: str) -> tuple[int, float]:
    in_tokens = int(len(prompt) * TOKENS_PER_CHAR)
    in_cost = in_tokens / 1_000_000 * INPUT_PRICE_PER_MTOK
    out_cost = MAX_TOKENS_OUT / 1_000_000 * OUTPUT_PRICE_PER_MTOK
    return in_tokens, in_cost + out_cost


def call_anthropic(prompt: str) -> str:
    try:
        from anthropic import Anthropic
    except ImportError:
        print(
            "anthropic SDK not installed. Run: pip install anthropic",
            file=sys.stderr,
        )
        sys.exit(2)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set in environment.", file=sys.stderr)
        sys.exit(2)

    client = Anthropic()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS_OUT,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in resp.content if hasattr(b, "text"))


def append_section(profile_path: Path, synthesis: str) -> None:
    text = profile_path.read_text(errors="ignore")
    today = datetime.now().strftime("%Y-%m-%d")
    new_section = (
        f"\n\n## Operational Profile (synthesized {today})\n\n"
        f"_LLM-synthesized via `command-center/scripts/enrich_user_profile.py`. "
        f"Delete this section to revert; rerun the script to refresh._\n\n"
        f"{synthesis.strip()}\n"
    )
    # If a prior synthesis exists, replace it rather than stacking.
    pattern = re.compile(
        r"\n## Operational Profile \(synthesized \d{4}-\d{2}-\d{2}\).*?(?=\n## |\Z)",
        re.S,
    )
    if pattern.search(text):
        text = pattern.sub(new_section.rstrip(), text)
    else:
        text = text.rstrip() + new_section
    profile_path.write_text(text)


def process_one(profile_path: Path, args) -> dict:
    text = profile_path.read_text(errors="ignore")
    if has_recent_synthesis(text) and not args.force:
        return {"path": profile_path, "status": "skipped", "reason": "recent synthesis exists"}

    if len(text) < 400:
        return {"path": profile_path, "status": "skipped", "reason": "profile too thin"}

    prompt = build_prompt(profile_path, args.include_meets)
    in_tokens, cost = estimate_cost(prompt)

    if args.dry_run:
        print(f"\n=== {profile_path.name} ===")
        print(f"# Estimated input tokens: {in_tokens}, cost: ${cost:.4f}")
        if args.show_prompt:
            print("\n--- PROMPT ---")
            print(prompt[:3000] + ("...[truncated]" if len(prompt) > 3000 else ""))
        return {"path": profile_path, "status": "dry-run", "tokens": in_tokens, "cost": cost}

    synthesis = call_anthropic(prompt)
    append_section(profile_path, synthesis)
    return {
        "path": profile_path,
        "status": "enriched",
        "tokens": in_tokens,
        "cost": cost,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("user", nargs="?", help="user.<slug> or just <slug>")
    ap.add_argument("--all", action="store_true", help="process every user.*.md")
    ap.add_argument("--include-meets", type=int, default=0, help="include last N meet.*.md mentions in prompt")
    ap.add_argument("--run", action="store_true", help="actually call the API and write the section")
    ap.add_argument("--confirm", action="store_true", help="required with --all --run")
    ap.add_argument("--force", action="store_true", help="overwrite recent synthesis")
    ap.add_argument("--show-prompt", action="store_true", help="print the prompt in dry-run")
    ap.add_argument("--estimate-cost", action="store_true", help="--all in cost-only mode")
    args = ap.parse_args()
    args.dry_run = not args.run

    if args.all and args.run and not args.confirm:
        print(
            "Refusing to batch-write without --confirm. Run with --estimate-cost first to see total.",
            file=sys.stderr,
        )
        return 2

    targets = []
    if args.user:
        targets = [find_profile(args.user)]
    elif args.all or args.estimate_cost:
        targets = sorted(VAULT.glob("user.*.md"))
    else:
        ap.print_help()
        return 1

    if args.estimate_cost:
        total_tokens = 0
        total_cost = 0.0
        skipped = 0
        for fp in targets:
            text = fp.read_text(errors="ignore")
            if has_recent_synthesis(text) or len(text) < 400:
                skipped += 1
                continue
            prompt = build_prompt(fp, args.include_meets)
            t, c = estimate_cost(prompt)
            total_tokens += t
            total_cost += c
        print(f"Targets: {len(targets) - skipped} ({skipped} skipped)")
        print(f"Estimated input tokens: {total_tokens:,}")
        print(f"Estimated total cost (input + {MAX_TOKENS_OUT}-tok output): ${total_cost:.2f}")
        return 0

    results = [process_one(fp, args) for fp in targets]
    summary = {"enriched": 0, "skipped": 0, "dry-run": 0}
    total_cost = 0.0
    for r in results:
        summary[r["status"]] = summary.get(r["status"], 0) + 1
        total_cost += r.get("cost", 0)
    print(
        f"\n--- {len(results)} targets · enriched={summary.get('enriched', 0)} "
        f"skipped={summary.get('skipped', 0)} dry-run={summary.get('dry-run', 0)} "
        f"· total cost ${total_cost:.4f} ---",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
