from pathlib import Path
import sqlite3

import pytest

from cnc_assistant.db.init_db import get_connection, init_database


def test_init_database_creates_tables_and_indexes(tmp_path: Path) -> None:
    """初始化后应建出 3 张表与 4 个自定义索引。"""
    db_path = init_database(tmp_path / "test_cnc.db")
    conn = get_connection(db_path)
    try:
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        indexes = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            )
        }
    finally:
        conn.close()

    assert {"machines", "alarm_events", "maintenance_records"}.issubset(tables)
    assert {
        "idx_machines_models",
        "idx_alarms_machine_time",
        "idx_alarms_code_source",
        "idx_maint_machine_verify",
    }.issubset(indexes)


def test_foreign_key_blocks_unknown_machine(tmp_path: Path) -> None:
    """往报警表插入不存在的 machine_id，必须被外键拦截报错。"""
    db_path = init_database(tmp_path / "test_cnc.db")
    conn = get_connection(db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO alarm_events
                    (machine_id, alarm_code, alarm_source, occurred_at, severity)
                VALUES
                    ('CNC-GHOST', 'Err16', 'drive', '2026-11-23T18:00:00', 'critical')
                """
            )
    finally:
        conn.close()


def test_check_constraint_blocks_invalid_verify_status(tmp_path: Path) -> None:
    """往维修表插入不在白名单里的 verify_status，必须被 CHECK 约束拦截。"""
    db_path = init_database(tmp_path / "test_cnc.db")
    conn = get_connection(db_path)
    try:
        conn.execute(
            """
            INSERT INTO machines
                (machine_id, name, workshop, controller_model, drive_model, comm_card_model)
            VALUES
                ('CNC-A01', '一车间立加1号机', 'A区', 'GSK988MA', 'MD500-PLUS', 'MD38TX1')
            """
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO maintenance_records
                    (machine_id, reported_at, operator_claim, action_taken, verify_status)
                VALUES
                    ('CNC-A01', '2026-11-23T18:30:00', '师傅说参数没动过', '更换MD38TX1', '随便写的状态')
                """
            )
    finally:
        conn.close()