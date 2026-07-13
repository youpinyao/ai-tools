# ai-tools

面向 Cursor IDE 的 AI 工具集，用于扩展 OpenSpec 规范驱动开发工作流。

## 简介

本仓库提供 Cursor 自定义 Skill 与 Command，帮助在实现代码与 OpenSpec 变更文档出现偏差时，以**代码和用户决策为唯一事实来源**，将变更文档与相关仓库文档同步回写。

这是 `openspec-apply-change` 的逆向流程，与 `openspec-sync-specs`（更新主规格）相互独立。

## 前置要求

- [Cursor IDE](https://cursor.com/)
- [OpenSpec CLI](https://github.com/openspec-dev/openspec)（Skill 依赖 `openspec` 命令行工具）

## 功能

### OpenSpec 从代码回写变更

| 类型 | 路径 | 说明 |
|------|------|------|
| Skill | `.cursor/skills/openspec-update-change-from-code/SKILL.md` | 定义完整工作流：选择变更、发现实现证据、对比漂移、确认策略、更新文档、校验报告 |
| Command | `.cursor/commands/opsx-update-change-from-code.md` | 快捷命令，触发上述 Skill |

**适用场景：**

- 实现代码已与 OpenSpec 变更文档不一致
- 需要将实现结果同步回 `proposal.md`、`design.md`、`tasks.md`、`specs/**` 等变更产物
- 需要更新与变更相关的仓库文档

**不适用场景：**

- 更新主规格（请使用 `openspec-sync-specs`）
- 实现新功能或重构业务逻辑
- 归档变更（请使用 `openspec-archive-change`）

## 使用方法

### 通过 Cursor Command

在 Cursor 聊天框中输入：

```text
/opsx-update-change-from-code
```

指定变更名称：

```text
/opsx-update-change-from-code add-auth
```

若未指定变更名，Agent 会尝试从对话、引用文件和 Git 变更中推断；若无法唯一确定，将提示你从活跃变更列表中选择。

### 工作流概览

1. **选择变更** — 使用显式名称或从仓库证据推断
2. **解析 schema 与编辑边界** — 通过 `openspec status --change "<name>" --json` 获取 `changeRoot`、`artifactPaths`、`actionContext`
3. **发现实现证据** — 收集 Git diff、代码、测试、配置、迁移脚本及相关文档
4. **构建行为漂移列表** — 对比文档意图与代码现实，区分简单漂移与复杂漂移
5. **确认策略** — 简单漂移自动更新；复杂漂移需用户确认
6. **精确更新** — 仅修改变更上下文允许的产物，保持原有结构与术语
7. **校验与报告** — 运行 `openspec validate "<name>" --type change --strict --json` 并输出摘要

## 项目结构

```text
ai-tools/
├── .cursor/
│   ├── commands/
│   │   └── opsx-update-change-from-code.md   # Cursor 快捷命令
│   └── skills/
│       └── openspec-update-change-from-code/
│           └── SKILL.md                       # Skill 工作流定义
└── README.md
```

## 安装

将本仓库克隆或复制到你的项目根目录，确保 `.cursor/` 目录位于项目根下，Cursor 会自动识别其中的 Skills 与 Commands。

```bash
git clone git@codeup.aliyun.com:5f2cb2f8df9df74e36afcb8c/ai-tools.git
```

若只需单个 Skill，也可将 `.cursor/skills/openspec-update-change-from-code/` 和 `.cursor/commands/opsx-update-change-from-code.md` 复制到目标项目的 `.cursor/` 目录中。

## 约束与注意事项

- 仅编辑 `changeRoot`、`artifactPaths` 和 `actionContext` 范围内的产物
- 不会通过此工作流写入主规格
- 已归档的变更不会静默编辑，需用户确认处理方式
- 生成的文件可作为契约读取，但不应手动编辑

## 许可证

Skill 采用 [MIT License](https://opensource.org/licenses/MIT)。
