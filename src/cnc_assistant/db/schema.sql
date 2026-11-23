-- 每次连接 SQLite 必须显式开启外键检查，否则外键约束不生效
PRAGMA foreign_keys = ON;

-- 1. 设备资产台账：绑定机台与其数控系统、主轴变频、通信卡、伺服的精确型号
CREATE TABLE IF NOT EXISTS machines (
    machine_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    workshop TEXT NOT NULL,
    controller_model TEXT NOT NULL,
    drive_model TEXT NOT NULL,
    comm_card_model TEXT,
    servo_model TEXT,
    firmware_version TEXT,
    status TEXT NOT NULL DEFAULT 'running'
        CHECK (status IN ('running', 'alarm', 'maintenance', 'stopped'))
);

-- 2. 报警事件与事发参数快照：支撑同码异机过滤、高频统计与实测值核验
CREATE TABLE IF NOT EXISTS alarm_events (
    alarm_id INTEGER PRIMARY KEY,
    machine_id TEXT NOT NULL,
    alarm_code TEXT NOT NULL,
    alarm_source TEXT NOT NULL
        CHECK (alarm_source IN ('controller', 'drive', 'comm_card', 'servo')),
    occurred_at TEXT NOT NULL,
    param_snapshot_json TEXT,
    severity TEXT NOT NULL
        CHECK (severity IN ('info', 'warning', 'critical')),
    is_resolved INTEGER NOT NULL DEFAULT 0
        CHECK (is_resolved IN (0, 1)),
    FOREIGN KEY (machine_id) REFERENCES machines (machine_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- 3. 维修与交接工单：记录现场口语报修、维修动作与复测状态，支撑多源冲突检测
CREATE TABLE IF NOT EXISTS maintenance_records (
    record_id INTEGER PRIMARY KEY,
    machine_id TEXT NOT NULL,
    related_alarm_id INTEGER,
    reported_at TEXT NOT NULL,
    operator_claim TEXT NOT NULL,
    technician_note TEXT,
    action_taken TEXT NOT NULL,
    verify_status TEXT NOT NULL DEFAULT '待复测'
        CHECK (verify_status IN ('待复测', '空载正常_负载未复测', '通电灯亮_联机未复测', '已复测通过')),
    FOREIGN KEY (machine_id) REFERENCES machines (machine_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (related_alarm_id) REFERENCES alarm_events (alarm_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

-- 4. 高频查询索引（直接服务后续核验 SQL 与 Agent 工具调用）
CREATE INDEX IF NOT EXISTS idx_machines_models
    ON machines (controller_model, drive_model, comm_card_model);

CREATE INDEX IF NOT EXISTS idx_alarms_machine_time
    ON alarm_events (machine_id, occurred_at);

CREATE INDEX IF NOT EXISTS idx_alarms_code_source
    ON alarm_events (alarm_code, alarm_source);

CREATE INDEX IF NOT EXISTS idx_maint_machine_verify
    ON maintenance_records (machine_id, verify_status, reported_at);