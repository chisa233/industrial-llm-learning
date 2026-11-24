"""生成高仿真车间原始脏数据"""

from __future__ import annotations

import csv
import pandas as pd
import random
from pathlib import Path
from typing import Any

from cnc_assistant.config import PROJECT_ROOT

RAW_DIR = PROJECT_ROOT / "data" / "raw"

MACHINE_FIELDS = [
    "machine_id",
    "name",
    "workshop",
    "controller_model",
    "drive_model",
    "comm_card_model",
    "servo_model",
    "firmware_version",
    "status",
]

ALARM_EVENTS_FIELDS = [
    "alarm_id",
    "machine_id",
    "alarm_code",
    "alarm_source",
    "occurred_at",
    "param_snapshot_json",
    "severity",
    "is_resolved"
]

MAINTENANCE_RECORDS_FIELDS = [
    "record_id",
    "machine_id",
    "related_alarm_id",
    "reported_at",
    "operator_claim",
    "technician_note",
    "action_taken",
    "verify_status"
]

def write_csv(
    rows: list[dict[str, Any]],
    fieldnames: list[str],
    path: Path,
    encoding: str = "utf-8",
) -> Path:
    """通用 CSV 写入函数：自动建目录、支持指定编码（UTF-8 / GBK）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding=encoding, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] 生成 {path.name}: {len(rows)} 行（编码: {encoding}）")
    return path

def write_excel(
    rows: list[dict[str, Any]],
    fieldnames: list[str],
    path: Path,
) -> Path:
    """通用 Excel 写入函数：自动建目录并写出 .xlsx。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=fieldnames).to_excel(path, index=False)
    print(f"[OK] 生成 {path.name}: {len(rows)} 行")
    return path

def build_raw_machines() -> list[dict[str, Any]]:
    """6 台覆盖核心原厂手册的机台台账，故意植入 4 类脏数据。"""
    rows = [
        #1：MD500-PLUS + MD38TX1（脏点：前后空格 + 小写）
        {
            "machine_id": "CNC-A01",
            "name": "立式加工中心1号",
            "workshop": "一车间",
            "controller_model": "GSK988MA",

            "drive_model": " md500-plus ",
            "comm_card_model": "MD38TX1",
            "servo_model": "SV660N",
            "firmware_version": "V2.18",
            "status": "alarm",
        },
        #2：MD500 + MD38TX1（同码异机对比；脏点：小写 + 尾部空格）
        {
            "machine_id": "CNC-A02",
            "name": "立式加工中心2号",
            "workshop": "一车间",
            "controller_model": "gsk988ma ",
            "drive_model": "MD500",
            "comm_card_model": "MD38TX1",
            "servo_model": "SV660N",
            "firmware_version": "V2.14",
            "status": "running",
        },
        # 华中 HNC-848（脏点：中文非标状态，违背 schema.sql 的 CHECK 约束）
        {
            "machine_id": "CNC-A03",
            "name": "龙门加工中心3号",
            "workshop": "一车间",
            "controller_model": "HNC-848",
            "drive_model": "MD500-PLUS",
            "comm_card_model": "MD38TX1",
            "servo_model": "SV660N",
            "firmware_version": "V3.02",
            "status": "运行中",
        },
        # Haas NGC（对应主轴过热 4.254 案例）
        {
            "machine_id": "CNC-B01",
            "name": "五轴铣削中心1号",
            "workshop": "二车间",
            "controller_model": "Haas NGC",
            "drive_model": "Haas-Spindle-30HP",
            "comm_card_model": "",
            "servo_model": "Haas-Sigma5",
            "firmware_version": "100.23.000",
            "status": "alarm",
        },
        # 缺失可选字段 firmware_version
        {
            "machine_id": "CNC-B02",
            "name": "卧式加工中心2号",
            "workshop": "二车间",
            "controller_model": "HNC-848",
            "drive_model": "MD500",
            "comm_card_model": "",
            "servo_model": "SV660N",
            "firmware_version": "",
            "status": "maintenance",
        },
        {
            "machine_id": "CNC-C01",
            "name": "精密雕铣机1号",
            "workshop": "三车间",
            "controller_model": "GSK988MA",
            "drive_model": "MD500-PLUS",
            "comm_card_model": "MD38TX1",
            "servo_model": "SV660N",
            "firmware_version": "V2.18",
            "status": "stopped",
        },
    ]
    # 脏点：重复行（模拟人工合并台账时粘重了）
    rows.append(dict(rows[0]))
    return rows

def build_raw_alarm_events() -> list[dict[str, Any]]:
    rows = [
        #severity 写成非规范值
        {
            "alarm_id": "101",
            "machine_id": "CNC-A01",
            "alarm_code": "Err16",
            "alarm_source": "comm_card",
            "occurred_at": "2026-11-23 22:15:00",
            "param_snapshot_json": '{"FD-00": 6005, "comm_card": "MD38TX1"}',
            "severity": "严重",
            "is_resolved": 0
        },
        {
            "alarm_id": "102",
            "machine_id": "CNC-A02",
            "alarm_code": "Err16",
            "alarm_source": "comm_card",
            "occurred_at": "2026/11/23 09:30",
            "param_snapshot_json": '{"FD-00": 6005, "baud_rate": 9600}',
            "severity": "warning",
            "is_resolved": 1
        },

        {
            "alarm_id": "103",
            "machine_id": "CNC-B01",
            "alarm_code": "4.254",
            "alarm_source": "controller",
            "occurred_at": "2026.11.23 19:40",
            "param_snapshot_json": '{"spindle_temp_c": 112.5, "load_pct": 88}',
            "severity": "critical",
            "is_resolved": 0
        },
        {
            "alarm_id": "104",
            "machine_id": "CNC-A01",
            "alarm_code": "952",
            "alarm_source": "controller",
            "occurred_at": "2026-11-22T14:05:00",
            "param_snapshot_json": '{"tool_offset_crc": "ERR"}',
            "severity": "critical",
            "is_resolved": 1
        },
        # 不存在的机台 缺少 param_snapshot_json参数快照
        {
            "alarm_id": "105",
            "machine_id": "CNC-Z02",
            "alarm_code": "Er.620",
            "alarm_source": "servo",
            "occurred_at": "2026-11-21 16:20:00",
            "param_snapshot_json": "",
            "severity": "warning",
            "is_resolved": 1
        }
    ]
    # 随机错误生成循环
    valid_machines = ["CNC-A01", "CNC-A02", "CNC-A03", "CNC-B01", "CNC-B02", "CNC-C01"]
    rng = random.Random(42)
    for i in range(106, 120):
        rows.append({
            "alarm_id": str(i),
            "machine_id": rng.choice(valid_machines),
            "alarm_code": rng.choice(["Err16", "952", "4.254", "Er.620", "Err14"]),
            "alarm_source": rng.choice(["comm_card", "controller", "servo", "drive"]),
            "occurred_at": f"2026-11-{rng.randint(20, 25)} {rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}:00",
            "param_snapshot_json": '{"FD-00": 6005, "baud_rate": 9600}',
            "severity": rng.choice(["warning", "critical", "info"]),
            "is_resolved": rng.choice([0, 1]),
        })
    # 脏点：重复行（模拟人工合并台账时粘重了）
    rows.append(dict(rows[0]))
    return rows

def build_raw_maintenance_records() -> list[dict[str, Any]]:

    rows = [
        {
            "record_id": "201",
            "machine_id": "CNC-A01",
            "related_alarm_id": "101",
            "reported_at": "2026/11/23 23:10",
            "operator_claim": "汇川500换了485卡后上位机读不到，师傅说波特率参数没动过",
            "technician_note": "昨晚更换MD38TX1扩展卡，通电指示灯亮，上位机联机未复测",
            "action_taken": "更换MD38TX1通信扩展卡并重接终端电阻",
            "verify_status": "通电灯亮_联机未复测"
        },
        {
            "record_id": "202",
            "machine_id": "CNC-A02",
            "related_alarm_id": "102",
            "reported_at": "2026-11-23 11:00:00",
            "operator_claim": "二号机500变频器通信中断，问FD-00是不是该改5",
            "technician_note": "核对铭牌为MD500非PLUS，FD-00保持6005，紧固端子后恢复",
            "action_taken": "紧固485端子并复核FD-00=6005",
            "verify_status": "已复测通过"
        },
        # technician_note 缺失
        {
            "record_id": "203",
            "machine_id": "CNC-B01",
            "related_alarm_id": "103",
            "reported_at": "2026.11.23 20:30",
            "operator_claim": "主轴报4.254过热停机，操作工说之前一直正常没修过",
            "technician_note": "昨晚清理过主轴冷却风扇并补液，仅空载试转10分钟正常，未做切削负载复测",
            "action_taken": "清理冷却风扇滤网并补充冷却液",
            "verify_status": "空载正常_负载未复测"
        },
        # verify_status 不规范
        {
            "record_id": "204",
            "machine_id": "CNC-A01",
            "related_alarm_id": "104",
            "reported_at": "2026.11.23 20:30",
            "operator_claim": "处理 952 刀补出错的工单",
            "technician_note": "",
            "action_taken": "重新校验刀补并复测，发现刀补数据异常，重新输入后正常",
            "verify_status": "空载OK"
        }
        ]
    
    # 脏点：重复行（模拟人工合并台账时粘重了）
    rows.append(dict(rows[0]))
    return rows

def main() -> None:
    write_csv(
        rows=build_raw_machines(),
        fieldnames=MACHINE_FIELDS,
        path=RAW_DIR / "machines_raw.csv",
        encoding="utf-8",
    )
    write_csv(
            rows=build_raw_alarm_events(),
            fieldnames=ALARM_EVENTS_FIELDS,
            path=RAW_DIR / "alarm_events_raw.csv",
            encoding="gbk",
    )
    write_excel(
    rows=build_raw_maintenance_records(),
    fieldnames=MAINTENANCE_RECORDS_FIELDS,
    path=RAW_DIR / "maintenance_records_raw.xlsx",
    )

if __name__ == "__main__":
    main()