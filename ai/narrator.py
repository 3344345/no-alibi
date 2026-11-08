from typing import List
from contracts.event import CommittedEvent
from ai.provider import BaseLLMProvider

class Narrator:
    """
    叙事渲染器。
    读取 Committer 已经写入的历史事实，生成给玩家看的文本。
    """
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider

    def render(self, events: List[CommittedEvent]) -> str:
        if not events:
            return "一切如常。"

        # 构造给 AI 的上下文（只给玩家能感知到的事件）
        context_prompt = "你是一个官场小说的叙述者。请用克制、压抑的笔触，将以下发生的事实渲染成场景文本：\n"
        for e in events:
            context_prompt += f"- 事实：{e.actor_id} 执行了 {e.event_type}，结果：{'成功' if not e.is_failure else '失败'}\n"
        
        context_prompt += "注意：绝对不要添加任何未提及的设定或历史，只做环境与动作描写。"

        # 调用 AI 渲染
        narrative = self.llm.generate_text(context_prompt)
        return narrative