---
name: integrating-ai-tools
description: Guides ai-tools integration into new, official OpenSpec, or legacy ai-tools projects. Use when installing, migrating, upgrading, validating, or troubleshooting ai-tools and evidence-driven OpenSpec in a target repository.
compatibility: Requires Node.js, npm, OpenSpec CLI, Python 3.8+, and shell access.
---

# 接入 ai-tools

将本仓库的 `evidence-driven` 扩展安全接入其它业务仓库。OpenSpec 官方生成层继续由 OpenSpec CLI 管理，ai-tools 只叠加本仓库维护的自定义层。

## 开始前

1. 全程使用简体中文沟通并记录 OpenSpec 制品与结论。
2. 完整读取 [ai-tools 接入指南](reference.md)，以该文档作为步骤、注入块和验收命令的唯一事实源。
3. 明确 `AI_TOOLS_DIR` 与 `TARGET_PROJECT` 的绝对路径，确认当前目录究竟是本仓库还是目标项目。
4. 检查目标项目现状，按文档选择且只选择一条路径：全新接入、已有官方 OpenSpec 叠加，或旧版 ai-tools 迁移。
5. 查询执行时的 OpenSpec 稳定版本并固定精确版本；不要把文档中的历史版本当作永久最新版本。

## 执行约束

- 不在 ai-tools 仓库根目录运行 `openspec init` 或 `openspec update`。
- OpenSpec 只初始化 `codex` 工具，Cursor 与 Codex 共用 `.agents/skills/openspec-*`；不得初始化或保留重复的 Cursor commands/skills。
- 已有 `openspec/config.yaml` 时只合并 `schema` 字段，保留其它配置。
- 已有 `AGENTS.md` 时只合并或替换 `AI_TOOLS_OPENSPEC_CHINESE_V1` 标记块，不整文件覆盖。
- 把 `.agents/skills/` 作为 Cursor 与 Codex 共用的唯一 OpenSpec Skill 源，包括官方 skills 与 from-code Skill。
- 替换验证门禁时，同步更新 V2 指纹脚本和所有规定的注入目标；不得只改其中一处。
- 保留目标项目中与本次接入无关的修改。遇到无法安全合并的已有定制时先停止并说明冲突。
- 不自动提交、归档 active change、合并或清理 worktree，除非用户明确要求。

## 完成条件

逐项执行接入指南的验收清单，至少确认：CLI 版本、`evidence-driven` schema、目标项目配置、官方生成层、自定义层、验证门禁、指纹脚本和冒烟 change 均符合预期。报告采用“所选路径、安装或修改、验证结果、保留项、阻塞或剩余风险”的结构，不把未执行的检查写成成功。
