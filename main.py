import os
import sqlite3
import json
from datetime import datetime, timedelta

from ai.provider import OfflineTemplateProvider # 以后换成真实 LLM 只需改这里
from ai.parser import IntentParser
from ai.narrator import Narrator
from api.gateway import CommandGateway
from contracts.command import Command, Attempt
from contracts.event import CommittedEvent

def init_database(db_path):
    """纯粹的数据库初始化"""
    if os.path.exists(db_path):
        os.remove(db_path)
    # 数据库建表由 Gateway 内部自动完成

def get_latest_events(conn, last_seen_seq, limit=5):
    """读取上次看到的序列号之后的所有新事件"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM event_log WHERE sequence > ? ORDER BY sequence ASC LIMIT ?", 
        (last_seen_seq, limit)
    )
    rows = cursor.fetchall()
    
    events = []
    for row in rows:
        events.append(CommittedEvent(
            event_id=row[0], command_id=row[1], sequence=row[2], world_time=row[3],
            actor_id=row[4], event_type=row[5], payload=json.loads(row[6]),
            caused_by=json.loads(row[7]), rule_version=row[8], is_failure=bool(row[9])
        ))
    return events

def main_game_loop():
    print("=======================================")
    print("  《在场证明》 No Alibi - 引擎 v2.0")
    print("=======================================")
    
    db_path = "no_alibi_save.db"
    init_database(db_path)

    # 1. 依赖注入 (Dependency Injection)
    # 以后不管你朋友用 GPT-6 还是本地大模型，只改这一行
    llm = OfflineTemplateProvider() 
    parser = IntentParser(llm)
    narrator = Narrator(llm)
    gateway = CommandGateway(db_path)
    
    # 2. 初始化状态追踪
    cursor = gateway.conn.cursor()
    cursor.execute("SELECT revision, projection FROM world_state WHERE id=1")
    row = cursor.fetchone()
    current_rev = row[0]
    projection = json.loads(row[1])
    
    game_time = datetime(1991, 3, 1, 9, 0, 0) # 设定游戏开局时间
    last_seen_seq = projection.get("last_sequence", 1000)

    print(f"\n[开局时间]: {game_time.strftime('%Y年%m月%d日')}")
    print("[身份]: 李达康，金山县县长")
    print("（输入 'time' 推进时间，输入 'quit' 退出，其他指令将进入解析器）\n")

    # 3. 核心循环
    while True:
        try:
            player_input = input(">>> ").strip()
            
            if not player_input:
                continue
            if player_input.lower() == 'quit':
                break
                
            # ---- 动作 A：时间推进 ----
            if player_input.lower() == 'time':
                game_time += timedelta(days=30) # 每次推进一个月
                print(f"\n[系统]: 时间流逝，来到 {game_time.strftime('%Y年%m月')}...")
                gateway.advance_time(game_time)
            
            # ---- 动作 B：玩家指令 ----
            else:
                # 这里为了兼容离线模板，暂时把输入当成预设选项（比如 choice_defer）
                command = parser.parse(player_input, actor_id="player", current_revision=current_rev, world_time_str=game_time.isoformat())
                success = gateway.submit_command(command.model_dump())
                if not success:
                    print("[系统]: 指令执行失败。")
            
            # ---- 统一获取新事件并渲染 ----
            new_events = get_latest_events(gateway.conn, last_seen_seq)
            if new_events:
                # 更新序列号标记
                last_seen_seq = new_events[-1].sequence
                
                # 更新世界版本号 (防止并发冲突)
                cursor.execute("SELECT revision FROM world_state WHERE id=1")
                current_rev = cursor.fetchone()[0]
                
                # 让 Narrator 渲染事件
                narrative = narrator.render(new_events)
                print("\n--- 游戏画面 ---")
                print(narrative)
                print("----------------\n")

        except KeyboardInterrupt:
            print("\n[系统]: 游戏已退出。")
            break
        except Exception as e:
            print(f"\n[系统错误]: {e}")

if __name__ == "__main__":
    main_game_loop()