# Setup Guide: AI-Powered Journal Generation

## Quick Setup (5 minutes)

### 1. Get Anthropic API Key

If you don't have one:
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys
4. Create a new key
5. Copy the key (starts with `sk-ant-...`)

### 2. Configure Environment

Add to your `~/.zshrc` (or `~/.bashrc`):

```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

Reload your shell:
```bash
source ~/.zshrc
```

### 3. Test the Setup

```bash
# Test API access
curl -s https://api.anthropic.com/v1/messages \
  -H "content-type: application/json" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "Say hello"}]
  }'
```

If you see a JSON response with "hello", you're ready!

### 4. Generate Your First AI-Powered Journal

```bash
bash /Users/A.Y/Documents/Manual Library/Dendron/.cursor/skills/screenpipe-daily-journal/scripts/full_workflow.sh 2026-01-30
```

## What You Get

### Before (v2 - Basic)
```markdown
## Day Summary

Email (Gmail).
Terminal - Python development.
Terminal work.

## Timeline

### 11:00 AM

- 🎤 "instead of three. It's gonna be back..."
**Coding - JavaScript**
- ® Browser Tabhttp://localhost:3030This page isn't...
```

### After (v5 - AI-Powered)
```markdown
## Day Summary

Built screenpipe journal automation system from scratch. Developed people 
detection, keyframe extraction, and AI timeline generation. UMich faculty 
interview preparation. Email correspondence about protein clock collaboration.

## Timeline

### 11:00 AM - Screenpipe Setup & Integration Research

**Initial Setup**
- Started screenpipe recording: Display 4 + HyperX SoloCast
- Testing localhost:3030 connection
- Reviewing screenpipe functionality and open source philosophy
- Decision: Privacy concerns addressed with local-only processing

**AI Integration Research**
- Researching Open Interpreter integration with screenpipe
- Planning database query conversion for screenpipe data
- 🎤 "you get that snappy speed, and I set up this search screen pipe 
      function as a custom tool..."

![Screenpipe terminal setup](assets/journal_2026-01-30_moment_1.png)

## State & Open Questions

**Screenpipe Journal System**
- Status: Initial design and planning phase
- Next: Implement full workflow (people detection → keyframes → AI timeline)

**UMich Faculty Interview**
- Status: Preparation in progress
- Next: Finalize 1-minute summary, prepare for on-campus visit

## Tasks

### Inferred from Today

**Screenpipe Journal System**
- [ ] Implement people detection script (full names only)
- [ ] Build keyframe extraction from screenpipe videos
- [ ] Create AI timeline generation with semantic grouping

**Faculty Applications**
- [ ] Complete UMich 1-minute faculty plan summary
- [ ] Prepare for on-campus visit scheduling
```

## Key Improvements

1. **Rich Context**: Specific details about what you did, not just app names
2. **Semantic Grouping**: Activities grouped by work session, not just time
3. **Decisions & Blockers**: Automatically extracted from conversations
4. **Smart Task Inference**: Only real, actionable tasks (filters OCR garbage)
5. **Human-Like Writing**: Natural summaries like you'd write manually

## Cost & Usage

**Typical cost per journal entry**:
- Input: ~5,000 tokens (screen activity data)
- Output: ~1,500 tokens (journal content)
- Cost: ~$0.05 per journal at Claude Sonnet 4 pricing

**Monthly estimate** (30 journals): ~$1.50/month

## Fallback Mode

If API key is not set or API fails:
- Script generates basic structure
- You can fill in manually
- All other features (keyframes, people detection, etc.) still work

## Privacy Note

- All analysis happens via Anthropic API (data sent to Claude)
- Your screen data is sent for analysis
- If privacy is a concern, use basic mode (without API key)
- Consider: Screen data already captured locally by screenpipe

## Next Steps

After setup, try:
1. Generate today's journal: `@screenpipe-daily-journal`
2. Regenerate yesterday: `@screenpipe-daily-journal 2026-01-30`
3. Review and refine the output
4. Add manual notes in the Notes section
