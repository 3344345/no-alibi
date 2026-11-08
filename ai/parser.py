import uuid
from typing import Dict, Any, List
from contracts.command import Command, Attempt
from ai.provider import BaseLLMProvider

class IntentParser:
    """
    意图解析器。
    将玩家的自然语言输入，转换为结构化的 Command。
    """
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider

    def parse(self, player_input: str, actor_id: str, current_revision: int, world_time_str: str) -> Command:
        # 1. 如果是预设选项（这里假设预设选项以 choice_ 开头），直接本地映射，不消耗 AI
        if player_input.startswith("choice_"):
            attempts = self._map_preset_choice(player_input)
        else:
            # 2. 自由输入，调用大模型解析
            prompt = f"玩家说：'{player_input}'。请拆解为动作列表。"
            schema = {"attempts": [{"type": "str", "target_id": "str"}]}
            
            parsed_json = self.llm.generate_structured(prompt, schema)
            
            if "error" in parsed_json:
                # 离线或解析失败，生成一个无效动作
                attempts = [Attempt(attempt_id="err", type="invalid_input", target_id="none")]
            else:
                # 解析成功，转换为 Attempt 对象
                attempts = [
                    Attempt(attempt_id=str(uuid.uuid4()), type=a["type"], target_id=a.get("target_id", "none"))
                    for a in parsed_json.get("attempts", [])
                ]

        # 3. 封装为统一 Command
        return Command(
            command_id=str(uuid.uuid4()),
            source="player",
            actor_id=actor_id,
            expected_revision=current_revision,
            world_time=world_time_str, # 实际应解析为 datetime
            intent_text=player_input,
            attempts=attempts,
            is_high_risk_confirmed=False
        )

    def _map_preset_choice(self, choice_str: str) -> List[Attempt]:
        """本地硬编码映射预设选项"""
        if choice_str == "choice_defer":
            return [Attempt(attempt_id=str(uuid.uuid4()), type="defer_signature", target_id="doc_17")]
        return []