# File Intake Schema

Use this contract for file intake candidates, sync summaries, and audit records.

## Modes

| Mode | Writes allowed | Use |
|---|---:|---|
| `scan` | no | Inventory recent Downloads/Desktop files and print suggestions. |
| `current-task-route` | yes, narrow | Move only files created/downloaded by the current agent task when destination is obvious and denylist checks pass. |
| `downloads-evacuation` | yes, broad after explicit approval | Route every top-level Downloads item to a project, Personal Info, File Archive review, software archive, or non-indexed sensitive archive. |
| `broad-cleanup` | checklist only | Use `fs_drift_scan.py` and Albert-reviewed `fs_drift_apply.py`. |
| `sync-summary` | no | Include file-intake counts in `/sync`; never move files. |

## Candidate Fields

Every scanner output candidate should include:

- `path`: absolute source path.
- `candidate_id`: stable identifier derived from path, size, and mtime.
- `name`: basename.
- `kind`: coarse type such as `pdf`, `document`, `spreadsheet`, `slide-deck`, `image`, `archive`, `installer`, `structure`, `folder`, or `unknown`.
- `size_bytes`: integer size if available.
- `modified_at`: local ISO-like timestamp.
- `age_days`: whole days since modification.
- `intent`: `route`, `record`, `review`, `archive`, `rename-candidate`, `installer-cleanup`, or `sensitive-archive`.
- `confidence`: `high`, `medium`, or `low`.
- `route_hint`: suggested destination family or empty string.
- `safe_action`: `current-task-only`, `ask-before-move`, `checklist-only`, or `record-only`.
- `rationale`: short reason for the suggestion.

## Confidence Meanings

- `high`: file name, extension, task context, and existing folder convention all agree. Eligible for current-task routing if the agent created/downloaded it in the same task.
- `medium`: file likely belongs to a known zone, but personal/admin sensitivity or incomplete context requires approval.
- `low`: leave in place and ask.

## Hard Denylist

Do not auto-move or rename these without explicit approval:

- Secrets, credentials, OAuth tokens, API keys, `.env` files, SSH keys, 1Password exports, browser state, or auth databases.
- Personal identity, immigration, tax, legal, medical, bank, payroll, or original signed records.
- Databases, large research datasets, app bundles, package installers, virtual environments, caches, or generated build trees.
- Files modified by another app within the last 24 hours unless they were created by the current task and the task requires delivery.

When Albert has explicitly approved Downloads cleanup, secrets and browser
exports may be moved out of Downloads, but only into a non-indexed sensitive
archive. Do not place them under the vault, normal File Archive manifests, or
project folders, and do not log exact sensitive filenames in vault notes.

## Audit Record

Append one bullet per routed file to the most specific project/person/meeting note or to `tool.file-intake-log.md`:

```markdown
- YYYY-MM-DD HH:MM source=`/absolute/original/path` final=`/absolute/final/path` action=`moved|renamed|recorded` mode=`current-task-route|approved-cleanup` confidence=`high|medium|low` rationale="short reason" approval="current-task obvious|Albert approved|dry-run only"
```

Do not store secrets or private content excerpts in the audit record. Paths and operational rationale are enough.

For `downloads-evacuation`, a manifest plus a summary record is preferred over
hundreds of vault bullets. Keep sensitive manifests outside indexed roots.

## Sync Summary Contract

`/sync` may include a file-intake section with:

- number of candidates scanned,
- count by `safe_action`,
- top five high-signal candidates,
- path to a saved JSON/markdown report if one was written.

`/sync` must not call an apply/move command unless Albert explicitly asked for cleanup in the same turn.
