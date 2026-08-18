# OpenSpec propose worktree 选择设计

## 背景

本仓库坚持“官方生成层归 OpenSpec 官方管理”：目标项目中的
`.cursor/skills/openspec-propose/` 与 `.cursor/commands/opsx-propose.md`
由 `openspec init/update` 生成，本仓库不跟踪它们。现有接入流程已经通过带版本标记的
幂等追加块增强 apply、verify、sync、archive，因此 propose 的 worktree 选择也应采用
同一扩展方式，避免分叉官方文件。

当前 propose 会直接在所在工作区创建 change 及其制品。用户需要在每次 propose 开始时
明确选择是否隔离工作区，并要求该选择发生在任何 OpenSpec 文件写入之前。

## 目标

- 每次 `/opsx-propose` 或对应 `openspec-propose` skill 启动时都询问是否使用 worktree。
- 在创建 change、分配 change 名称或写入任何制品前完成选择和工作区准备。
- 同时覆盖 command 与 skill 入口，并保持两者语义一致。
- OpenSpec 官方生成物升级后，可以检测增强块状态并安全地重新注入。
- 避免创建嵌套 worktree，并让失败路径可见、可恢复。

## 非目标

- 不把官方 propose command/skill 纳入 Git 跟踪。
- 不修改 OpenSpec CLI 或 `evidence-driven` schema。
- 不自动替用户选择 worktree，也不根据工作区是否干净跳过询问。
- 不改变 apply、verify、sync、archive 的既有门禁语义。
- 不自动提交、合并或删除 worktree 中的变更。

## 方案选择

采用“向官方生成物追加版本化增强块”的方案。新增独立标记
`AI_TOOLS_PROPOSE_WORKTREE_V1`，分别注入：

- `.cursor/commands/opsx-propose.md`
- `.cursor/skills/openspec-propose/SKILL.md`

没有采用全局 Cursor rule，因为其作用范围过宽，难以保证只在 propose 的正确阶段触发。
也不跟踪官方生成物的本地分叉，因为这会增加升级冲突，并违反当前仓库的官方优先约定。

## 交互与执行流程

每个 propose 入口必须先执行以下前置流程，完成后才进入官方原有步骤：

1. 向用户提供两个明确选项：
   - `使用隔离 worktree`
   - `在当前工作区继续`
2. 无论工作区是否干净、是否已经处于 linked worktree，每次调用都必须询问。
3. 若选择当前工作区，保留当前目录和分支，继续官方 propose。
4. 若选择隔离 worktree：
   - 检测 `git rev-parse --git-dir` 与 `git rev-parse --git-common-dir`；
   - 同时检查 `git rev-parse --show-superproject-working-tree`，避免把 submodule
     误判为 linked worktree；
   - 若当前已处于 linked worktree，复用当前 worktree，不再嵌套创建；
   - 否则优先使用运行环境提供的原生 worktree 能力；没有原生能力时才使用
     `git worktree`；
   - 手工创建时遵循显式项目约定，其次复用 `.worktrees/` 或 `worktrees/`，
     都不存在时默认 `.worktrees/`；
   - 项目内 worktree 目录必须先确认被 Git 忽略；
   - 使用尚未占用的临时工作分支和路径。最终 change 名称仍由官方 propose 流程确定，
     不要求预先用 change 名称命名分支。
5. worktree 准备完成后，执行项目可识别的基础 setup 与基线检查，再继续官方 propose。
6. 用户取消选择、worktree 创建失败、setup 失败或基线检查失败时暂停并报告原因；
   不得静默退回当前工作区。

## 状态检测与升级

接入文档新增与现有门禁一致的状态检查：

- `OK`：目标文件恰有一个当前版本标记块。
- `MISSING`：目标文件存在但没有标记块，可以追加。
- `DUPLICATE`：存在多个标记块，必须先清理。
- `STALE`：存在旧版块但内容与当前 V1 定义不一致，必须整体替换。
- `NOFILE`：官方生成文件不存在，应先运行 `openspec init/update`。

`openspec update` 可能覆盖官方文件，因此日常升级流程必须重新检查这两个 propose 文件，
并处理所有非 `OK` 状态。增强块正文由接入文档维护为单一权威文本，command 与 skill
使用相同规则，仅根据文件上下文调整标题层级。

## 错误处理与安全边界

- 不在已识别的 linked worktree 中再次创建 worktree。
- 不在未被 Git 忽略的项目内目录创建 worktree。
- 不使用 `git reset --hard`、强制删除分支或其它破坏性清理命令。
- 不把未提交改动自动搬运到新 worktree；隔离 worktree 基于当前 `HEAD`。
- 当前工作区存在未提交改动时仍允许用户选择原地继续，但选择 worktree 后这些改动不会
  自动出现于新 worktree，应在询问说明中明确这一点。
- 所有阻塞都发生在 OpenSpec change 和制品创建前，避免半成品 change。

## 验收

在临时目标项目中安装官方 Cursor 生成物并注入增强块，验证：

1. command 与 skill 两个文件均被识别为 `OK`，且各只有一个标记块。
2. 每次 propose 都先询问，即使工作区干净或已经处于 worktree。
3. 选择当前工作区时，官方 propose 在原目录继续。
4. 选择 worktree 时，普通 checkout 会进入新 worktree 后再创建 change。
5. 已处于 linked worktree 时选择 worktree 会复用当前目录，不创建嵌套 worktree。
6. submodule 不会被误判为 linked worktree。
7. worktree 目录未被忽略、创建失败或基线检查失败时，流程在写入 change 前停止。
8. 重复运行注入流程不会产生重复块；模拟旧块时状态为 `STALE` 并可整体替换。
9. 运行 `openspec update` 后重新注入，两个文件恢复为 `OK`。

