CORPUS_BY_ROUTE = {
    "bio": ["paperclip", "pubmed", "semantic_scholar"],
    "cs": ["semantic_scholar", "arxiv", "web"],
}
GROUNDING_CONFIDENCE = {"bio": "high", "cs": "low"}

_BIO = {"gene", "protein", "cell", "assay", "mouse", "mice", "methylation", "clock",
        "senescence", "lifespan", "aging", "biomarker", "rna", "dna", "tissue", "disease",
        "receptor", "pathway", "organoid", "proteome", "transcriptome", "mortality"}
_CS = {"agent", "agents", "llm", "benchmark", "transformer", "neural", "policy",
       "reinforcement", "memory", "topology", "verification", "prompt", "embedding",
       "multi-agent", "reasoning", "token", "architecture"}


def route(idea):
    words = set(w.strip(".,;:()") for w in f"{idea.thesis} {idea.contribution}".lower().split())
    return "cs" if len(words & _CS) > len(words & _BIO) else "bio"
