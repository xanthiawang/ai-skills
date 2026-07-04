#!/usr/bin/env python3
"""
Universal Dendron configuration manager.
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict

CONFIG_PATH = Path.home() / ".cursor/dendron-config.json"


def load_config() -> Dict:
    """Load configuration or return defaults."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)

    return {
        "default_vault": None,
        "vaults": {},
        "screenpipe": {"enabled": True, "auto_journal": True},
    }


def save_config(config: Dict):
    """Save configuration."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def is_dendron_vault(path: Path) -> bool:
    """Check if directory is a Dendron vault."""
    path = Path(path)

    # Look for dendron indicators
    if (path / "dendron.yml").exists():
        return True
    if (path / "root.schema.yml").exists():
        return True
    if (path.parent / "dendron.yml").exists():
        return True

    return False


def find_vault_from_cwd() -> Optional[str]:
    """Find Dendron vault from current working directory."""
    cwd = Path.cwd()

    # Check if we're in a vault
    if is_dendron_vault(cwd):
        return str(cwd)

    # Check parent directories
    for parent in [cwd] + list(cwd.parents):
        if (parent / "dendron.yml").exists():
            # Found workspace root
            notes_dir = parent / "notes"
            if notes_dir.exists():
                return str(notes_dir)
            return str(parent)

    return None


def get_vault_path(vault_name: Optional[str] = None) -> str:
    """Get vault path by name or default."""
    config = load_config()

    # If specific vault requested
    if vault_name:
        if vault_name in config["vaults"]:
            return config["vaults"][vault_name]["path"]
        raise ValueError(f"Vault '{vault_name}' not found in config")

    # Try default vault
    if config["default_vault"]:
        default = config["default_vault"]
        if default in config["vaults"]:
            return config["vaults"][default]["path"]

    # Try to auto-detect from current directory
    vault = find_vault_from_cwd()
    if vault:
        return vault

    # No vault found
    raise ValueError(
        "No Dendron vault configured. Run:\n" "  @dendron-config set /path/to/vault"
    )


def add_vault(name: str, path: str):
    """Add a vault to configuration."""
    config = load_config()

    path = str(Path(path).resolve())

    if not is_dendron_vault(Path(path)):
        print(f"Warning: {path} doesn't appear to be a Dendron vault")

    config["vaults"][name] = {
        "path": path,
        "db_path": str(Path(path).parent / "notes.db"),
    }

    # Set as default if first vault
    if not config["default_vault"]:
        config["default_vault"] = name

    save_config(config)
    print(f"Added vault '{name}': {path}")


def set_default(name: str):
    """Set default vault."""
    config = load_config()

    if name not in config["vaults"]:
        raise ValueError(f"Vault '{name}' not found")

    config["default_vault"] = name
    save_config(config)
    print(f"Set default vault: {name}")


def list_vaults():
    """List all configured vaults."""
    config = load_config()

    if not config["vaults"]:
        print("No vaults configured.")
        return

    print("Configured vaults:")
    for name, vault_config in config["vaults"].items():
        default = " (default)" if name == config["default_vault"] else ""
        print(f"  {name}{default}: {vault_config['path']}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Manage Dendron configuration")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # set command
    set_parser = subparsers.add_parser("set", help="Set vault path")
    set_parser.add_argument("path", help="Vault path")

    # add-vault command
    add_parser = subparsers.add_parser("add-vault", help="Add named vault")
    add_parser.add_argument("name", help="Vault name")
    add_parser.add_argument("path", help="Vault path")

    # use command
    use_parser = subparsers.add_parser("use", help="Switch to vault")
    use_parser.add_argument("name", help="Vault name")

    # list command
    subparsers.add_parser("list", help="List vaults")

    # current command
    subparsers.add_parser("current", help="Show current vault")

    args = parser.parse_args()

    if args.command == "set":
        add_vault("default", args.path)
        set_default("default")

    elif args.command == "add-vault":
        add_vault(args.name, args.path)

    elif args.command == "use":
        set_default(args.name)

    elif args.command == "list":
        list_vaults()

    elif args.command == "current":
        try:
            vault = get_vault_path()
            print(f"Current vault: {vault}")
        except ValueError as e:
            print(f"Error: {e}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
