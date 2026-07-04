#!/usr/bin/env bash
# Honcho A/B install helper.
#
# Brings up Honcho's 4-service docker compose (api + deriver + Postgres+pgvector + Redis)
# pointing at Albert's Anthropic API key. Smoke-tests the API. After this runs,
# `honcho_adapter.py` will start mirroring turns when invoked.
#
# Run once: `bash honcho_install.sh`
# Stop:     `cd ~/programs/honcho-eval && docker compose down`
# Restart:  `cd ~/programs/honcho-eval && docker compose up -d`

set -euo pipefail

ROOT="$HOME/programs/honcho-eval"

if [ -d "$ROOT" ]; then
    echo "Honcho dir already exists at $ROOT — pulling latest"
    cd "$ROOT"
    git pull --ff-only
else
    echo "Cloning honcho into $ROOT"
    mkdir -p "$(dirname "$ROOT")"
    git clone https://github.com/plastic-labs/honcho.git "$ROOT"
    cd "$ROOT"
fi

# Compose file.
if [ ! -f docker-compose.yml ]; then
    cp docker-compose.yml.example docker-compose.yml
    echo "Copied docker-compose.yml.example → docker-compose.yml"
fi

# .env. Ask for the API key only if not already set.
if [ ! -f .env ]; then
    cp .env.template .env
    if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
        # Append our key to the .env. Using a delimiter that's unlikely in keys.
        printf '\nLLM_ANTHROPIC_API_KEY=%s\n' "$ANTHROPIC_API_KEY" >> .env
        echo "Wrote LLM_ANTHROPIC_API_KEY to .env from environment"
    else
        echo ""
        echo "⚠ ANTHROPIC_API_KEY not set in environment."
        echo "  Edit $ROOT/.env and add one of:"
        echo "    LLM_ANTHROPIC_API_KEY=sk-ant-..."
        echo "    LLM_OPENAI_API_KEY=sk-..."
        echo "    LLM_GEMINI_API_KEY=..."
        echo ""
        echo "  Then re-run this script."
        exit 1
    fi
fi

echo "Bringing up honcho services in detached mode..."
docker compose up -d --build

echo "Waiting up to 60s for API to become healthy..."
for i in $(seq 1 60); do
    if curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1; then
        echo "✓ Honcho API healthy at http://127.0.0.1:8000"
        break
    fi
    sleep 1
done

if ! curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1; then
    echo "✗ API still not responding. Check: docker compose logs api"
    exit 1
fi

# Install python SDK.
if ! python3 -c "import honcho" 2>/dev/null; then
    echo "Installing honcho-ai SDK..."
    pip install --user honcho-ai
fi

cat <<'EOF'

Honcho is up. To enable the adapter, export:
    export HONCHO_BASE_URL=http://127.0.0.1:8000

Smoke test:
    HONCHO_BASE_URL=http://127.0.0.1:8000 python3 \
        ~/programs/ai-skills/dendron/command-center/scripts/honcho_adapter.py \
        write --session smoke-test --peer albert --role user --text "first ping"

Stop services with:
    cd ~/programs/honcho-eval && docker compose down

A/B protocol + decision criteria: see vault note `tool.honcho-ab.md`.
EOF
