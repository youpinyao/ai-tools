# Verification 代码审查状态收敛设计

## 背景

`evidence-driven` 的 `verification.md` 模板将代码审查状态同时记录在需求映射、代码审查结论和实际执行结果三处，容易产生互相矛盾的状态。另外，当前“不适用”条件以工作区是否存在实现 diff 为依据，可能把已经提交但尚未审查的实现误判为无 diff。

## 目标

- 让“实际执行结果”成为代码审查状态的唯一权威来源。
- 保留审查范围、标准、发现项和结论摘要，避免丢失审查证据。
- 只有本次变更相对明确基线的完整 diff 为空时，代码审查才可标记为“不适用”。
- 明确工作区干净不能单独证明本次变更没有实现 diff。
- 保持模板、schema 指令和工作流文档的表述一致。

## 设计

### 唯一状态来源

从“需求与验证对应关系”中移除预置的代码审查行，因为代码审查属于必做验证检查，不是业务需求或场景。

“代码审查 / 结论”保留文字结论摘要，不再维护状态表。“实际执行结果”中的代码审查行作为唯一权威状态，记录实际审查的 diff 范围、结论摘要和证据。

### Diff 范围

审查范围必须说明本次变更使用的明确基线或提交范围，例如基线分支到当前提交、指定提交区间，或尚未提交的工作区 diff。

只有该完整范围为空时才允许标记为“不适用”。工作区干净、实现已经提交或当前没有未提交文件，都不能单独作为“不适用”的依据。

### 一致性调整

同步更新：

- `openspec/schemas/evidence-driven/templates/verification.md`
- `openspec/schemas/evidence-driven/schema.yaml`
- `docs/ai-sdd-workflow.md`
- `docs/superpowers/specs/2026-08-14-verification-required-code-review-design.md`

`docs/ai-tools-integration.md` 仅在其现有表述与新规则冲突时修改。

## 验证

- 全文检索并确认不再使用“工作区相对本变更无实现 diff”作为判据。
- 确认模板中代码审查只有一个状态字段。
- 检查 Markdown 表格结构和 YAML 语法。
- 执行仓库中已存在且适用于 schema 或文档的校验命令；若不存在，则记录人工检查结果。

## 非目标

- 不改变 Critical、Important、Minor 的严重度定义。
- 不新增自动解析 verification 状态的工具。
- 不改变官方 archive 裁决条件。
