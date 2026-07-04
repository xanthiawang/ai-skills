---
name: dendron-config
description: Configure Dendron vault settings for universal access across all Dendron skills. Auto-detects vault from current directory or allows manual configuration. Use when setting up Dendron integration or switching between vaults.
---

# Dendron Configuration

Universal configuration system for Dendron skills. Auto-detects vault location or allows manual configuration.

## Auto-Detection

Dendron skills automatically detect your vault by:

1. **Current directory**: Check if you're inside a Dendron vault
2. **dendron.yml**: Look for `dendron.yml` in parent directories
3. **Workspace config**: Read from VSCode/Cursor workspace settings
4. **Saved config**: Use `~/.cursor/dendron-config.json`

## Manual Configuration

Set vault explicitly:

```bash
@dendron-config set /Users/A.Y/Documents/Manual Library/Dendron/notes
```

Or configure multiple vaults:

```bash
@dendron-config add-vault personal ~/Dendron/personal
@dendron-config add-vault work ~/work/dendron-vault
@dendron-config set-default personal
```

## Configuration File

Location: `~/.cursor/dendron-config.json`

```json
{
  "default_vault": "personal",
  "vaults": {
    "personal": {
      "path": "/Users/A.Y/Documents/Manual Library/Dendron/notes",
      "db_path": "/Users/A.Y/Documents/Manual Library/Dendron/notes.db"
    },
    "work": {
      "path": "/Users/A.Y/work/dendron-vault",
      "db_path": "/Users/A.Y/work/dendron.db"
    }
  },
  "screenpipe": {
    "enabled": true,
    "auto_journal": true
  }
}
```

## Vault Detection Logic

```python
def find_vault() -> str:
    # 1. Check saved config
    if config_exists():
        return load_config()['default_vault']
    
    # 2. Check current directory
    cwd = os.getcwd()
    if is_dendron_vault(cwd):
        return cwd
    
    # 3. Search parent directories for dendron.yml
    for parent in get_parents(cwd):
        if (parent / 'dendron.yml').exists():
            return str(parent / 'notes')
    
    # 4. Ask user
    return prompt_for_vault()
```

## Commands

### Set Default Vault

```bash
@dendron-config set /path/to/vault
```

### List Vaults

```bash
@dendron-config list
```

### Add Vault

```bash
@dendron-config add-vault <name> <path>
```

### Switch Vault

```bash
@dendron-config use <name>
```

### Show Current

```bash
@dendron-config current
```

## Integration

All Dendron skills (dendron-add, dendron-query, dendron-generate) use this configuration automatically:

```python
from dendron_config import get_vault_path

vault = get_vault_path()
# Auto-detects or uses saved config
```

## Related Skills

- **[[dendron-add]]** - Add notes to vault
- **[[dendron-query]]** - Query vault
- **[[dendron-generate]]** - Generate content
- **[[screenpipe-daily-journal]]** - Uses Dendron config for journal path
