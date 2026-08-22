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
- 选择隔离 worktree 时，每次 propose 都必须新建独立 worktree，不得复用已有目录。
- 进入官方 propose 前，本会话工作区根目录必须已切到新 worktree。
- 避免在当前 worktree 内部创建嵌套 worktree，并让失败路径可见、可恢复。

## 非目标

- 不把官方 propose command/skill 纳入 Git 跟踪。
- 不修改 OpenSpec CLI 或 `evidence-driven` schema。
- 不自动替用户选择 worktree，也不根据工作区是否干净跳过询问。
- 不改变 apply、verify、sync、archive 的既有门禁语义。
- 不自动提交、合并或删除 worktree 中的变更。2026-08-22 起，各入口结束时
  不得主动询问收尾；仅在用户明确要求后合并或删除，见
  [禁止主动收尾询问设计](2026-08-22-openspec-worktree-finish-no-ask-design.md)。

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
   - 无论普通 checkout、submodule 还是已处于 linked worktree，都必须新建
     独立 worktree（新路径 + 新分支），不得复用当前目录或任一已有 worktree；
   - 新建路径必须是绝对路径，且不得位于当前 worktree 目录内部；
   - 优先使用运行环境提供的原生 worktree 能力。原生能力只需新建、不复用、
     不嵌套，可以落在仓库外；不满足时回退手工 `git worktree`，不得因此停止；
   - 手工创建时锚定主工作区并用绝对路径：遵循显式项目约定，其次使用主工作区
     下已有 `.worktrees/` 或 `worktrees/`，都不存在时默认 `.worktrees/`；
   - 项目内 worktree 目录必须先用 `git -C "$MAIN_WORKTREE" check-ignore` 确认
     被 Git 忽略；
   - 使用尚未占用的临时工作分支和绝对路径。最终 change 名称仍由官方 propose
     流程确定，不要求预先用 change 名称命名分支；
   - 创建后必须把本会话工作区根目录切到新 worktree；仅 shell `cd` 不算成功。
5. 确认工作区根已切换后，执行项目可识别的基础 setup 与基线检查，再继续官方
   propose。
6. 用户取消选择、worktree 创建失败、会话工作区未切换、setup 失败或基线检查
   失败时暂停并报告原因；不得静默退回当前工作区。

## 状态检测与升级

接入文档新增与现有门禁一致的状态检查：

- `OK`：目标文件恰有一个当前版本标记块。
- `MISSING`：目标文件存在但没有标记块，可以追加。
- `DUPLICATE`：存在多个标记块，必须先清理。
- `STALE`：存在旧版块但内容与当前 V1 定义不一致（含仍使用
  `AI_TOOLS_PROPOSE_WORKTREE_REUSE_V1`，或缺少
  `AI_TOOLS_PROPOSE_WORKTREE_INDEPENDENT_V1` /
  `AI_TOOLS_PROPOSE_WORKTREE_WORKSPACE_ROOT_V1` 的块），必须整体替换。
- `NOFILE`：官方生成文件不存在，应先运行 `openspec init/update`。

`openspec update` 可能覆盖官方文件，因此日常升级流程必须重新检查这两个 propose 文件，
并处理所有非 `OK` 状态。增强块正文由接入文档维护为单一权威文本，command 与 skill
使用相同规则，仅根据文件上下文调整标题层级。

## 错误处理与安全边界

- 不在当前 worktree 目录内部创建嵌套 worktree；已处于 linked worktree 时
  仍须新建独立 worktree。手工创建锚定主工作区父目录；原生创建可以在仓库外。
- 不在未被 Git 忽略的项目内目录用手工 `git worktree` 创建 worktree。
- 不使用 `git reset --hard`、强制删除分支或其它破坏性清理命令。
- 不把未提交改动自动搬运到新 worktree；隔离 worktree 默认基于当前 `HEAD`，
  工作区独立不等于 Git 历史独立。
- 仅 shell `cd` 而会话工作区根仍指向旧目录时，不得继续 propose。
- 当前工作区存在未提交改动时仍允许用户选择原地继续，但选择 worktree 后这些改动不会
  自动出现于新 worktree，应在询问说明中明确这一点。
- 所有阻塞都发生在 OpenSpec change 和制品创建前，避免半成品 change。

## 验收

在临时目标项目中安装官方 Cursor 生成物并注入增强块，验证：

1. command 与 skill 两个文件均被识别为 `OK`，且各只有一个标记块。
2. 每次 propose 都先询问，即使工作区干净或已经处于 worktree。
3. 选择当前工作区时，官方 propose 在原目录继续。
4. 选择 worktree 时，普通 checkout 会进入新 worktree 后再创建 change。
5. 已处于 linked worktree 时选择 worktree 会新建独立 worktree，不复用当前目录，
   也不创建嵌套 worktree；手工路径为锚定主工作区的绝对路径。
6. submodule 不会被误判为 linked worktree。
7. worktree 目录未被忽略、创建失败、会话工作区未切换或基线检查失败时，流程在
   写入 change 前停止。
8. 重复运行注入流程不会产生重复块；完整旧版复用块与缺少
   `AI_TOOLS_PROPOSE_WORKTREE_WORKSPACE_ROOT_V1` 的块均为 `STALE` 并可整体替换。
9. 运行 `openspec update` 后重新注入，两个文件恢复为 `OK`。
10. 原生 worktree 建在仓库外且不嵌套时可以接受；仅 shell `cd` 不得视为已进入。
