# Verification 代码审查状态收敛实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将代码审查状态收敛到“实际执行结果”，并防止把已提交实现因工作区干净而误判为“不适用”。

**Architecture:** `verification.md` 负责结构与唯一状态记录，`schema.yaml` 负责生成和 apply 指令，规格与工作流文档同步描述同一规则。所有位置统一使用“相对明确基线的完整 diff”，不以未提交工作区状态代替本次变更范围。

**Tech Stack:** Markdown、YAML、Git、ripgrep、Ruby 标准库 Psych

## Global Constraints

- 全部 OpenSpec 产物和说明使用简体中文。
- “实际执行结果”中的代码审查行是唯一权威状态。
- 工作区干净不能单独作为代码审查“不适用”的依据。
- 不改变 Critical、Important、Minor 的严重度定义和 archive 裁决条件。
- 未经用户明确要求，不创建 Git 提交。

---

### Task 1: 收敛模板状态并统一 diff 判据

**Files:**
- Modify: `openspec/schemas/evidence-driven/templates/verification.md:10-79`
- Modify: `openspec/schemas/evidence-driven/schema.yaml:195-219`
- Modify: `docs/ai-sdd-workflow.md:108-120`
- Modify: `docs/superpowers/specs/2026-08-14-verification-required-code-review-design.md:8-18`
- Modify: `spec/spec-architecture-openspec-workflow-refactor.md:198-206`

**Interfaces:**
- Consumes: `verification.md` 的规划与执行阶段结构。
- Produces: 一个权威代码审查状态，以及模板、schema、规格和工作流文档一致的“不适用”判据。

- [x] **Step 1: 运行状态唯一性检查并确认当前失败**

Run:

```bash
python3 -c 'from pathlib import Path; s=Path("openspec/schemas/evidence-driven/templates/verification.md").read_text(); count=s.count("| 代码审查 |"); assert count == 1, "代码审查状态/行数量不是 1：%s" % count'
```

Expected: 断言失败，报告当前共有 3 个 `| 代码审查 |` 行。

- [x] **Step 2: 运行旧判据检查并确认当前失败**

Run:

```bash
if rg -n "工作区相对本变更无实现 diff" openspec/schemas/evidence-driven docs/ai-sdd-workflow.md docs/superpowers/specs/2026-08-14-verification-required-code-review-design.md spec/spec-architecture-openspec-workflow-refactor.md; then exit 1; fi
```

Expected: 命中模板、schema、工作流和规格中的旧表述后以状态 1 退出。

- [x] **Step 3: 修改模板形成唯一权威状态**

在 `verification.md` 中：

- 删除“需求与验证对应关系”中的预置代码审查行。
- 将“不适用”规则改为仅当“本次变更相对明确基线或提交范围的完整 diff 为空”时允许，并明确工作区干净不足以证明无实现 diff。
- 将“审查范围”提示改为必须记录基线或提交范围。
- 把“代码审查 / 结论”状态表替换为结论摘要占位说明。
- 保留“实际执行结果”中的代码审查行作为唯一状态，并要求记录完整 diff 范围与结论摘要。

- [x] **Step 4: 同步 schema、规格与工作流文档**

在所有列出的同步文件中统一：

- 必须审查本次变更相对明确基线或提交范围的完整 diff。
- 只有该完整范围为空时才可标记“不适用”。
- 工作区干净或实现已经提交不能单独作为“不适用”依据。
- `spec/spec-architecture-openspec-workflow-refactor.md` 不再要求代码审查状态出现在需求对应关系中，改为由实际执行结果保存唯一状态。

- [x] **Step 5: 重新运行内容检查并确认通过**

Run:

```bash
python3 -c 'from pathlib import Path; s=Path("openspec/schemas/evidence-driven/templates/verification.md").read_text(); assert s.count("| 代码审查 |") == 1'
if rg -n "工作区相对本变更无实现 diff" openspec/schemas/evidence-driven docs/ai-sdd-workflow.md docs/superpowers/specs/2026-08-14-verification-required-code-review-design.md spec/spec-architecture-openspec-workflow-refactor.md; then exit 1; fi
rg -n "明确基线|提交范围|完整 diff" openspec/schemas/evidence-driven/templates/verification.md openspec/schemas/evidence-driven/schema.yaml docs/ai-sdd-workflow.md docs/superpowers/specs/2026-08-14-verification-required-code-review-design.md spec/spec-architecture-openspec-workflow-refactor.md
```

Expected: 前两项以状态 0 完成；最后一项在全部五个文件中找到新判据。

- [x] **Step 6: 验证 YAML 与变更范围**

Run:

```bash
ruby -e 'require "yaml"; YAML.load_file("openspec/schemas/evidence-driven/schema.yaml"); puts "YAML OK"'
git diff --check
git diff -- openspec/schemas/evidence-driven/templates/verification.md openspec/schemas/evidence-driven/schema.yaml docs/ai-sdd-workflow.md docs/superpowers/specs/2026-08-14-verification-required-code-review-design.md spec/spec-architecture-openspec-workflow-refactor.md
```

Expected: 输出 `YAML OK`；`git diff --check` 无输出且状态为 0；最终 diff 只包含设计批准的状态收敛和判据调整。
