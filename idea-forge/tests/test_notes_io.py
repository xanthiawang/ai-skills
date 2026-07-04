import shutil
from pathlib import Path
from idea_forge.notes_io import (parse_idea, render_forge_block, upsert_forge_block, set_stage,
                                 read_forge_block, load_population)

FIX = Path(__file__).parent / "fixtures" / "sample_idea.md"
FREE = Path(__file__).parent / "fixtures" / "sample_idea_freeform.md"


def test_parse_sections():
    idea = parse_idea(str(FIX))
    assert idea.stage == "paper-idea"
    assert "Methylation velocity" in idea.thesis
    assert "velocity across organs" in idea.prior_work
    assert "velocity estimator" in idea.contribution
    assert "static clocks" in idea.empirical_claim
    assert idea.has_template


def test_parse_freeform_synonyms_and_rawbody():
    # A real-world note using Concept/Approach/Expected Outcomes, not the strict template.
    idea = parse_idea(str(FREE))
    assert idea.stage == "planned"
    assert idea.has_template
    assert "sequence model" in idea.thesis            # Concept -> thesis
    assert "Extract features" in idea.contribution     # Approach -> contribution
    assert "Novel regulatory" in idea.empirical_claim  # Expected Outcomes -> empirical_claim
    assert "sequence model" in idea.raw_body
    assert "sequence model" in idea.content_for_judge()


def test_stage_status_fallback(tmp_path):
    # Real sci.ideas notes use `status:` not `stage:` — read and update it in place, no dup.
    p = tmp_path / "s.md"
    p.write_text("---\nid: s\ntitle: S\nstatus: planned\n---\n\nbody\n")
    assert parse_idea(str(p)).stage == "planned"
    set_stage(str(p), "rejected")
    txt = p.read_text()
    assert "status: rejected" in txt
    assert "stage:" not in txt


def test_population_loading(tmp_path):
    a = tmp_path / "sci.ideas.a.md"
    a.write_text("---\nid: a\ntitle: A\n---\n\nbody\n")
    b = tmp_path / "sci.ideas.b.md"
    b.write_text("---\nid: b\ntitle: B\n---\n\nbody\n")
    c = tmp_path / "sci.ideas.c.md"
    c.write_text("---\nid: c\n---\n\nno idea-forge block here\n")
    upsert_forge_block(str(a), render_forge_block(
        {"idea_id": "a", "novelty": {"claude": 8, "codex": 7},
         "feasibility": {"claude": 4, "codex": 5}, "impact": {"claude": 9, "codex": 8}}))
    upsert_forge_block(str(b), render_forge_block(
        {"idea_id": "b", "novelty": {"claude": 3, "codex": 4},
         "feasibility": {"claude": 8, "codex": 8}, "impact": {"claude": 3, "codex": 2}}))

    assert read_forge_block(str(a))["novelty"]["claude"] == 8
    assert read_forge_block(str(c)) is None
    pop = load_population(str(tmp_path))
    assert pop["a"] == (7, 4, 8)   # per-axis min of the two model scores
    assert pop["b"] == (3, 8, 2)
    assert "c" not in pop


def test_parse_nontemplate_falls_back_to_rawbody(tmp_path):
    # A note with no recognizable sections at all -> raw_body carries the idea.
    p = tmp_path / "n.md"
    p.write_text("---\nid: x\ntitle: T\nstage: inbox\n---\n\n"
                 "Just a paragraph describing a wild idea about telomere reprogramming.\n")
    idea = parse_idea(str(p))
    assert not idea.has_template
    assert "wild idea about telomere reprogramming" in idea.raw_body
    assert idea.content_for_judge() == idea.raw_body


def test_render_block_has_provenance():
    md = render_forge_block({"tier_potential": "top",
                             "provenance": {"queries": ["q"], "models": ["claude", "codex"]}})
    assert md.startswith("## idea-forge")
    assert "provenance" in md and "tier_potential" in md


def test_upsert_idempotent_and_stage(tmp_path):
    p = tmp_path / "idea.md"
    shutil.copy(FIX, p)
    upsert_forge_block(str(p), render_forge_block({"tier_potential": "field"}))
    upsert_forge_block(str(p), render_forge_block({"tier_potential": "top"}))
    txt = p.read_text()
    assert txt.count("## idea-forge") == 1 and "top" in txt
    set_stage(str(p), "rejected")
    assert "stage: rejected" in p.read_text()
