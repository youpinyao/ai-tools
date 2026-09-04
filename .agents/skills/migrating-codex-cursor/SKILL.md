---
name: migrating-codex-cursor
description: Use when a project must migrate from Cursor-only or Codex-only conventions to support both tools, especially when skills, rules, hooks, or configuration are duplicated or tool-specific, or Cursor commands must be removed.
license: MIT
metadata:
  author: youpinyao
  version: "1.0.0"
---

# 迁移 Codex 与 Cursor 项目配置

将项目改为同时兼容 Codex 和 Cursor。核心原则是：共享内容只有一个可编辑真源；Skill 统一放在 `.agents/skills/`，Cursor 不保留 command。

## 目标约束

- `.cursor/commands/` 下不得保留任何 command；迁移时删除整个目录或其中全部文件。
- command 与 skill 表达相同能力时，删除 command，只保留 `.agents/skills/<name>/` 中的一份 skill。
- 不得用 Cursor command 作为薄适配入口，也不得把 command 转存到其它 Cursor 专属目录。
- Cursor 与 Codex 均从 `.agents/skills/` 发现共享 skill；无法从该目录发现时标为冲突，不通过复制 skill 或保留 command 绕过。

## 硬门禁

流程固定分为“计划”和“执行”两阶段：

1. 先完成只读盘点并提交迁移计划。
2. 只有用户在看到该计划后明确同意执行，才能修改、移动、链接或删除文件。

用户在最初请求中说“直接迁移”“不用问”不等于批准尚未展示的具体计划。批准必须发生在计划之后。计划调整后若目标、删除项或风险发生实质变化，重新取得批准。

## 计划阶段

### 1. 只读盘点

读取项目指令与文档，并检查 Git 状态。查找但不要修改：

- 根目录及子目录的 `AGENTS.md`；
- `.agents/skills/`、`.cursor/skills/`、`.codex/skills/`；
- Cursor rules、commands、hooks、MCP 配置及 Codex 对应配置；其中 commands 全部列为删除候选；
- 引用这些路径的脚本、文档、忽略规则和 CI；
- 符号链接、生成标记、同名文件与未提交改动。

不要把工具名称相似当作兼容证据。根据项目已有文档、当前工具帮助或用户提供的约束确认发现路径和格式；无法确认时标为待验证，不以符号链接或复制猜测兼容性。

### 2. 建立能力清单

每项能力记录：用途、当前真源、Codex 入口、Cursor 入口、内容是否相同、目标真源、适配方式、验证方式。按下列规则分类：

- **直接共享**：两种工具都原生读取同一路径与格式。
- **薄适配**：共享正文只有一份，但某工具必须保留独立元数据；Cursor command 不属于允许的薄适配。
- **工具专属**：另一工具没有等价能力；保留并说明边界，不伪造兼容。
- **冲突/未知**：语义冲突、外部链接或支持情况未确认；执行前必须解决。

默认优先级：通用 Agent Skill 使用 `.agents/skills/<name>/`；跨工具项目规则使用 `AGENTS.md`；工具私有能力留在其原生目录，但 Cursor command 必须删除。实际探测结果高于默认值，唯独不得推翻“Cursor 不保留 command”的目标约束。

### 3. 输出迁移计划

计划必须按此顺序包含：

1. **目标布局**：每项能力的唯一真源和必要适配入口。
2. **变更清单**：逐项列出保留、合并、移动、新增和删除候选，并明确 `.cursor/commands/` 的删除范围。
3. **冲突与未知项**：需要用户决定或需要先验证的事项。
4. **安全与回滚**：未提交改动的保护方式，以及如何恢复每个移动或删除项。
5. **验证清单**：静态检查、工具发现检查、行为检查和重复内容检查。

计划结尾必须停止并请求明确批准，不得在同一轮开始执行。

## 执行阶段

获得批准后：

1. 重新检查 Git 状态；若批准后出现重叠改动，停止并报告。
2. 先建立并验证 `.agents/skills/` 共享真源，再更新引用和必要的非 command 薄适配入口。
3. 合并时保留更具体、仍有效的规则；语义无法判定时停止，不静默选边。
4. 未提交内容视为用户资产；不覆盖、不回滚、不顺手格式化无关文件。
5. 只有共享 skill 已验证等价后才处理旧产物；随后删除 `.cursor/commands/`，不得保留回退 command。删除必须与批准计划逐项一致；符号链接只操作链接本身，不跟随删除目标。
6. 不将“复制两份并提醒同步”当作最终兼容方案。若工具限制迫使生成副本，保留一个源模板、确定性生成方式和漂移检查，并在结果中明确例外。

## 验证与结果

执行所有适用检查：

- skill frontmatter、名称、引用路径和符号链接有效；
- `.cursor/commands/` 不存在或为空，且文档、脚本、CI 不再把 Cursor command 当作入口；
- Codex 与 Cursor 各自能发现预期规则、skill 或入口；
- 工具专属功能仍保留，薄适配入口指向同一语义真源；
- 不存在未声明的重复正文或旧引用；
- 项目测试、配置校验及 `git diff --check` 通过；
- 完整 diff 与批准计划一致，没有改动范围外文件。

结果按以下契约汇报：

```text
迁移结果：<完成 / 部分完成 / 阻塞>
唯一真源：<路径与用途>
薄适配层：<非 command 的路径、原因；无则写“无”>
验证：<命令或检查及真实结果>
保留项：<无法共享的工具专属能力>
未解决：<冲突、失败或待用户决定事项>
回滚：<恢复方法>
```

验证失败时如实报告“部分完成”或“阻塞”，不要把文件已移动等同于迁移完成。
