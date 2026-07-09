---
name: file-organizer
description: "Safely route, name, and record Zixin's downloaded or generated files. Use when organizing Downloads/Desktop clutter, handling newly downloaded or created task artifacts, deciding where files belong, renaming important files, recording canonical file locations, or adding a file-intake pass to Dendron sync."
---

> **Asset status (Zixin machine, 2026-07-09):** `scripts/fs_drift_scan.py` and
> `scripts/fs_drift_apply.py` were never committed to the shared snapshot. The drift checklist
> is therefore manual-only on this machine; `scripts/file_intake_scan.py` is present and works.

# File Organizer

Keep Zixin's filesystem from accumulating untracked intake files. Route files only when the destination is strongly supported by the current task, the File Atlas, or an existing project convention. Broad cleanup is always approval-first.

## Core Contract

- Treat `~/Downloads` as a zero-retention intake tray, not a permanent home. Loose `~/Desktop` is also an intake zone, but may have a few review-only items.
- Read `file-finder` and `tool.file-atlas.md` when deciding where an artifact belongs.
- Use `references/intake_schema.md` for the candidate schema, audit fields, confidence meanings, and sync behavior.
- Default to read-only inventory for broad cleanup. Do not silently bulk-move, delete, deduplicate, or rename old files.
- When Zixin explicitly asks to clean or organize Downloads, use **Downloads evacuation**: route every top-level item out of `~/Downloads` to a project folder, Personal Info, File Archive review folder, software archive, or non-indexed sensitive archive. Do not leave a `_quarantine` folder inside Downloads.
- Move current-task artifacts immediately only when all of these are true:
  - The agent just created, downloaded, exported, or modified the file in this task.
  - The canonical destination is obvious from task context plus an existing path convention.
  - The destination does not already contain a conflicting file.
  - The file is not a secret, credential, local database, token, browser state, OAuth material, medical/legal/immigration original, or active app bundle.
  - The move is logged in the relevant note or `tool.file-intake-log.md`.
- Ask Zixin before moving files from old Downloads/Desktop clutter, personal documents, immigration/tax/ID files, archives, installers, or anything with ambiguous ownership unless he has explicitly asked for cleanup/organization in the same turn.
- Never delete files as part of this skill. Use dated archive/review folders for cleanup.
- Password exports, browser exports, OAuth material, and similar secrets must move only to a non-indexed sensitive archive. Do not record their exact filenames in vault notes.

## Quick Inventory

Run the bundled scanner for a read-only triage table:

```bash
python3 ~/programs/ai-skills/file-organizer/scripts/file_intake_scan.py --days 30 --format markdown --max 80
```

For machine-readable output:

```bash
python3 ~/programs/ai-skills/file-organizer/scripts/file_intake_scan.py --days 30 --format json --out ~/Documents/sci-ideas/.cache/sync-state/file-intake-latest.json
```

The scanner inspects top-level `~/Downloads` and loose `~/Desktop` entries by default. It does not recurse, read file contents, move files, rename files, or delete files.

## Routing Workflow

1. Identify the scope: current-task artifact, recent intake review, Downloads evacuation, Desktop cleanup, project folder hygiene, or `/sync` file-intake.
2. Inventory the candidate files with safe metadata: path, type, size, modification time, age, route hint, confidence, and safe action.
3. Decide mode:
   - `current-task`: route obvious artifacts now, then log the action.
   - `recent-intake`: summarize candidates and ask before moving unless every immediate-routing condition is met.
   - `downloads-evacuation`: after explicit approval, route all top-level Downloads entries out of Downloads.
   - `broad-cleanup`: for Desktop or other zones, use a checklist/review pass unless Zixin clearly approved movement.
   - `sync`: summary only, no moves.
4. Choose destinations using this order:
   - Explicit user path or current task path.
   - Existing project folder named in the task.
   - `tool.file-atlas.md` routing table.
   - `file-finder` zone model.
   - Ask Zixin if the first three do not converge.
5. Preserve official filenames for submitted documents, receipts, institution forms, passports, immigration/tax records, and collaborator-provided files unless Zixin approves a rename.
6. For generated analysis, draft, figure, or slide artifacts, prefer date-stamped descriptive names: `YYYY-MM-DD_short-context_variant.ext`.
7. Verify after moving: destination exists, size is nonzero when expected, and no source conflict remains.
8. Record the action.

## Records

Use the lightest record that keeps the file findable:

- Current project file or meeting note: add a bullet with the final absolute path when the file matters only to that project/thread.
- `tool.file-atlas.md`: update only when the canonical routing rule, search hint, or source-of-truth path changes.
- `tool.file-intake-log.md`: append for moved/routed files when there is no more specific project note, or when the action is part of Downloads/Desktop cleanup.
- `tool.file-drift.YYYY-MM-DD.md`: use for approval-based broad cleanup.

Each record should include original path, final path, date, rationale, and whether Zixin approved it or it was a current-task obvious route.

## Downloads Evacuation

When Zixin asks to clean Downloads, the target end state is `~/Downloads` empty
or containing only live files created after the cleanup started.

Destination rules:

- Strong project match → `~/Desktop/Projects/.../<project>/_downloads_archive/YYYY-MM-DD/<category>/`
- Personal/admin/tax/immigration/employment/health → `~/Documents/Manual Library/Personal Info/_downloads_archive/YYYY-MM-DD/<category>/`
- Password exports / browser exports / OAuth or credential material → a non-indexed folder such as `~/Documents/Sensitive Downloads Archive/YYYY-MM-DD/<category>/`
- Installers/apps → `~/Documents/Manual Library/Software Installers/downloads_archive/YYYY-MM-DD/`
- Ambiguous items → `~/Documents/Manual Library/File Archive/Downloads/YYYY-MM-DD/review/`
- Legacy `~/Downloads/_quarantine` → move into `File Archive/Downloads/YYYY-MM-DD/legacy-quarantine/`

Write a manifest for non-sensitive moves and a separate non-indexed manifest for
sensitive moves. Record a summary in the vault, not hundreds of per-file bullets.

## Broad Cleanup

Use the existing vault drift system for bulk Downloads/Desktop cleanup:

```bash
python3 ~/Documents/sci-ideas/notes/.scripts/fs_drift_scan.py
python3 ~/Documents/sci-ideas/notes/.scripts/fs_drift_apply.py ~/Documents/sci-ideas/notes/tool.file-drift.YYYY-MM-DD.md --dry-run
```

Only apply after Zixin has reviewed/ticked the checklist or explicitly approved the listed moves. For Downloads, prefer evacuation over leaving old files in a local `_quarantine`.

## Sync Mode

During `/sync`, do not move files. Run a summary-only intake pass after the vault index/catalog refresh:

```bash
python3 ~/programs/ai-skills/file-organizer/scripts/file_intake_scan.py --days 30 --format markdown --max 40
```

If the file catalog exists, the sync agent may also generate the normal drift checklist with `fs_drift_scan.py`, but it must not run moves without explicit approval. If Zixin asks for cleanup in the same turn as `/sync`, run Downloads evacuation after the read-only sync summary.
