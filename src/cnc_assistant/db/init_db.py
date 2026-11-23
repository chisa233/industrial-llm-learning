from pathlib import Path
import sqlite3

from cnc_assistant.config import load_settings

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def get_connection(db_path: Path) -> sqlite3.Connection:
    """打开 SQLite 连接并强制开启外键约束。"""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_database(db_path: Path | None = None) -> Path:
    """按 schema.sql 初始化三张表与索引，返回最终数据库路径。"""
    target_path = db_path if db_path is not None else load_settings().db_path
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")

    conn = get_connection(target_path)
    try:
        conn.executescript(schema_sql)
    finally:
        conn.close()
    return target_path


if __name__ == "__main__":
    created = init_database()
    print(f"数据库初始化完成：{created}")