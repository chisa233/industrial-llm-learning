"""读取 data/raw/ 三份原始脏数据，用 Pandas 清洗并入库到 SQLite。"""

from __future__ import annotations

import pandas as pd

from cnc_assistant.db.init_db import get_connection, init_database
from cnc_assistant.config import PROJECT_ROOT

RAW_DIR = PROJECT_ROOT / "data" / "raw"

STATUS_MAP = {
    "运行中": "running",
    "报警": "alarm",
    "维修中": "maintenance",
    "停机": "stopped",
}

MODEL_CANONICAL_MAP = {
    "HAAS NGC": "Haas NGC",
    "HAAS-SPINDLE-30HP": "Haas-Spindle-30HP",
    "HAAS-SIGMA5": "Haas-Sigma5",
}

SEVERITY_MAP = {
    "一般": "info",
    "中": "warning",
    "严重": "critical",
}

VERIFY_STATUS_MAP = {
    "空载OK": "空载正常_负载未复测",
    "未复测": "待复测",
}

def clean_machines(df: pd.DataFrame) -> pd.DataFrame:
    """清洗设备资产台账：去空格、规范型号/状态、主键去重。"""
    cleaned = df.copy()

    # 1. 所有字符串列统一去首尾空格
    for col in cleaned.columns:
        cleaned[col] = cleaned[col].astype(str).str.strip()

    # 2. 规范已知小写型号（注意不粗暴全列 .upper()，避免把 Haas NGC 破坏成 HAAS NGC）
    for col in ["controller_model", "drive_model", "comm_card_model", "servo_model"]:
        cleaned[col] = cleaned[col].str.upper().replace(MODEL_CANONICAL_MAP)

    # 3. 中文非标状态映射为 schema.sql 允许的英文枚举
    cleaned["status"] = cleaned["status"].replace(STATUS_MAP)

    # 4. 可选字段空字符串转为 None（入库 SQLite 后变成真正的 NULL）
    for col in ["comm_card_model", "servo_model", "firmware_version"]:
        cleaned[col] = cleaned[col].replace({"": None})

    # 5. 按主键去重，保留第一条
    cleaned = cleaned.drop_duplicates(subset=["machine_id"], keep="first").reset_index(drop=True)
    return cleaned

def clean_alarm_events(df: pd.DataFrame, valid_machine_ids: set) -> pd.DataFrame:
    cleaned = df.copy()

    for col in cleaned.columns:
        cleaned[col] = cleaned[col].astype(str).str.strip()

    cleaned["occurred_at"] = pd.to_datetime(
        cleaned["occurred_at"], format="mixed"
    ).dt.strftime("%Y-%m-%d %H:%M:%S")   
    
    for col in ["severity"]:
        cleaned[col] = cleaned[col].str.lower().replace(SEVERITY_MAP)

    cleaned = cleaned[cleaned["machine_id"].isin(valid_machine_ids)]

    cleaned = cleaned.drop_duplicates(subset=["alarm_id"], keep="first").reset_index(drop=True)

    for col in ["param_snapshot_json"]:
        cleaned[col] = cleaned[col].replace({"": None})

    for col in ["alarm_id", "is_resolved"]:
        cleaned[col] = cleaned[col].astype(int)

    return cleaned

def clean_maintenance_records(df: pd.DataFrame, valid_machine_ids: set, valid_alarm_ids: set) -> pd.DataFrame:
    cleaned = df.copy()

    for col in cleaned.columns:
        cleaned[col] = cleaned[col].astype(str).str.strip()

    cleaned["reported_at"] = pd.to_datetime(
            cleaned["reported_at"], format="mixed"
        ).dt.strftime("%Y-%m-%d %H:%M:%S") 

    cleaned = cleaned.drop_duplicates(subset=["record_id"], keep="first").reset_index(drop=True)

    cleaned["verify_status"] = cleaned["verify_status"].replace(VERIFY_STATUS_MAP)

    cleaned = cleaned[cleaned["machine_id"].isin(valid_machine_ids)]

    cleaned["related_alarm_id"] = cleaned["related_alarm_id"].apply(
        lambda x: int(x) if x.isdigit() and int(x) in valid_alarm_ids else None
    )
    for col in ["technician_note"]:
        cleaned[col] = cleaned[col].replace({"": None})

    for col in ["record_id"]:
        cleaned[col] = cleaned[col].astype(int)
    
    return cleaned

def load_to_sqlite(
    machines: pd.DataFrame,
    alarm_events: pd.DataFrame,
    maintenance_records: pd.DataFrame,
) -> None:
    """幂等写入 SQLite：保留 schema.sql 约束，先子后父清空，再先父后子插入。"""
    db_path = init_database()
    conn = get_connection(db_path)
    try:
        with conn:
            # 1. 先子表后父表清空旧数据
            conn.execute("DELETE FROM maintenance_records;")
            conn.execute("DELETE FROM alarm_events;")
            conn.execute("DELETE FROM machines;")

            # 2. 先父表后子表追加写入（保留主外键、CHECK 约束和索引）
            machines.to_sql("machines", conn, if_exists="append", index=False)
            alarm_events.to_sql("alarm_events", conn, if_exists="append", index=False)
            maintenance_records.to_sql("maintenance_records", conn, if_exists="append", index=False)
    finally:
        conn.close()
    print(f"[OK] 已写入数据库: {db_path}")

def main() -> None:
    raw_machines = pd.read_csv(RAW_DIR / "machines_raw.csv", dtype=str, keep_default_na=False)
    machines = clean_machines(raw_machines)
    print(f"[machines] 清洗前: {len(raw_machines)} 行 -> 清洗后: {len(machines)} 行")
    print(machines[["machine_id", "controller_model", "drive_model", "status"]])

    # 生成有效机台 ID 集合，用于清洗报警事件
    valid_machine_ids = set(machines["machine_id"])

    raw_alarm_events = pd.read_csv(RAW_DIR / "alarm_events_raw.csv",encoding= "gbk" , dtype=str, keep_default_na=False)
    alarm_events = clean_alarm_events(raw_alarm_events,valid_machine_ids)
    print(f"[alarm_events] 清洗前: {len(raw_alarm_events)} 行 -> 清洗后: {len(alarm_events)} 行")
    print(alarm_events[["alarm_id", "machine_id", "alarm_code", "occurred_at", "severity"]])

    # 生成有效报警 ID 集合，用于清洗维修记录
    valid_alarm_ids = set(alarm_events["alarm_id"])

    raw_maintenance_records = pd.read_excel(RAW_DIR / "maintenance_records_raw.xlsx", dtype=str, keep_default_na=False)
    maintenance_records = clean_maintenance_records(raw_maintenance_records, valid_machine_ids, valid_alarm_ids)
    print(f"[maintenance_records] 清洗前: {len(raw_maintenance_records)} 行 -> 清洗后: {len(maintenance_records)} 行")
    print(maintenance_records[["record_id", "machine_id", "related_alarm_id", "action_taken"]])

    load_to_sqlite(machines, alarm_events, maintenance_records)

if __name__ == "__main__":
    main()