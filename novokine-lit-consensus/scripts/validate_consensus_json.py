#!/usr/bin/env python3
"""Validate novokine literature consensus JSON files."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "novokine-lit-consensus-v1"
ACTIVATION_DIRECTIONS = {
    "favor_activation",
    "warn_activation",
    "mixed_context_dependent",
    "unknown",
}
CONFIDENCE = {"high", "medium", "low", "none"}
TIERS = {"high", "mid", "small"}
DIR_FOR_ACTIVATION = {"support", "contra", "neutral", "unclear"}
CONTEXT_MATCH = {"matched", "adjacent", "mismatch", "unclear"}
EVIDENCE_CLASS = {
    "human_perturbation",
    "animal_perturbation",
    "cell_perturbation",
    "patient_tissue",
    "expression_association",
    "review",
    "association",
    "topology",
    "other",
}
DOC_ID_RE = re.compile(r"^(PMC\d+|bio_[A-Za-z0-9_.-]+|med_[A-Za-z0-9_.-]+|arx_[A-Za-z0-9_.-]+)$")


def fail(errors: list[str], path: str, msg: str) -> None:
    errors.append(f"{path}: {msg}")


def require_type(errors: list[str], path: str, value: Any, typ: type) -> bool:
    if not isinstance(value, typ):
        fail(errors, path, f"expected {typ.__name__}, got {type(value).__name__}")
        return False
    return True


def require_enum(errors: list[str], path: str, value: Any, allowed: set[str]) -> None:
    if value not in allowed:
        fail(errors, path, f"expected one of {sorted(allowed)}, got {value!r}")


def validate_evidence(errors: list[str], path: str, evidence: Any) -> None:
    if not require_type(errors, path, evidence, list):
        return
    for i, ev in enumerate(evidence):
        ep = f"{path}[{i}]"
        if not require_type(errors, ep, ev, dict):
            continue
        for key in ("doc_id", "claim", "direction_for_activation", "context_match", "evidence_class"):
            if key not in ev:
                fail(errors, f"{ep}.{key}", "missing required field")
        doc_id = ev.get("doc_id")
        if isinstance(doc_id, str) and not DOC_ID_RE.match(doc_id):
            fail(errors, f"{ep}.doc_id", "must be a Paperclip document id such as PMC123456")
        if "direction_for_activation" in ev:
            require_enum(errors, f"{ep}.direction_for_activation", ev.get("direction_for_activation"), DIR_FOR_ACTIVATION)
        if "context_match" in ev:
            require_enum(errors, f"{ep}.context_match", ev.get("context_match"), CONTEXT_MATCH)
        if "evidence_class" in ev:
            require_enum(errors, f"{ep}.evidence_class", ev.get("evidence_class"), EVIDENCE_CLASS)
        if ev.get("verified") is not True:
            fail(errors, f"{ep}.verified", "must be true for evidence used in consensus output")
        if "line_refs" in ev and not isinstance(ev["line_refs"], list):
            fail(errors, f"{ep}.line_refs", "must be a list when present")


def validate_target(errors: list[str], gene_key: str, rec: Any) -> None:
    path = f"targets.{gene_key}"
    if not require_type(errors, path, rec, dict):
        return
    required = [
        "gene",
        "activation_direction",
        "direction_confidence",
        "novokine_likelihood",
        "surface_accessible",
        "evidence",
        "rationale",
        "likelihood_rationale",
    ]
    for key in required:
        if key not in rec:
            fail(errors, f"{path}.{key}", "missing required field")
    if rec.get("gene") != gene_key:
        fail(errors, f"{path}.gene", "must match the targets object key")
    if "activation_direction" in rec:
        require_enum(errors, f"{path}.activation_direction", rec.get("activation_direction"), ACTIVATION_DIRECTIONS)
    if "direction_confidence" in rec:
        require_enum(errors, f"{path}.direction_confidence", rec.get("direction_confidence"), CONFIDENCE)
    if "novokine_likelihood" in rec:
        require_enum(errors, f"{path}.novokine_likelihood", rec.get("novokine_likelihood"), TIERS)
    if "direction_score" in rec:
        score = rec["direction_score"]
        if not isinstance(score, (int, float)) or score < -1 or score > 1:
            fail(errors, f"{path}.direction_score", "must be numeric in [-1, 1]")
    if "manual_review" in rec and not isinstance(rec["manual_review"], bool):
        fail(errors, f"{path}.manual_review", "must be boolean")
    if "surface_accessible" in rec and not isinstance(rec["surface_accessible"], (bool, type(None))):
        fail(errors, f"{path}.surface_accessible", "must be true, false, or null")
    validate_evidence(errors, f"{path}.evidence", rec.get("evidence"))


def validate_pair(errors: list[str], pair_key: str, rec: Any) -> None:
    path = f"pairs.{pair_key}"
    if not require_type(errors, path, rec, dict):
        return
    for key in ("pair_id", "anchor", "specifier", "pair_novokine_likelihood", "pair_direction", "pair_rationale"):
        if key not in rec:
            fail(errors, f"{path}.{key}", "missing required field")
    if rec.get("pair_id") != pair_key:
        fail(errors, f"{path}.pair_id", "must match the pairs object key")
    if "pair_novokine_likelihood" in rec:
        require_enum(errors, f"{path}.pair_novokine_likelihood", rec.get("pair_novokine_likelihood"), TIERS)
    if "pair_direction" in rec:
        require_enum(errors, f"{path}.pair_direction", rec.get("pair_direction"), ACTIVATION_DIRECTIONS)
    if "activation_warning" in rec and not isinstance(rec["activation_warning"], bool):
        fail(errors, f"{path}.activation_warning", "must be boolean")


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001 - CLI should report JSON/file errors plainly.
        return [f"{path}: cannot read JSON: {exc}"]
    if not require_type(errors, "$", data, dict):
        return errors
    if data.get("schema_version") != SCHEMA_VERSION:
        fail(errors, "schema_version", f"must be {SCHEMA_VERSION!r}")
    for key in ("program", "disease_context", "targets"):
        if key not in data:
            fail(errors, key, "missing required top-level field")
    targets = data.get("targets")
    if require_type(errors, "targets", targets, dict):
        for gene, rec in targets.items():
            validate_target(errors, str(gene), rec)
    pairs = data.get("pairs", {})
    if pairs is not None and require_type(errors, "pairs", pairs, dict):
        for pair_id, rec in pairs.items():
            validate_pair(errors, str(pair_id), rec)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_path", type=Path)
    args = parser.parse_args()
    errors = validate(args.json_path)
    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1
    data = json.loads(args.json_path.read_text())
    print(
        "OK",
        args.json_path,
        f"targets={len(data.get('targets', {}))}",
        f"pairs={len(data.get('pairs', {}) or {})}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
