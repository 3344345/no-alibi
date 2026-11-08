import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, Any
from contracts.command import Command
from contracts.errors import ConcurrencyError
from judgment.j6_orchestrator import ActionOrchestrator
from storage.committer import Committer

class CommandGateway:
    """
    统一命令网关。
    所有玩家、NPC和系统的动作都必须从这里进入。
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.committer = Committer(self.conn)
        
        # 初始化一个最简单的世界状态表（如果不存在的话）
        self._init_db()

    def _init_db(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS world_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    revision INTEGER DEFAULT 0,
                    projection TEXT DEFAULT '{}'
                )
            """)
            self.conn.execute("""
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
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS outbox (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payload TEXT
                )
            """)
            # 插入初始状态
            self.conn.execute("INSERT OR IGNORE INTO world_state (id, revision, projection) VALUES (1, 0, '{\"last_sequence\": 1000}')")

    def submit_command(self, raw_command_json: Dict[str, Any]) -> bool:
        """
        接收原始 JSON 命令，并处理完整生命周期。
        """
        try:
            command = Command(**raw_command_json)
        except Exception as e:
            print(f"[Gateway] 命令格式校验失败: {e}")
            return False

        # 1. 获取当前世界快照 (World Snapshot)
        cursor = self.conn.cursor()
        cursor.execute("SELECT projection, revision FROM world_state WHERE id = 1")
        row = cursor.fetchone()
        
        if not row:
            return False
            
        projection = json.loads(row[0])
        
        # 将当前 Actor 注入快照，方便硬约束读取
        projection["current_command_actor"] = command.actor_id
        
        # 2. 编排裁定 (J6)
        # 使用 command_id 作为种子的一部分，确保重试不会产生不同结果
        seed = f"{command.command_id}_{row[1]}"
        
        resolution = ActionOrchestrator.process(command, projection, seed)
        
        # 3. 提交给 Committer (事务写入)
        success = self.committer.commit(resolution, expected_revision=command.expected_revision)
        
        if success:
            print(f"[Gateway] 命令 {command.command_id} 处理成功。生成事件 {len(resolution.generated_events)} 个。")
            return True
        else:
            print(f"[Gateway] 命令 {command.command_id} 提交失败（可能版本冲突）。")
            return False