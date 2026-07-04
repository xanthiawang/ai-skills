---
name: file-finder
description: "Locate Albert's files across the filesystem. Provides the mental model, key paths, and decision logic for finding manuscripts, grants, data, notes, and any file not in the current directory."
alwaysApply: false
---

# File Finder

Albert's filesystem has four zones. Understand these before searching.

## Four Zones

1. **Downloads** (`~/Downloads`) — A **zero-retention intake tray**. New files land here from browsers, email, Slack, and app exports, but they should be routed out by the end of the task or during the next explicit cleanup. Check here first for very recent files, then move/record them with `file-organizer`.
2. **Projects** (`~/Desktop/Projects`) — The **organized archive**. Papers, grants, job apps, and research projects sorted by category and year.
3. **Dendron** (`~/Documents/Manual Library/Dendron/notes/`) — The **knowledge graph**. Cross-linked notes on people, ideas, meetings, projects, papers, protocols.
4. **Programs** (`~/programs`) — **Code and tools**. 66 git repos including ai-skills, academic-forge, dotfiles.

Files flow: **Downloads → Projects / Personal Info / File Archive** and **everywhere → Dendron** as notes/links. Downloads should not be used as a long-term archive.

For routing, naming, or cleanup decisions, use the `file-organizer` skill. This
skill answers "where is it?"; `file-organizer` answers "where should it go, how
should it be named, and what record needs to be updated?"

## Key Paths

| What | Path |
|------|------|
| Recent files (system-wide) | `~/Downloads/Recents` (macOS smart folder — shows files from ANYWHERE) |
| Downloads intake tray | `~/Downloads` |
| All projects root | `~/Desktop/Projects` |
| Papers/manuscripts | `~/Desktop/Projects/Manuscripts/{year}_{topic}/` |
| Grant applications | `~/Desktop/Projects/Grant/{year}_{name}/` |
| Job applications | `~/Desktop/Projects/Job/` (2025_ap/{institution}/, 2025_postdoc/, company/) |
| Active research (current year) | `~/Desktop/Projects/2026/{project}/` |
| Active research (prior years) | `~/Desktop/Projects/2025/`, `~/Desktop/Projects/2024/` |
| Software packages | `~/Desktop/Projects/Packages/` (biolearn, pyforce, R_package, vscode_ext) |
| CV (multiple variants) | `~/Desktop/Projects/website/kejunying.com/content/cv/` |
| Letter templates | `~/Desktop/Projects/letters/` (cover_letter.qmd, sign.jpg, visa/) |
| Websites | `~/Desktop/Projects/website/` (kejunying.com, albert-ying.github.io) |
| Dendron knowledge base | `~/Documents/Manual Library/Dendron/notes/` |
| Voice/style profile | `~/Documents/Manual Library/Dendron/notes/me/` |
| Reference books (PDF) | `~/Documents/Manual Library/Books/` |
| Code repos & tools | `~/programs/` |
| AI skills | `~/programs/ai-skills/` |
| Zotero bibliography | `~/OneDrive - Harvard University/My Library.bib` |
| Citation styles | `~/Zotero/styles/nature.csl` |
| Presentations | Check manuscript folder first, then `~/Desktop/Projects/{year}/presentation(s)/` |

## Decision Tree — "Where Is That File?"

1. **Recently created/downloaded/opened?** → `~/Downloads/Recents` first, then `~/Downloads`; if found in Downloads, route it out before finishing the task.
2. **A paper or manuscript?** → `~/Desktop/Projects/Manuscripts/{year}_{topic}/`
3. **A grant application?** → `~/Desktop/Projects/Grant/{year}_{name}/`
4. **A job application?** → `~/Desktop/Projects/Job/2025_ap/{institution}/`
5. **Active research project?** → `~/Desktop/Projects/2026/` → `2025/` → `2024/`
6. **CV or bio?** → `~/Desktop/Projects/website/kejunying.com/content/cv/`
7. **A letter (cover, rec, support)?** → `~/Desktop/Projects/letters/`
8. **Code or a tool?** → `~/programs/` or `~/Desktop/Projects/Packages/`
9. **A presentation?** → Manuscript folder first, then `{year}/presentation(s)/`
10. **Notes about a person/project/paper?** → Dendron (see prefixes below)
11. **A reference book?** → `~/Documents/Manual Library/Books/`
12. **Protein structures/designs?** → current project folder, usually under `~/Desktop/Projects/2026/`; Downloads only means not yet routed.
13. **Analysis outputs (CSVs, PNGs, RDS)?** → project folder or dated `_downloads_archive/`; Downloads only means not yet routed.
14. **Can't find it?** → Glob `**/{keyword}*` across `~/Desktop/Projects` and `~/Downloads`

## Dendron Note Prefixes

Look up notes at `~/Documents/Manual Library/Dendron/notes/` using these prefixes:

| Prefix | Content |
|--------|---------|
| `daily.journal.YYYY.MM.DD` | Daily work journal |
| `meet.YYYY.MM.DD` | Meeting notes |
| `proj.YYYY.name` | Project plans and status |
| `sci.paper.authorYear` | Paper annotations |
| `sci.ideas.*` | Research ideas |
| `sci.review.YYYY.*` | Peer reviews |
| `sci.tools.*` | Tool docs |
| `sci.protocol.*` | Lab protocols |
| `user.firstname-lastname` | People/contacts (30+ researchers) |
| `personal.*` | Health, diet, recipes, training, grants |
| `lang.*` | Programming notes (Python, R, ggplot2) |
| `tool.*` | Tool configs (vim, git, ssh, yabai) |
| `prompt.*` | AI prompt templates |

Indices for browsing: `_index.by-person.md`, `_index.by-project.md`, `_index.by-topic.md`

## Authoring Pipeline

Albert writes in Quarto: `.qmd` → `.docx` (primary) → `.pdf` (archival).

- **Citations**: Zotero via `zotero.lua` pandoc filter + `My Library.bib` + `nature.csl`
- **Templates**: Each manuscript has `template.docx` as a Word reference doc
- **Versioning**: `{name}_v{N}.qmd` — pick the highest N. Suffixes: `_redoc` = tracked changes, `_long` = extended, `_v3b` = minor revision
- **Job apps**: Base `.md` files + institution-specific variants (e.g., `cover_letter_MIT_ChemE.md`)

## Downloads — Expected State

Downloads should normally be empty or contain only files actively being handled in the current task. If files accumulate there, use `file-organizer` to route every top-level item to one of:
- the matching project folder under `~/Desktop/Projects`,
- `~/Documents/Manual Library/Personal Info/` for personal/admin records,
- `~/Documents/Manual Library/File Archive/Downloads/YYYY-MM-DD/` for ambiguous review items,
- a non-indexed sensitive archive for password/browser exports.

Do not create new permanent archives inside `~/Downloads`; even `_quarantine/` should be moved out during cleanup.

## Intake Rule

When a task creates, downloads, exports, or modifies a file in `~/Downloads`,
loose `~/Desktop`, or another temporary location:

- If the file belongs to the current task and the destination is obvious from
  the task/project context, move it to the canonical project folder and record
  the final path before finishing.
- If Albert explicitly asks to clean Downloads, evacuate all top-level entries:
  project files go to project `_downloads_archive/YYYY-MM-DD/`, personal/admin
  material goes to Personal Info, sensitive password/browser exports go to a
  non-indexed sensitive archive, and ambiguous files go to a dated File Archive
  review folder.
- Use `tool.file-atlas.md` for canonical routing and `tool.file-intake-log.md`
  for file moves that do not have a better project/person/meeting note.

## Delivering a File to Albert

When a file is the deliverable, hand it off — don't just print the path.

- **Drop it on Albert's shelf with Yoink.** Albert keeps files staged in Yoink (a macOS drag-shelf). His shell alias is `yo='open -a Yoink'`. The alias only exists in interactive zsh, so from a script/non-interactive shell call the underlying command directly:
  ```bash
  open -a Yoink "/absolute/path/to/file"
  ```
  Multiple files: pass them all in one call (`open -a Yoink fileA fileB`). Do this proactively whenever Albert says "yoink it", "put it to yoink", "yo <file>", or asks for a file he'll move/attach elsewhere.
- **Reveal in Finder** (`open -R <file>`) when he needs to find it on disk rather than carry it.
- **Send it inline** (the harness file-send tool) when he just wants the file itself in chat.

These compose — e.g. build a deliverable, `open -a Yoink` it for staging, and confirm in one line.
