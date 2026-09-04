---
name: integrating-graphify
description: Guides Graphify integration, updates, team setup, privacy controls, validation, and removal. Use when adding Graphify to a Cursor, Codex, ai-tools, or OpenSpec project, or when troubleshooting a stale or conflicted graph.
compatibility: Requires Python 3.10+, uv or pipx, Graphify CLI, and shell access.
---

# 接入 Graphify

把 Graphify 作为 AI-SDD / OpenSpec 的可选上下文增强层。图谱用于缩小调查范围，源码、规范和真实验证结果仍是事实依据。

## 开始前

1. 完整读取 [Graphify 接入方案](reference.md)，以该文档作为安装、协作、安全、移除和验收步骤的唯一事实源。
2. 确认目标项目、使用的平台（Cursor、Codex 或两者）、是否团队共享图谱，以及仓库对外部模型处理文档或媒体的限制。
3. 检查 Python、`uv` / `pipx`、`graphify` 命令和目标项目现有的 Graphify 文件；不要假定尚未安装。

## 执行约束

- 不覆盖或删除 ai-tools 的 `AGENTS.md` 中文标记块和 `.agents/skills/openspec-update-change-from-code/`。
- 敏感仓库默认收紧提取范围：维护 `.graphifyignore`，优先 `--code-only` 或明确的本地模型后端。
- 将 `.env`、密钥、证书、客户数据和导出数据排除在图谱之外。
- 图谱查询只提供调查线索；涉及实现、架构或验证结论时回读源码、OpenSpec 制品和测试。
- 团队共享图谱时，区分提交前的手动 `graphify update .` 与异步 hook；不得声称 post-commit hook 会修改刚创建的提交。
- 图谱异常减少时先查提取错误，不默认用 `--allow-partial` 覆盖完整图谱。
- Graphify 状态默认不构成 OpenSpec 归档门禁，除非目标项目另有明确规则。

## 完成条件

按接入方案的验收清单检查平台集成文件、忽略规则、Git hook / merge driver（若适用）、`graphify-out/` 核心产物和代表性查询。报告安装范围、隐私选择、生成产物、查询验证和未启用的可选能力。
