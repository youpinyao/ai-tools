# verification 必做代码审查实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `evidence-driven` 的 verification 把代码审查列为必做检查，并同步规格与文档。

**Architecture:** 只改自定义 schema 的 instruction 与 `verification.md` 模板，以及说明该语义的规格/文档。不改官方 skills/commands，不引入归档裁决。

**Tech Stack:** OpenSpec schema YAML、Markdown。

## Global Constraints

- 简体中文；专有名词与路径可保留原文。
- 模板与 `schema.yaml` 不得出现 `归档硬门禁`、`独立验证结论`、`Superpowers`、`Task 派发`、`Finishing`。
- 未获用户明确要求时不得 git commit。

---

## 文件地图

- Modify: `openspec/schemas/evidence-driven/schema.yaml`
- Modify: `openspec/schemas/evidence-driven/templates/verification.md`
- Modify: `spec/spec-architecture-openspec-workflow-refactor.md`
- Modify: `README.md`
- Modify: `docs/ai-sdd-workflow.md`
- Modify: `docs/ai-tools-integration.md`

### Task 1: Schema 与模板

**Files:**
- Modify: `openspec/schemas/evidence-driven/schema.yaml`
- Modify: `openspec/schemas/evidence-driven/templates/verification.md`

- [x] **Step 1: 更新 verification 与 apply instruction**
- [x] **Step 2: 扩展 verification 模板**
- [x] **Step 3: 校验 schema**

### Task 2: 规格与文档

**Files:**
- Modify: `spec/spec-architecture-openspec-workflow-refactor.md`
- Modify: `README.md`
- Modify: `docs/ai-sdd-workflow.md`
- Modify: `docs/ai-tools-integration.md`

- [x] **Step 1: 更新架构规格 4.2/4.4/4.5 与 AC-VER**
- [x] **Step 2: 更新 README 与两份工作流文档**
- [x] **Step 3: 静态检查**

确认模板含 `## 代码审查`；schema 与模板不含禁止短语；`openspec schema validate evidence-driven` 通过。
