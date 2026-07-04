#!/usr/bin/env python3
"""Deterministic verifier for a manuscript-revision deliverable set.

Mechanizes the skill's "Rebuild + verify" checklist so the objective invariants
are a non-zero exit, not a re-derived regex an agent gets subtly wrong. It
VERIFIES only — it never authors, generates redlines, or composes citations, so
it cannot fabricate (the safest thing a revision tool can ship).

Paper-agnostic: every path is an argument; no project filename is hardcoded.

Usage
-----
  # qmd source gate (pre-render): em-dash, [..]{.mark} balance, exponent-vs-citation
  revision_lint.py --qmd manuscript.qmd [--qmd p2p.qmd ...]

  # rendered-docx gate: ACCEPT==NATIVE + raw [@key]/leftover ^N^ + baseline sanity
  revision_lint.py --clean NATIVE.docx --tracked TRACKED-ALL.docx [--baseline BASELINE.docx]
  revision_lint.py --docx CLEAN.docx          # standalone docx checks only

Exit code is 1 if any check FAILs (WARN does not fail). A green lint is
NECESSARY but NOT SUFFICIENT: it is syntactic. The semantic/fabrication gate
(every quoted change traces to a real edit, every number to a real analysis
output) still applies by hand — see SKILL.md.
"""
from __future__ import annotations

import argparse
import re
import sys

EMDASH = "—"          # — (forbidden); en-dash – and hyphen - are fine
FAILS = 0


def emit(status, check, msg):
    global FAILS
    if status == "FAIL":
        FAILS += 1
    print(f"  [{status:4}] {check}: {msg}")


# ---------------------------------------------------------------- qmd checks
def _strip_code(text):
    """Remove fenced + inline code and escaped brackets so bracket-matching and
    superscript scans don't trip over code/escapes."""
    text = re.sub(r"```.*?```", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", "", text)
    text = text.replace(r"\[", "").replace(r"\]", "")
    return text


def check_emdash(path, raw):
    hits = [i + 1 for i, ln in enumerate(raw.splitlines()) if EMDASH in ln]
    if hits:
        emit("FAIL", "em-dash", f"{path}: literal em-dash on lines {hits[:15]}"
             + (" ..." if len(hits) > 15 else ""))
    else:
        emit("PASS", "em-dash", f"{path}: none")


def check_mark_balance(path, raw):
    """Stack-match [ ] over the de-coded text; links [t](u) and cites [@k] are
    balanced, so leftovers are a broken half of a [..]{.mark} span."""
    text = _strip_code(raw)
    depth = 0
    bad_close = 0
    for ch in text:
        if ch == "[":
            depth += 1
        elif ch == "]":
            if depth == 0:
                bad_close += 1
            else:
                depth -= 1
    n_mark = len(re.findall(r"\]\{\.mark\}", raw))
    if depth or bad_close:
        emit("FAIL", "mark-balance",
             f"{path}: unbalanced square brackets ({depth} unclosed '[', "
             f"{bad_close} stray ']') — a [..]{{.mark}} span is likely broken "
             f"({n_mark} closers seen)")
    else:
        emit("PASS", "mark-balance", f"{path}: balanced ({n_mark} [..]{{.mark}} spans)")


def check_superscripts(path, raw):
    """Classify ^...^ superscripts in the BODY (after '# Introduction') as
    safe exponents vs ambiguous bare-positive (a mis-convertible power OR a
    leftover numeric citation callout). Both are the converter's load-bearing trap."""
    m = re.search(r"(?m)^#\s+Introduction\b", raw)
    body = raw[m.start():] if m else raw
    base = raw[:m.start()].count("\n") + 1 if m else 1
    text = _strip_code(body)
    native_cites = bool(re.search(r"\[@[A-Za-z]", text))   # already converted?
    ambiguous = []
    for mm in re.finditer(r"\^([^\^\n]+)\^", text):
        inner = mm.group(1)
        if inner[:1] in "-−":          # ^-4^  negative exponent -> safe
            continue
        if inner.startswith("{") or "$" in inner:   # ^{6}^ / math -> safe
            continue
        if re.fullmatch(r"[0-9][0-9,\s–—\\-]*", inner):   # bare ^6^ / ^1,4^
            line = base + text[:mm.start()].count("\n")
            ambiguous.append((line, mm.group(0)))
    if not ambiguous:
        emit("PASS", "superscript", f"{path}: no ambiguous bare ^N^ superscripts")
    elif native_cites:
        emit("FAIL", "superscript",
             f"{path}: native [@key] present but {len(ambiguous)} LEFTOVER citation "
             f"superscripts remain (missed conversion), e.g. {ambiguous[:6]}")
    else:
        emit("WARN", "superscript",
             f"{path}: {len(ambiguous)} bare ^N^ — citation callouts to convert, but "
             f"a positive power (10^6^) would be MIS-CONVERTED; disambiguate: {ambiguous[:6]}")


def lint_qmd(path):
    print(f"== qmd: {path} ==")
    try:
        raw = open(path, encoding="utf-8", errors="replace").read()
    except OSError as e:
        emit("FAIL", "open", f"{path}: {e}")
        return
    check_emdash(path, raw)
    check_mark_balance(path, raw)
    check_superscripts(path, raw)


# ------------------------------------------------------------- docx checks
def _accept_text(path):
    """Proven ACCEPT==NATIVE walker (reused from the project validate.py): the
    text you get after accepting all tracked changes (drop del/moveFrom + the
    superscript citation marks), normalized for quotes/dashes/whitespace."""
    import unicodedata
    import zipfile
    from lxml import etree
    W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    NS = {"w": W}

    def qn(t):
        return f"{{{W}}}{t}"

    def nk(s):
        s = unicodedata.normalize("NFC", s or "")
        for a, b in [("’", "'"), ("‘", "'"), ("“", '"'),
                     ("”", '"'), ("–", "-"), ("—", "-"),
                     ("−", "-"), (" ", " ")]:
            s = s.replace(a, b)
        return re.sub(r"\s+", " ", s).strip()

    z = zipfile.ZipFile(path)
    doc = etree.fromstring(z.read("word/document.xml"))
    parts = []

    def is_sup(r):
        return bool(r.xpath("./w:rPr/w:vertAlign[@w:val='superscript']", namespaces=NS))

    def walk(n, skip):
        s = skip or n.tag in (qn("del"), qn("moveFrom"))
        if n.tag == qn("r") and is_sup(n):
            return
        if n.tag == qn("t") and not s:
            parts.append(n.text or "")
        for c in n:
            walk(c, s)

    walk(doc.find(qn("body")), False)
    return nk("".join(parts)), doc, qn


def _body_plain(path):
    import zipfile
    return zipfile.ZipFile(path).read("word/document.xml").decode("utf8", "ignore")


def check_docx_standalone(path):
    xml = _body_plain(path)
    raw_key = re.findall(r"\[@[A-Za-z][\w:-]*", xml)
    if raw_key:
        emit("FAIL", "raw-cite", f"{path}: {len(raw_key)} raw [@key] survived render, e.g. {raw_key[:4]}")
    else:
        emit("PASS", "raw-cite", f"{path}: citations resolved (no raw [@key])")


def check_accept_native(clean, tracked):
    try:
        ctext, _, qn = _accept_text(clean)
        ttext, tdoc, _ = _accept_text(tracked)
    except Exception as e:
        emit("FAIL", "accept==native", f"{e}")
        return None
    if ctext == ttext:
        emit("PASS", "accept==native", f"accepting all tracked changes reproduces CLEAN ({len(ctext)} chars)")
    else:
        # show the first divergence
        i = next((k for k in range(min(len(ctext), len(ttext))) if ctext[k] != ttext[k]), min(len(ctext), len(ttext)))
        emit("FAIL", "accept==native",
             f"tracked != clean after accept; first diff @char {i}: "
             f"clean=...{ctext[max(0,i-25):i+25]!r}... tracked=...{ttext[max(0,i-25):i+25]!r}...")
    return tdoc, qn


def check_baseline(clean, tracked, baseline):
    """ACCEPT==NATIVE passes even against a WRONG baseline. Sanity-check that the
    tracked doc has real insertions and the change volume is plausible."""
    import zipfile
    from lxml import etree
    W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

    def qn(t):
        return f"{{{W}}}{t}"

    def ins_del_chars(path):
        doc = etree.fromstring(zipfile.ZipFile(path).read("word/document.xml"))
        ins = sum(len(t.text or "") for n in doc.iter(qn("ins")) for t in n.iter(qn("t")))
        dele = sum(len(t.text or "") for n in doc.iter(qn("del")) for t in n.iter(qn("delText")))
        total = sum(len(t.text or "") for t in doc.iter(qn("t")))
        return ins, dele, total

    ins, dele, total = ins_del_chars(tracked)
    if ins == 0 and dele == 0:
        emit("FAIL", "baseline", "tracked doc has ZERO insertions/deletions — baseline likely identical/stale (no real redline)")
        return
    frac = (ins + dele) / max(total, 1)
    if frac > 0.9:
        emit("WARN", "baseline", f"change volume {frac:.0%} of body — baseline may be WRONG (near-total rewrite); verify it is the correct prior version")
    else:
        emit("PASS", "baseline", f"{ins} ins / {dele} del chars ({frac:.0%} of body) — plausible redline (still confirm the baseline is the right prior version)")


def main():
    ap = argparse.ArgumentParser(description="Deterministic manuscript-revision verifier (verifies, never authors).")
    ap.add_argument("--qmd", action="append", default=[], metavar="FILE")
    ap.add_argument("--docx", action="append", default=[], metavar="FILE")
    ap.add_argument("--clean", metavar="NATIVE.docx")
    ap.add_argument("--tracked", metavar="TRACKED.docx")
    ap.add_argument("--baseline", metavar="BASELINE.docx")
    args = ap.parse_args()

    if not (args.qmd or args.docx or args.clean):
        ap.error("nothing to check: pass --qmd, --docx, and/or --clean/--tracked")

    for q in args.qmd:
        lint_qmd(q)
    for d in args.docx:
        print(f"== docx: {d} ==")
        check_docx_standalone(d)
    if args.clean:
        print(f"== tracked pair: clean={args.clean} tracked={args.tracked} ==")
        check_docx_standalone(args.clean)
        if args.tracked:
            check_docx_standalone(args.tracked)
            check_accept_native(args.clean, args.tracked)
            if args.baseline:
                check_baseline(args.clean, args.tracked, args.baseline)

    print()
    if FAILS:
        print(f"LINT: {FAILS} FAIL — not shippable. (Green lint is necessary, not sufficient: the fabrication/semantic gate still applies by hand.)")
        sys.exit(1)
    print("LINT: all checks passed. (Necessary, not sufficient — verify every quoted change/number by hand.)")


if __name__ == "__main__":
    main()
