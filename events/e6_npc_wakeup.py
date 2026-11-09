import uuid
from typing import List, Dict, Any
from domain.actor import Actor
from contracts.command import Command, Attempt
from datetime import datetime

class NPCWakeupEngine:
    """
    NPC 唤醒引擎 (E6)。
    读取 NPC 的认知、目标和触发条件，生成他们主动行动的 Command。
    """
    
    @classmethod
    def evaluate_npcs(cls, world_state: Dict[str, Any], current_time: datetime) -> List[Command]:
        commands = []
        actors = world_state.get("actors", {})
        
        for actor_id, data in actors.items():
            if actor_id == "player" or data.get("status") == "inactive":
                continue
                
            # 1. 检查唤醒条件（例如：NPC 处于恐慌状态，或者玩家很久没理他）
            if data.get("mental_state") == "terrified":
                # 生成一个“主动找玩家求救/试探”的动作
                cmd = Command(
                    command_id=str(uuid.uuid4()),
                    source="npc",
                    actor_id=actor_id,
                    expected_revision=world_state.get("revision", 0),
                    world_time=current_time,
                    intent_text="NPC 恐慌，主动找玩家试探",
                    attempts=[Attempt(
                        attempt_id=str(uuid.uuid4()),
                        type="request_meeting",
                        target_id="player"
                    )]
                )
                commands.append(cmd)
                
            # 2. 检查承诺到期等业务逻辑...
            
        return commands