# 协作指南 (Contributing Guide)

## 一、架构铁律（不可违反）
1. **单向数据流**：Command -> Resolver -> Committer -> EventLog。
2. **AI 无写库权限**：任何大模型生成的输出必须是 Proposal，不能直接修改 WorldFacts。
3. **业务逻辑隔离**：所有新机制（调查、人事、事件）必须在 `judgment/handlers/` 建立独立类，并在 `ACTION_HANDLERS` 注册，绝不允许在 `j6_orchestrator.py` 写 `if-else` 屎山。
4. **数据契约至上**：所有输入输出必须通过 `contracts/` 下的 Pydantic 模型校验。

## 二、目录职责划分
- `contracts/` & `storage/` & `judgment/`：**核心引擎（非常敏感，需架构师 Review 才能合入）**。
- `content/` & `data/`：**剧情数据（策划/写手负责，可随时丰富）**。
- `ai/`：**AI 接口层（仅限替换 LLM API 和调整 Prompt）**。

## 三、协作流程
1. 提交前跑通 `python main.py`。
2. 不准把本地生成的 `*.db` 和 `.env` 推送到远端。
3. 严格使用 Pydantic 进行类型约束。
