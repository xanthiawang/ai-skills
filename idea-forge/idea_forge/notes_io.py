import glob
import os
import re
import yaml
from idea_forge.models import IdeaNote

# Header synonyms: Albert's strict template first, then the common variants his real
# sci.ideas notes actually use (Concept/Approach/Expected Outcomes/etc.). The trailing `.*?`
# in _section lets a header carry extra words (e.g. "Core Empirical Claim To Seek").
_HEADERS = {
    "thesis": r"(?:paper thesis|thesis|concept|core idea|overview|summary)",
    "prior_work": r"(?:prior[- ]work boundary|prior work|related work|background|motivation)",
    "contribution": r"(?:contribution shape|contributions?|approach|key innovation|method)",
    "empirical_claim": r"(?:core empirical claim|key questions?|expected outcomes?|hypothesis)",
}


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _fm(text, key):
    m = re.search(rf"^{key}:\s*(.+)$", text, flags=re.MULTILINE)
    return m.group(1).strip() if m else None


def _section(text, header_regex):
    pat = rf"^#{{1,6}}\s*{header_regex}.*?$\n(.*?)(?=^#{{1,6}}\s|\Z)"
    m = re.search(pat, text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else ""


def _raw_body(text):
    """The note body with frontmatter, the idea-forge block, and bare separators removed."""
    t = re.sub(r"\A---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL)          # frontmatter
    t = re.sub(r"^## idea-forge\b.*?(?=^## |\Z)", "", t, flags=re.MULTILINE | re.DOTALL)  # our block
    lines = [ln for ln in t.splitlines() if ln.strip() != "---"]                 # bare separators
    return "\n".join(lines).strip()


def parse_idea(path):
    text = _read(path)
    sec = {k: _section(text, rx) for k, rx in _HEADERS.items()}
    return IdeaNote(id=_fm(text, "id") or "", path=path, title=_fm(text, "title") or "",
                    thesis=sec["thesis"], prior_work=sec["prior_work"],
                    contribution=sec["contribution"], empirical_claim=sec["empirical_claim"],
                    stage=_fm(text, "stage") or _fm(text, "status") or "inbox", sections=sec,
                    raw_body=_raw_body(text))


def render_forge_block(data):
    body = yaml.safe_dump(data, sort_keys=False, allow_unicode=True).rstrip()
    return f"## idea-forge\n\n```yaml\n{body}\n```\n"


def upsert_forge_block(path, block_md):
    text = _read(path)
    pat = r"^## idea-forge\b.*?(?=^## |\Z)"
    block = block_md if block_md.endswith("\n") else block_md + "\n"
    # Use a replacement function so backslashes/group-refs in `block` are inserted literally.
    if re.search(pat, text, flags=re.MULTILINE | re.DOTALL):
        text = re.sub(pat, lambda _m: block, text, flags=re.MULTILINE | re.DOTALL)
    else:
        text = text.rstrip() + "\n\n" + block
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def read_forge_block(path):
    """Parse the YAML inside a note's `## idea-forge` block; None if absent/unparseable."""
    m = re.search(r"^## idea-forge\b.*?```yaml\n(.*?)\n```", _read(path),
                  flags=re.MULTILINE | re.DOTALL)
    if not m:
        return None
    try:
        return yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None


def _axis_score(block, axis):
    """Per-axis Pareto value = min of the two model scores (mirrors SKILL aggregation)."""
    v = block.get(axis)
    if isinstance(v, dict):
        nums = [x for x in (v.get("claude"), v.get("codex")) if isinstance(x, (int, float))]
        return min(nums) if nums else None
    return v if isinstance(v, (int, float)) else None


def load_population(notes_dir, pattern="sci.ideas.*.md"):
    """Build {idea_id: (novelty, feasibility, impact)} from all scored notes, for Pareto positioning."""
    pop = {}
    for p in glob.glob(os.path.join(notes_dir, pattern)):
        block = read_forge_block(p)
        if not block:
            continue
        vec = tuple(_axis_score(block, a) for a in ("novelty", "feasibility", "impact"))
        if all(isinstance(x, (int, float)) for x in vec):
            key = block.get("idea_id") or os.path.basename(p)[:-3]
            pop[key] = vec
    return pop


def set_stage(path, stage):
    text = _read(path)
    # Update whichever key the note already uses (`stage:` or `status:`); else insert `stage:`.
    m = re.search(r"^(stage|status):\s*.+$", text, flags=re.MULTILINE)
    if m:
        text = re.sub(r"^(stage|status):\s*.+$", rf"{m.group(1)}: {stage}", text,
                      count=1, flags=re.MULTILINE)
    else:
        text = re.sub(r"^(---\n)", rf"\1stage: {stage}\n", text, count=1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
