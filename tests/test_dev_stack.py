from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_dev_scripts_exist_and_parse() -> None:
    for name in ("dev-up.sh", "dev-down.sh"):
        path = REPO_ROOT / "scripts" / name
        assert path.is_file()
        text = path.read_text(encoding="utf-8")
        assert "dev-mcp.pid" in text


def test_dev_config_loads() -> None:
    from alloccontext.config import load_config

    config = load_config(REPO_ROOT / "config" / "config.dev.yaml")
    assert config.paths.db == Path("state/dev/alloccontext.db")
    assert config.ingest.sources["kraken"] is False
    assert config.ingest.sources["fear_greed"] is True


def test_local_dev_doc_exists() -> None:
    doc = REPO_ROOT / "docs" / "local-dev.md"
    assert doc.is_file()
    assert "dev-up.sh" in doc.read_text(encoding="utf-8")
