# 数据模型翻译对照表

> 本文件用于把数据库中的英文表名、字段名对照成中文，方便非计算机背景的读者理解。
> **英文原名保持不变**，本表只做翻译与释义。
>
> 三张表的关系：`machines`（机床台账）→ 产生 → `alarm_events`（报警事件）→ 关联 → `maintenance_records`（维修记录）。
> 一句话：每台机床会报出若干报警，每次报警可能对应若干条维修记录。


---

## 1. machines（机床台账）

记录每台机床的身份信息和硬件配置，相当于设备的「身份证」。

| 英文原名               | 类型      | 中文含义   | 说明                                                         |
| ------------------ | ------- | ------ | ---------------------------------------------------------- |
| `machine_id`       | TEXT PK | 机床编号   | 主键，唯一标识一台机床                                                |
| `name`             | TEXT    | 机床名称   | 便于人阅读的叫法，如「三号加工中心」                                         |
| `workshop`         | TEXT    | 所在车间   | 机床物理位置                                                     |
| `controller_model` | TEXT    | 数控系统型号 | 机床的「大脑」，决定能执行哪些指令                                          |
| `drive_model`      | TEXT    | 驱动型号   | 伺服驱动器型号 -> 主轴变频器型号（如 MD500 / MD500-PLUS）                   |
| `comm_card_model`  | TEXT    | 通讯卡型号  | 负责与外部系统通信的板卡(可为空)                                          |
| `servo_model`      | TEXT    | 伺服电机型号 | 伺服电机型号 → 进给伺服驱动型号（如 SV660N，可为空）                            |
| `firmware_version` | TEXT    | 固件版本   | 控制器内置软件的版本号（可为空）                                           |
| `status`           | TEXT    | 当前状态   | status：running / alarm / maintenance / stopped（默认 running） |

## 2. alarm_events（报警事件）

记录机床每一次报警，是排查问题的核心数据。

| 英文原名                  | 类型         | 中文含义   | 说明                                                  |
| --------------------- | ---------- | ------ | --------------------------------------------------- |
| `alarm_id`            | INTEGER PK | 报警记录编号 | 主键，自增                                               |
| `machine_id`          | TEXT FK    | 机床编号   | 外键，指向 `machines.machine_id`                         |
| `alarm_code`          | TEXT       | 报警代码   | 机床给出的错误码，如 `ALM-401`                                |
| `alarm_source`        | TEXT       | 报警来源   | alarm_source：controller / drive / comm_card / servo |
| `occurred_at`         | TEXT       | 报警发生时间 | ISO 8601 格式存储                                       |
| `param_snapshot_json` | TEXT       | 参数快照   | 报警瞬间机床各项参数的「拍照」，以 JSON 文本存储，供事后复盘                   |
| `severity`            | TEXT       | 严重程度   | severity：info / warning / critical                  |
| `is_resolved`         | INTEGER    | 是否已解决  | `0` = 未解决，`1` = 已解决（SQLite 无布尔类型）                   |

## 3. maintenance_records（维修记录）

记录每一次维修/保养的过程和结果。

| 英文原名               | 类型         | 中文含义   | 说明                                                          |
| ------------------ | ---------- | ------ | ----------------------------------------------------------- |
| `record_id`        | INTEGER PK | 维修记录编号 | 主键，自增                                                       |
| `machine_id`       | TEXT FK    | 机床编号   | 外键，指向 `machines.machine_id`                                 |
| `related_alarm_id` | INTEGER FK | 关联报警编号 | 外键，指向 `alarm_events.alarm_id`；可为空（如定期保养不是因报警而修）             |
| `reported_at`      | TEXT       | 报修时间   | 与「报警发生时间」区分：一个是机器报的，一个是人报的                                  |
| `operator_claim`   | TEXT       | 操作员描述  | 报修时操作员陈述的现象                                                 |
| `technician_note`  | TEXT       | 维修人员记录 | 排查过程与结论（可为空）                                                |
| `action_taken`     | TEXT       | 处理措施   | 实际做了什么，如「更换伺服电机」                                            |
| `verify_status`    | TEXT       | 验证状态   | verify_status：待复测 / 空载正常_负载未复测 / 通电灯亮_联机未复测 / 已复测通过（默认 待复测） |

## 4. 表关系

| 关系                                 | 符号  | 含义                          |
| ---------------------------------- | --- | --------------------------- |
| machines → alarm_events            | 一对多 | 一台机床可产生 0 到多条报警，每条报警只属于一台机床 |
| machines → maintenance_records     | 一对多 | 一台机床可有 0 到多条维修记录            |
| alarm_events → maintenance_records | 一对多 | 一条报警可关联 0 到多条维修记录           |

## 5.外键级联与索引

外键与索引：机台删除采用 `ON DELETE RESTRICT` 保护历史工单；
`related_alarm_id` 允许为空并采用 `ON DELETE SET NULL`；
按后续核验 SQL 场景预建 4 个高频联合索引。

|索引名|所在表与字段|服务哪类查询|
|---|---|---|
|`idx_machines_models`|`machines (controller_model, drive_model, comm_card_model)`|按型号组合反查机台|
|`idx_alarms_machine_time`|`alarm_events (machine_id, occurred_at)`|查单台机床近期报警流水|
|`idx_alarms_code_source`|`alarm_events (alarm_code, alarm_source)`|同码异机过滤、高频报警 `GROUP BY` 统计|
|`idx_maint_machine_verify`|`maintenance_records (machine_id, verify_status, reported_at)`|`JOIN` 历史工单快速排查未复测记录|
[[SQLite 常用命令汇总#外键（`FOREIGN KEY`）与级联动作]]
[[SQLite 常用命令汇总#索引 `CREATE INDEX`]]

## 6. 术语速查

统一译法，避免同一概念多种叫法。

| 英文 | 推荐中文 | 避免使用 | 备注 |
|---|---|---|---|
| machine | 机床 | 机器、设备（泛指时可用「设备」） | 本项目特指数控机床 |
| workshop | 车间 | 工厂、工坊 | |
| controller | 数控系统 / 控制器 | 控制机 | 首次出现建议写「数控系统（controller）」 |
| drive | 驱动器 | 驱动 | |
| servo | 伺服电机 | 伺服 | |
| firmware | 固件 | 固件程序 | 出厂烧录在硬件里的软件 |
| alarm | 报警 | 警报、告警 | |
| alarm event | 报警事件 | 报警记录 | 「事件」强调一次发生 |
| severity | 严重程度 | 等级、优先级 | |
| resolve | 解决 | 处理、关闭 | |
| maintenance | 维修 | 维护、保养 | 「保养」是预防性的，语义不同 |
| operator | 操作员 | 操作工 | |
| technician | 维修人员 | 技术员、工程师 | |
| snapshot | 快照 | 截图、备份 | 指某一瞬间的数据副本 |
| report | 报告 / 报修 | 上报 | 名词用「报告」，动作可用「报修」 |
| record | 记录 | 纪录 | |
| verify | 验证 | 校验、核实 | |

---
