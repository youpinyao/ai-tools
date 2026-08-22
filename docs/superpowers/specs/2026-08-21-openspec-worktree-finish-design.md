# OpenSpec 隔离 worktree 收尾设计

> **触发条件已被取代（2026-08-22）：** 「入口结束时必须询问」改为「禁止主动询问、仅按需执行」。见 [openspec-worktree-finish-no-ask-design.md](2026-08-22-openspec-worktree-finish-no-ask-design.md)。合并/清理安全步骤与收尾范围仍可参考本文；触发条件、询问菜单与验收中的「必须先问」以 2026-08-22 为准。

## 背景

`AI_TOOLS_PROPOSE_WORKTREE_V1` 已要求每次 propose 先询问是否使用隔离
worktree，并在选择隔离时新建独立 worktree。2026-08-18 设计将「不自动提交、
合并或删除 worktree 中的变更」列为非目标，因此隔离会话结束后没有收尾步骤。
用户需要在 worktree 跑完后被明确询问：是否把本次分支合并到主分支，以及是否
清理本次 worktree。

本设计修正该缺口，但不改为自动合并或自动删除。

## 目标

- 入口 Agent 准备结束回复时，若存在本次相关的隔离 worktree，必须先询问
  收尾，再结束回复。官方主体失败但本次 worktree 已创建时同样要问。
- 同时覆盖 propose、apply、verify、sync、archive 的 command 与 skill 入口。
- 用户确认后，才把本次 worktree 分支合并进主工作区当前分支，并删除本次
  worktree；有未提交改动时须先经用户明确同意提交。
- 只收尾本次相关路径，不得删除同目录其它 worktree 或父目录。
- 所有合并与删除命令锚定主工作区，不依赖 Shell 当前目录。
- OpenSpec 官方生成物升级后，可以检测收尾增强块状态并安全地重新注入。

## 非目标

- 不把官方 command/skill 纳入 Git 跟踪。
- 不修改 OpenSpec CLI 或 `evidence-driven` schema。
- 不自动替用户选择合并、清理、提交或保留。
- 不自动 stash、`git reset --hard`、`git worktree remove --force` 或
  `git branch -D`。
- 不改变 apply、verify、sync、archive 的既有 Verify 门禁语义。
- 不对长期手工 worktree，或仓库外且不是本会话创建的托管 worktree 收尾。

## 方案选择

采用与现有增强块相同的「向官方生成物追加版本化标记块」方案。新增独立标记
`AI_TOOLS_WORKTREE_FINISH_V1`，分别注入以下 10 个文件：

- `.cursor/commands/opsx-propose.md`
- `.cursor/skills/openspec-propose/SKILL.md`
- `.cursor/commands/opsx-apply.md`
- `.cursor/skills/openspec-apply-change/SKILL.md`
- `.cursor/commands/opsx-verify.md`
- `.cursor/skills/openspec-verify-change/SKILL.md`
- `.cursor/commands/opsx-sync.md`
- `.cursor/skills/openspec-sync-specs/SKILL.md`
- `.cursor/commands/opsx-archive.md`
- `.cursor/skills/openspec-archive-change/SKILL.md`

不并入 `AI_TOOLS_PROPOSE_WORKTREE_V1` 或 `AI_TOOLS_VERIFY_GATE_V1`，以免起始
选择、流转门禁与收尾三类规则互相抬高 `DUPLICATE` 计数，或把无关变更标成
`STALE`。

## 交互与执行流程

每个入口必须在准备结束回复时执行（官方主体成功、失败停止，或 worktree 已
创建但官方主体未开始）：

1. 若当前 Agent 是实施者、调查者或 apply/verify 阶段子 Agent，不得询问，不得
   合并或删除 worktree。
2. 一次性解析并冻结路径与分支；切换工作区后不得重算 `$FINISH_WORKTREE`。
   对 `git worktree list --porcelain` 每条路径 `pwd -P` 后全等匹配，记下
   `$FINISH_REMOVE_PATH`；不得用 list 原文做子串包含。
3. 只收尾本次相关对象：本会话 `$SESSION_WORKTREE`，或主工作区下
   `.worktrees/` / `.worktree/` / `worktrees/`（及项目约定父目录）中的当前
   路径。其它 linked worktree 跳过。D 节必须冻结 `$SESSION_WORKTREE`（
   `AI_TOOLS_PROPOSE_WORKTREE_SESSION_V1`），缺该标记的旧 D 块为 `STALE`。
4. 向用户展示本次路径、分支、主工作区、主分支（主工作区当前检出分支）以及
   是否有未提交改动。
5. 干净且分支具名时提供：合并并清理、仅清理、保留。脏时只提供「提交后合并
   并清理」与保留，不得提供仅清理。
6. `$WORKTREE_BRANCH` 或 `$TARGET_BRANCH` 为 `HEAD` / 空游离时不得提供合并。
7. 用户未明确选择时，不得提交、合并或删除。
8. 同一入口命令在本会话中只询问一次；apply 衔接 verify 时不得在 verify
   开始前询问。

## 合并与清理

用户选择合并并清理时：

1. 若选择「提交后合并」，先在 `$FINISH_WORKTREE` 展示 status，用户明确同意
   后才提交；拒绝则停止。提交后（含 hook 改动）仍脏则停止，不得合并或删除。
2. `$FINISH_WORKTREE` 与 `$MAIN_WORKTREE` 都必须干净。
3. 先把本会话工作区根目录切到主工作区；仅 shell `cd` 不算成功。
4. 使用 `git -C "$MAIN_WORKTREE" merge --no-edit "$WORKTREE_BRANCH"`。
5. 冲突、主工作区脏、游离 HEAD 或失败时保留 worktree，不得继续删除。
6. 断言 `$FINISH_WORKTREE != $MAIN_WORKTREE` 后，
   `git -C "$MAIN_WORKTREE" worktree remove "$FINISH_REMOVE_PATH"`（不得
   `--force`）。仅当 `$WORKTREE_BRANCH` 是具名分支时再
   `git -C "$MAIN_WORKTREE" branch -d`（不得 `-D`，不得对 `HEAD` 执行 `-d`）。

用户选择「仅清理」时：worktree 必须干净，同样先切回主工作区再用
`git -C` remove；游离 HEAD 只删目录，不删分支。

用户选择「保留」时：不提交、不合并、不切换、不删除。

## 状态检测与升级

接入文档新增与现有门禁同构的第三套状态检查，覆盖上述 10 个文件：

- `OK`：目标文件恰有一个当前版本收尾标记块。
- `MISSING`：目标文件存在但没有收尾标记块，可以追加。
- `DUPLICATE`：存在多个收尾标记块，必须先清理。
- `STALE`：存在收尾块但缺少
  `AI_TOOLS_WORKTREE_FINISH_ASK_ALWAYS_V1`、
  `AI_TOOLS_WORKTREE_FINISH_SCOPE_V1` 或
  `AI_TOOLS_WORKTREE_FINISH_MERGE_CLEANUP_V1`，必须整体替换。
- `NOFILE`：官方生成文件不存在，应先运行 `openspec init/update`。

`openspec update` 可能覆盖官方文件，因此日常升级必须重新检查这 10 个文件。
增强块正文由接入文档维护为单一权威文本。

## 错误处理与安全边界

- 不自动提交、stash 或丢弃未提交改动；提交必须用户明确同意。
- 不在未切回主工作区时删除当前 worktree。
- 合并、remove、删分支必须 `git -C "$MAIN_WORKTREE"`，不依赖 Shell cwd。
- 只删除本次 `$FINISH_WORKTREE` 及其对应分支；不得删除同目录下其它
  worktree，也不得删除 `.worktrees/`、`.worktree/`、`worktrees/` 等父目录。
- 合并冲突、任一侧脏工作区、游离 HEAD 或删除失败时停止并报告，保留现场。
- 子 Agent 与工作者不得向用户提问，也不得执行收尾。

## 验收

在临时目标项目中安装官方 Cursor 生成物并注入增强块，验证：

1. 10 个目标文件的收尾块均被识别为 `OK`，且各只有一个
   `AI_TOOLS_WORKTREE_FINISH_V1` 标记。
2. 在本次相关隔离 worktree 中结束 propose / apply / verify / sync / archive
   后都会先询问；官方主体失败但 worktree 已在时也询问。
3. 在主工作区且无会话 worktree 时不询问。长期手工 worktree 不询问。
4. 有未提交改动时先询问是否提交，未同意不得合并或删除。
5. 选择合并并清理时，用 `git -C "$MAIN_WORKTREE"` 先合并再删除本次路径。
6. 主工作区脏、游离 HEAD 或未切换成功时停止，worktree 仍在。
7. 实施者、调查者与阶段子 Agent 不询问。
8. apply 入口在衔接的 verify 结束前不询问。
9. 重复注入不会产生重复块；缺少内嵌标记的旧块为 `STALE` 并可整体替换。
10. 运行 `openspec update` 后重新注入，10 个文件恢复为 `OK`。
11. `.worktrees/` 下同时存在多个 worktree 时，清理只删除本次
    `$FINISH_REMOVE_PATH` 与具名 `$WORKTREE_BRANCH`，其它实例和父目录仍在。
12. `git worktree list` 路径经 `pwd -P` 后全等才算命中；提交后仍脏必须停止；
    `$WORKTREE_BRANCH` 为 `HEAD` 时不得 `branch -d`。
13. 缺少 `AI_TOOLS_PROPOSE_WORKTREE_SESSION_V1` 的旧 D 块为 `STALE`。
