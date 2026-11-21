from pathlib import Path

from cnc_assistant.config import load_settings


def test_load_settings_defaults(monkeypatch, tmp_path: Path) -> None:
    """未配置环境变量时，应回退到安全的本地默认值。"""
    for key in ("LLM_BASE_URL", "LLM_MODEL", "LLM_API_KEY", "DB_PATH"):
        monkeypatch.delenv(key, raising=False)

    settings = load_settings(env_file=tmp_path / "not_exist.env")

    assert settings.llm_base_url == "http://127.0.0.1:11434/v1"
    assert settings.llm_model == "qwen3:0.6b"
    assert settings.db_path.name == "cnc_ops.db"


def test_load_settings_from_env(monkeypatch, tmp_path: Path) -> None:
    """环境变量存在时，应优先读取环境变量的值。"""
    monkeypatch.setenv("LLM_BASE_URL", "http://192.168.1.100:11434/v1")
    monkeypatch.setenv("LLM_MODEL", "qwen3:8b")
    monkeypatch.setenv("DB_PATH", "custom.db")

    settings = load_settings(env_file=tmp_path / "not_exist.env")

    assert settings.llm_base_url == "http://192.168.1.100:11434/v1"
    assert settings.llm_model == "qwen3:8b"
    assert settings.db_path.name == "custom.db"