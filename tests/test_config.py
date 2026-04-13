import os
import pytest
from bookmark2skill.config import load_config


def test_load_defaults_when_no_config_exists(tmp_home):
    """Config returns sensible defaults when no config file exists."""
    cfg = load_config(home_dir=tmp_home)
    assert cfg["vault_path"] is None
    assert cfg["skill_dir"] is None
    assert cfg["manifest_path"] == str(tmp_home / ".bookmark2skill" / "manifest.json")
    assert cfg["taxonomy_path"] == str(tmp_home / ".bookmark2skill" / "taxonomy.toml")


def test_load_from_toml(tmp_home):
    """Config reads values from config.toml."""
    config_dir = tmp_home / ".bookmark2skill"
    config_dir.mkdir(exist_ok=True)
    (config_dir / "config.toml").write_text(
        '[paths]\nvault_path = "/my/vault"\nskill_dir = "/my/skills"\n',
        encoding="utf-8",
    )
    cfg = load_config(home_dir=tmp_home)
    assert cfg["vault_path"] == "/my/vault"
    assert cfg["skill_dir"] == "/my/skills"


def test_env_vars_override_toml(tmp_home, monkeypatch):
    """Environment variables override config.toml values."""
    config_dir = tmp_home / ".bookmark2skill"
    config_dir.mkdir(exist_ok=True)
    (config_dir / "config.toml").write_text(
        '[paths]\nvault_path = "/from/toml"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("BOOKMARK2SKILL_VAULT_PATH", "/from/env")
    cfg = load_config(home_dir=tmp_home)
    assert cfg["vault_path"] == "/from/env"


def test_cli_overrides_take_highest_priority(tmp_home, monkeypatch):
    """CLI-provided overrides beat env vars and toml."""
    monkeypatch.setenv("BOOKMARK2SKILL_VAULT_PATH", "/from/env")
    cfg = load_config(home_dir=tmp_home, overrides={"vault_path": "/from/cli"})
    assert cfg["vault_path"] == "/from/cli"


def test_chrome_profile_auto_detect(tmp_home):
    """Chrome profile path is auto-detected for the current OS."""
    cfg = load_config(home_dir=tmp_home)
    assert cfg["chrome_profile"] is not None
    assert "Chrome" in cfg["chrome_profile"] or "chrome" in cfg["chrome_profile"]
