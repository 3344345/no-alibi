import sqlite3
import json
from contracts.resolution import Resolution
from contracts.errors import ConcurrencyError

class Committer:
    """
    唯一持久化写入者。
    以原子化事务提交事件、状态变更和待传播消息。
    """
    def __init__(self, db_conn: sqlite3.Connection):
        self.conn = db_conn
        # 启用外键约束和 WAL 模式，保证并发读写安全
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.conn.execute("PRAGMA journal_mode=WAL;")

    def commit(self, resolution: Resolution, expected_revision: int) -> bool:
        """
        核心事务方法。
        返回 True 表示成功，抛出异常或返回 False 表示全量回滚。
        """
        try:
            # 使用 with 语句自动处理 BEGIN 和 COMMIT/ROLLBACK
            with self.conn:
                cursor = self.conn.cursor()
                
                # 1. 校验乐观锁（防止同一命令重复提交，或并发冲突）
                cursor.execute("SELECT revision FROM world_state WHERE id = 1")
                row = cursor.fetchone()
                if not row or row[0] != expected_revision:
                    raise ConcurrencyError(f"世界版本冲突！当前版本 {row[0] if row else 'None'}，期望版本 {expected_revision}")

                # 2. 写入 CommittedEvent (不可篡改的历史事实)
                for event in resolution.generated_events:
                    cursor.execute(
                        """
                        INSERT INTO event_log 
                        (event_id, command_id, sequence, world_time, actor_id, event_type, payload, caused_by, rule_version, is_failure) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            event.event_id, event.command_id, event.sequence, 
                            event.world_time.isoformat(), event.actor_id, event.event_type, 
                            json.dumps(event.payload), json.dumps(event.caused_by), 
                            event.rule_version, event.is_failure
                        )
                    )

                # 3. 更新状态投影 (Projections)
                if resolution.state_changes:
                    # 这里使用 JSON Patch 逻辑更新整个世界的状态
                    # 实际开发中可能拆分成不同的表（项目表、人物表等）
                    cursor.execute(
                        "UPDATE world_state SET projection = json_patch(projection, ?) WHERE id = 1",
                        (json.dumps(resolution.state_changes),)
                    )

                # 4. 写入待传播消息队列 (Outbox 模式)
                for obs in resolution.pending_observations:
                    cursor.execute(
                        "INSERT INTO outbox (payload) VALUES (?)",
                        (json.dumps(obs),)
                    )

                # 5. 递增世界版本号，产生新的 revision
                cursor.execute("UPDATE world_state SET revision = revision + 1 WHERE id = 1")
                
            # with 块结束如果没有异常，自动 COMMIT
            return True
            
        except Exception as e:
            # 如果发生任何异常（包括乐观锁、数据库错误），with 块自动 ROLLBACK
            print(f"[Committer] 事务提交失败并已全量回滚: {e}")
            # 在实际应用中，这里应该抛出异常给 API Gateway 处理
            return False