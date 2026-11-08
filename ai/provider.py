from abc import ABC, abstractmethod
from typing import Dict, Any, List
import json

class BaseLLMProvider(ABC):
    """所有 AI 提供商（云端、本地、离线模板）必须实现的接口"""
    
    @abstractmethod
    def generate_structured(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """用于 Parser，输出结构化 JSON"""
        pass

    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        """用于 Narrator，输出自然语言"""
        pass


class CloudLLMProvider(BaseLLMProvider):
    """云端 API 实现（如 OpenAI / 智谱 / DeepSeek）"""
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        # 这里省略具体的 client 初始化（如 OpenAI SDK）

    def generate_structured(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        # 实际调用大模型，并强制 JSON 输出
        # 此处在真实开发中替换为 API 调用
        print(f"[Cloud AI] 正在解析意图...")
        return {} # 模拟返回

    def generate_text(self, prompt: str) -> str:
        # 实际调用大模型生成文本
        print(f"[Cloud AI] 正在渲染叙事...")
        return "【云端AI生成】" + "这是一段根据你刚才行为生成的官场剧情。"


class OfflineTemplateProvider(BaseLLMProvider):
    """离线模板实现（断网时兜底）"""
    def __init__(self, template_path: str = "content/text_templates.yaml"):
        self.template_path = template_path
        # 实际开发中在这里加载 YAML 模板字典

    def generate_structured(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        # 离线时不解析长文本，仅返回默认的“无效动作”
        print(f"[Offline AI] 仅支持预设选项，无法解析自由输入。")
        return {"error": "Offline mode only supports preset choices."}

    def generate_text(self, prompt: str) -> str:
        # 基于事件类型的本地模板兜底
        print(f"[Offline AI] 正在使用本地模板渲染...")
        return "【本地模板】你环顾四周，目前的情况让你感到一阵不安。"