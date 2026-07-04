---
name: academic-forge
description: "Curated skill collection for academic writing and research. Includes 140+ scientific skills (LaTeX, citations, paper structure), AI research skills (model architecture, fine-tuning, evaluation, MLOps), and a humanizer for removing AI writing patterns. Use when writing papers, grants, theses, or doing research methodology work."
---

# Academic Forge

A curated collection of skills for academic writing and research, installed at `~/programs/academic-forge/`.

## Included skill sets

### claude-scientific-skills (140 skills)
Scientific paper writing and LaTeX formatting.
- Location: `~/programs/academic-forge/skills/claude-scientific-skills/`
- Docs: `~/programs/academic-forge/skills/claude-scientific-skills/docs/`

### AI-research-SKILLs (20 domains)
Research methodology, model architecture, fine-tuning, evaluation, MLOps, and more.
- Location: `~/programs/academic-forge/skills/AI-research-SKILLs/`
- Domains: model-architecture, tokenization, fine-tuning, mechanistic-interpretability, data-processing, post-training, safety-alignment, distributed-training, infrastructure, optimization, evaluation, inference-serving, mlops, agents, rag, prompt-engineering, observability, multimodal, emerging-techniques, ml-paper-writing

### Humanizer
Remove signs of AI-generated writing from text.
- Location: `~/programs/academic-forge/skills/humanizer/SKILL.md`

## Usage

Read the relevant sub-skill files for detailed instructions. Example:
```bash
# For scientific paper writing
cat ~/programs/academic-forge/skills/claude-scientific-skills/scientific-skills/*/SKILL.md

# For a specific AI research domain
cat ~/programs/academic-forge/skills/AI-research-SKILLs/03-fine-tuning/SKILL.md

# For humanizer
cat ~/programs/academic-forge/skills/humanizer/SKILL.md
```
