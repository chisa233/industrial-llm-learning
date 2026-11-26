-- Q1: 机台型号核验
SELECT machine_id, name, workshop, controller_model, drive_model, comm_card_model, servo_model, status
FROM machines
WHERE machine_id = 'CNC-A01';

-- Q2: 同码异机过滤
SELECT a.alarm_id, a.machine_id, m.drive_model, m.comm_card_model, a.alarm_code, a.occurred_at, a.param_snapshot_json
FROM alarm_events AS a
JOIN machines AS m ON a.machine_id = m.machine_id
WHERE a.alarm_code = 'Err16'
ORDER BY a.occurred_at DESC;

-- Q3: JOIN 历史工单排查未复测记录
SELECT r.record_id, r.machine_id, m.controller_model, m.drive_model, a.alarm_code, r.reported_at, r.operator_claim, r.technician_note, r.verify_status
FROM maintenance_records AS r
JOIN machines AS m ON r.machine_id = m.machine_id
LEFT JOIN alarm_events AS a ON r.related_alarm_id = a.alarm_id
WHERE r.verify_status != '已复测通过'
ORDER BY r.reported_at DESC;

-- Q4: GROUP BY 高频报警统计
SELECT alarm_code, alarm_source,
       COUNT(*) AS total_count,
       SUM(CASE WHEN is_resolved = 0 THEN 1 ELSE 0 END) AS unresolved_count
FROM alarm_events
GROUP BY alarm_code, alarm_source
ORDER BY total_count DESC, unresolved_count DESC;

-- Q5: 各机台未解决报警汇总
SELECT m.workshop, m.machine_id, m.name, m.status,
       COUNT(a.alarm_id) AS open_alarm_count
FROM machines AS m
LEFT JOIN alarm_events AS a
  ON m.machine_id = a.machine_id AND a.is_resolved = 0
GROUP BY m.workshop, m.machine_id, m.name, m.status
ORDER BY open_alarm_count DESC, m.machine_id;