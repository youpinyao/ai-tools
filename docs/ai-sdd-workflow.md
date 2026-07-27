# OpenSpec 验证工作流

## 目标

`evidence-driven` 以 OpenSpec 内置 `spec-driven` schema 为基线，只增加
`verification` 环节。Proposal、Specs、Design 和 Tasks 的定义、模板及依赖关系
保持与原始 schema 一致。

## 工作流

```text
proposal
  → specs
  → design
  → tasks
  → verification
  → apply
  → independent verify
  → archive
```

与原始 `spec-driven` 相比，仅有以下差异：

- Tasks 完成后生成 `verification.md`。
- Apply 以 `verification` artifact 就绪为前提。
- 实现 Agent 按 `verification.md` 执行检查并记录真实证据。
- 独立 Agent 在新会话中运行 `/opsx:verify`，填写独立验证结论。
- `/opsx:archive` 在验证未通过时阻止归档。

## 原始产物

以下产物直接沿用 OpenSpec `spec-driven` 的 instruction 和 template：

- `proposal.md`
- `specs/<capability>/spec.md`
- `design.md`
- `tasks.md`

本 schema 不额外规定风险分级、前后端拆分方式、技术栈、任务粒度或项目治理规则。

## Verification

`verification.md` 同时用于：

1. 规划实现前需要执行的自动化与人工检查。
2. 记录实现后的实际命令、结果、跳过原因和剩余风险。
3. 保存独立 Agent 的最终验证结论。

规划阶段不得填写未经执行的成功结果。实现 Agent 不得填写“独立验证结论”。

## 命令

- `/opsx:propose`：按 schema 顺序生成全部产物，包括 `verification.md`。
- `/opsx:apply`：实施 tasks，并记录 verification 证据。
- `/opsx:verify`：由未参与实现的 Agent 独立复验。
- `/opsx:archive`：验证通过后归档。

## 校验

```bash
openspec schema validate evidence-driven
openspec status
```
