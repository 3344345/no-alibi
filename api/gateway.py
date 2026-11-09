import sqlite3
import json
from datetime import datetime
from typing import Dict, Any

from contracts.command import Command
from judgment.j6_orchestrator import ActionOrchestrator
from storage.committer import Committer
from events.e5_scheduler import Scheduler
from events.e6_npc_wakeup import NPCWakeupEngine

class CommandGateway:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.committer = Committer(self.conn)

    def submit_command(self, raw_command_json: Dict[str, Any]) -> bool:
        try:
            command = Command(**raw_command_json)
        except Exception:
            return False

        cursor = self.conn.cursor()
        cursor.execute("SELECT projection, revision FROM world_state WHERE id = 1")
        row = cursor.fetchone()
        if not row: return False
            
        projection = json.loads(row[0])
        projection["current_command_actor"] = command.actor_id
        
        # 交由编排器
        resolution = ActionOrchestrator.process(command, projection, f"{command.command_id}_{row[1]}")
        
        # 交由事务锁提交
        return self.committer.commit(resolution, expected_revision=command.expected_revision)

    def advance_time(self, current_time: datetime):
        cursor = self.conn.cursor()
        cursor.execute("SELECT projection FROM world_state WHERE id = 1")
        projection = json.loads(cursor.fetchone()[0])
        
        commands = Scheduler.tick(current_time, projection) + NPCWakeupEngine.evaluate_npcs(projection, current_time)
        
        for cmd in commands:
            cursor.execute("SELECT revision FROM world_state WHERE id = 1")
            cmd.expected_revision = cursor.fetchone()[0]
            self.submit_command(cmd.model_dump())