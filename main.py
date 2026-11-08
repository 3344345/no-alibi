import sqlite3
import json
from ai.provider import OfflineTemplateProvider
from ai.parser import IntentParser
from ai.narrator import Narrator
from api.gateway import CommandGateway

def init_db(db_path):
    with sqlite3.connect(db_path) as conn:
        with open("storage/schema.sql", "r", encoding="utf-8") as f:
            conn.executescript(f.read())

def run_demo():
    print("=== 《在场证明》 引擎测试 ===")
    db_path = "no_alibi_demo.db"
    init_db(db_path)

    # 1. 组装系统 (AI 可插拔)
    llm = OfflineTemplateProvider() 
    parser = IntentParser(llm)
    narrator = Narrator(llm)
    
    # 2. 启动网关
    gateway = CommandGateway(db_path)
    
    # 获取当前版本号 (模拟前端状态)
    cursor = gateway.conn.cursor()
    cursor.execute("SELECT revision FROM world_state WHERE id=1")
    current_rev = cursor.fetchone()[0]

    # 3. 模拟玩家输入
    player_text = "我暂缓签字，并且今晚约老周吃饭。"
    print(f"\n[玩家输入]: {player_text}")
    
    # 解析成 Command
    command = parser.parse(player_text, actor_id="player", current_revision=current_rev, world_time_str="2028-04-03T10:00:00")
    
    # 4. 提交给 Gateway 进行校验与提交
    print("\n[系统正在处理...]")
    success = gateway.submit_command(command.model_dump())

    if not success:
        print("指令被系统拒绝。")
        return

    # 5. 提取刚刚发生的事件给 Narrator 渲染
    cursor.execute("SELECT * FROM event_log ORDER BY sequence DESC LIMIT 2")
    rows = cursor.fetchall()
    
    from contracts.event import CommittedEvent
    events = []
    for row in rows:
        events.append(CommittedEvent(
            event_id=row[0], command_id=row[1], sequence=row[2], world_time=row[3],
            actor_id=row[4], event_type=row[5], payload=json.loads(row[6]),
            caused_by=json.loads(row[7]), rule_version=row[8], is_failure=row[9]
        ))

    # 6. 生成叙事给玩家看
    story = narrator.render(events)
    print("\n=== 游戏画面 ===")
    print(story)
    
    # 验证版本冲突机制
    print("\n=== 测试重复提交(并发攻击) ===")
    # 用旧的版本号 current_rev 再次提交同一个命令
    attack_command = command.model_copy()
    import uuid
    attack_command.command_id = str(uuid.uuid4()) # 假装是一个新请求
    attack_command.expected_revision = current_rev # 但版本号没更新
    gateway.submit_command(attack_command.model_dump())

if __name__ == "__main__":
    run_demo()