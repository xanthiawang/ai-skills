---
name: vault-updater
description: "Consume sync manifests and apply edits to vault notes. Serial queue with lockfile."
---

# Vault Updater

Applies changes from sync adapter manifests to Dendron vault notes. This is the
write-side of the sync pipeline — adapters produce manifests, this skill consumes them.

## When to Use

Called by the `/sync` router after an adapter produces a manifest. Not invoked directly.

## Input

One or more manifest JSON files from `.cache/sync-state/*-manifest-*.json`.

## Process

### 1. Acquire Lock

Check `.cache/sync-state/.updater-lock`:
- If not exists: create it with current timestamp
- If exists and < 5 min old: wait 10s, retry up to 3 times, then fail
- If exists and > 5 min old: assume stale, delete and recreate

### 2. Load Manifests

Read all `*-manifest-*.json` files passed as input. Group changes by target note path.
If multiple sources target the same note + section, you must synthesize content from
all sources into a single coherent update (don't just pick one).

### 3. Apply Changes

For each target note, process changes in this order:
1. `update_frontmatter` first (sets metadata)
2. `rewrite_section` next (structural changes)
3. `append` last (additive only)

#### rewrite_section

1. Read the note file
2. Find the target heading (e.g., `## Current Status`)
3. Find the next heading at the same level (##)
4. Replace everything between them with the new content
5. If heading doesn't exist: insert at end of document, but BEFORE `## Chat History` or `## Stats` sections if they exist
6. If note has no headings at all: append heading + content at end of file
7. Update frontmatter `updated:` timestamp

#### append

1. Find the target section heading
2. Insert content at the end of that section (before next same-level heading)
3. If heading doesn't exist: create it (same insertion rules as rewrite_section)
4. Update frontmatter `updated:` timestamp

#### update_frontmatter

1. Parse existing YAML frontmatter
2. Merge new fields (overwrite existing keys, add new keys)
3. Always update `updated:` to current epoch milliseconds
4. Preserve field order: id, title, desc, tier, ..., updated, created

#### create_note

1. Check `suggested_path` doesn't already exist. If it does, skip and log warning.
2. Generate `id`: 23 lowercase alphanumeric characters (use Python: `''.join(random.choices(string.ascii_lowercase + string.digits, k=23))`)
3. Build frontmatter from manifest `frontmatter` object + generated id + timestamps
4. Write full note: frontmatter + content from manifest
5. Verify note follows Dendron hierarchy convention (filename matches hierarchy)

### 4. Confidence Gating

Before applying each change:
- confidence >= 0.8: apply silently, add to "applied" list
- confidence < 0.8: apply, add to "flagged" list (included in delta briefing with evidence)

### 5. Commit

```bash
git add [all changed/created note files]
git commit -m "vault-sync: N notes updated from <sources> (YYYY-MM-DD)"
```

Source list comes from the `source` field of consumed manifests (deduplicated).

### 6. Report

Output a delta summary in this format:

```markdown
## Sync Delta

**Applied**: N changes across M notes
**Flagged** (low confidence): K changes

### Changes
- `user.per-greisen.md` — rewrote "## Current Status" (email, 0.95)
- `proj.2025.disaggregase.md` — rewrote "## Current Status" (email+screenpipe, 0.88)
- `user.john-smith.md` — **created** (email, 0.85)

### Flagged (confidence < 0.8)
- `sci.tools.colabfold.md` — rewrote "## Current Status" (screenpipe, 0.72) — evidence: 3h ColabFold usage detected in screenpipe
```

### 7. Release Lock

Delete `.cache/sync-state/.updater-lock`.

### 8. Refresh Working Memory

After committing, update `_working-memory.md`:
- Rewrite `## Sync Status` section with current timestamps per source
- If calendar manifest was applied: update `## Today's Calendar` section
- If email manifest was applied: update `## Email Inbox — Active Items` section

### 9. Update SuperWhisper Vocabulary

After vault sync completes, check if any new terms appeared in the sync that aren't in the SuperWhisper dictionary:

1. Read `/Users/A.Y/Desktop/superwhisper/settings/settings.json`
2. Collect candidate terms from the sync delta:
   - New person names from `create_note` changes (user.*.md files)
   - New project/company names from project note updates
   - New technical terms, lab names, institution names from any updated notes
3. **Filter**: Only add terms that would be **verbally confusable** — words a speech model would misrecognize because they sound like common words or have unusual pronunciations. Examples: proper names (Wyss-Coray, Gladyshev, Kaeberlein), branded compound words (MethylGPT, ClockBase, RFdiffusion), unusual scientific words (ouabain, disaggregase, methylome).
4. **Do NOT add**: spelled-out acronyms (PPI, CLS, MLP, GWAS, CRISPR, FOXO, IGF-1, etc.) — the user spells these letter-by-letter and the speech model handles them fine. Also skip common English words, well-known place names (UCSD, Salk), and generic journal names (Nature Aging, NComms).
5. Compare candidates against the existing `vocabulary` array
6. If new terms found: append them to the `vocabulary` array and write the file
7. Report in delta briefing: "SuperWhisper: added N new terms ([list])"

## Error Handling

- If a note file can't be parsed (malformed YAML, encoding error): skip it, log to flagged list
- If git commit fails: log error, do NOT retry. Leave lock in place for debugging.
- If a `rewrite_section` can't find the note file: skip (note may have been deleted)
