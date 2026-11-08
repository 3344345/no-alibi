-- 启用外键约束
PRAGMA foreign_keys = ON;

-- 世界状态表 (唯一一行)
CREATE TABLE IF NOT EXISTS world_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    revision INTEGER DEFAULT 0,
    projection TEXT DEFAULT '{}'
);

-- 不可篡改的事件历史池
CREATE TABLE IF NOT EXISTS event_log (
    event_id TEXT PRIMARY KEY,
    command_id TEXT,
    sequence INTEGER,
    world_time TEXT,
    actor_id TEXT,
    event_type TEXT,
    payload TEXT,
    caused_by TEXT,
    rule_version TEXT,
    is_failure BOOLEAN
);

-- 消息与传播队列 (Outbox模式)
CREATE TABLE IF NOT EXISTS outbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payload TEXT
);

-- 初始化世界状态
INSERT OR IGNORE INTO world_state (id, revision, projection) 
VALUES (1, 0, '{"last_sequence": 1000, "entities": {"doc_17": {"status": "pending", "location": "office"}}}');