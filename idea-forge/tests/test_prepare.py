from pathlib import Path
import yaml
from idea_forge.prepare import prepare, calibration_status

FREE = Path(__file__).parent / "fixtures" / "sample_idea_freeform.md"


def test_prepare_scaffold():
    s = prepare(str(FREE))
    assert s["stage"] == "planned"
    assert s["route"] in ("bio", "cs")
    assert "sequence model" in s["content_for_judge"]
    assert s["grounding_confidence"] in ("high", "low")
    assert "advisory" in s["calibration"]


def test_calibration_advisory_when_empty(tmp_path):
    p = tmp_path / "empty.yaml"
    p.write_text("[]\n")
    assert calibration_status(str(p))["advisory"] is True


def test_calibration_not_advisory_when_full(tmp_path):
    rows = []
    for tier in ("top", "field", "failed", "incremental"):
        for k in range(3):
            rows.append({"id": f"{tier}{k}", "title": "T", "field": "bio",
                         "claim": "c", "known_tier": tier})
    p = tmp_path / "full.yaml"
    p.write_text(yaml.safe_dump(rows))
    st = calibration_status(str(p))
    assert st["advisory"] is False and st["n"] == 12
