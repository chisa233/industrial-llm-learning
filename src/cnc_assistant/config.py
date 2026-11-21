from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

# 定位项目根目录：config.py -> cnc_assistant -> src -> 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    """项目统一配置对象（frozen=True 表示只读，防止运行中途被误改）。"""

    llm_base_url: str
    llm_model: str
    llm_api_key: str
    db_path: Path


def load_settings(env_file: Path | None = None) -> Settings:
    """从环境变量（及 .env 文件）加载项目配置。"""
    target_env = env_file if env_file is not None else PROJECT_ROOT / ".env"
    load_dotenv(dotenv_path=target_env, override=False)

    raw_db_path = Path(os.getenv("DB_PATH", "data/processed/cnc_ops.db"))
    db_path = raw_db_path if raw_db_path.is_absolute() else PROJECT_ROOT / raw_db_path

    return Settings(
        llm_base_url=os.getenv("LLM_BASE_URL", "http://127.0.0.1:11434/v1"),
        llm_model=os.getenv("LLM_MODEL", "qwen3:0.6b"),
        llm_api_key=os.getenv("LLM_API_KEY", "ollama"),
        db_path=db_path,
    )