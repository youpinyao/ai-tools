# verification 必做代码审查

date: 2026-08-14
status: approved

## 目标

在 `evidence-driven` 的 verification 阶段，把代码审查定为必做检查：规划写入 `verification.md`，apply 时实际阅读本次变更相对明确基线或提交范围的完整 diff 并记录结论。不恢复官方 archive 裁决，不新增 Cursor rule 或 wrapper skill。

## 行为

- 模板新增一级章节「代码审查」：审查范围、审查标准（正确性、可维护性、安全、边界与测试）、发现项、结论。
- 该检查的权威状态仅在「实际执行结果」中维护。
- 规划阶段状态为「待执行」，不得预填通过。
- apply 必须实际阅读 diff 后再改状态。
- 存在未处理的 Critical 或 Important → 结论为失败，并记入剩余风险。
- Minor 可记后续项，不单独导致失败。
- 「不适用」仅当本次变更相对明确基线或提交范围的完整 diff 为空，并写明原因。工作区干净或实现已提交不能单独作为依据；文档、schema 与配置变更仍须审查。
- 审查由当前 apply 会话执行；schema 不绑定独立 reviewer 或 Superpowers。

## 非目标

- 不恢复「代码审查（归档硬门禁）」章节名或 archive 拦截。
- 不恢复独立验证结论、自动派发 verify、finishing。
- 不修改官方 verify/archive/apply skill。
