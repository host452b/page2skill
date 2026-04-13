from __future__ import annotations

import os
import platform
import pathlib
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


_DEFAULTS = {
    "vault_path": None,
    "skill_dir": None,
    "manifest_path": None,
    "taxonomy_path": None,
    "chrome_dir": None,
}

_ENV_PREFIX = "BOOKMARK2SKILL_"


def _detect_chrome_dir() -> str:
    """Return Chrome base directory (containing all profiles) for current OS."""
    system = platform.system()
    home = pathlib.Path.home()
    if system == "Darwin":
        return str(home / "Library/Application Support/Google/Chrome")
    elif system == "Linux":
        return str(home / ".config/google-chrome")
    elif system == "Windows":
        local = os.environ.get("LOCALAPPDATA", "")
        return str(pathlib.Path(local) / "Google/Chrome/User Data")
    return str(home / ".config/google-chrome")


def _read_toml(config_path: pathlib.Path) -> dict[str, Any]:
    """Read config.toml and flatten [paths] section to top-level keys."""
    if not config_path.is_file():
        return {}
    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    flat: dict[str, Any] = {}
    for key, value in data.get("paths", {}).items():
        flat[key] = value
    return flat


def _read_env() -> dict[str, str]:
    """Read BOOKMARK2SKILL_* env vars into a flat dict."""
    result: dict[str, str] = {}
    for key, value in os.environ.items():
        if key.startswith(_ENV_PREFIX):
            config_key = key[len(_ENV_PREFIX):].lower()
            result[config_key] = value
    return result


def load_config(
    *,
    home_dir: pathlib.Path | None = None,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Load config with layered precedence: defaults < toml < env < overrides."""
    home = pathlib.Path(home_dir) if home_dir else pathlib.Path.home()
    b2s_dir = home / ".bookmark2skill"

    cfg = dict(_DEFAULTS)
    cfg["manifest_path"] = str(b2s_dir / "manifest.json")
    cfg["taxonomy_path"] = str(b2s_dir / "taxonomy.toml")
    cfg["chrome_dir"] = _detect_chrome_dir()

    toml_values = _read_toml(b2s_dir / "config.toml")
    for key, value in toml_values.items():
        if key in cfg:
            cfg[key] = value

    env_values = _read_env()
    for key, value in env_values.items():
        if key in cfg:
            cfg[key] = value

    if overrides:
        for key, value in overrides.items():
            if key in cfg and value is not None:
                cfg[key] = value

    return cfg
