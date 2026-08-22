# OpenSpec 隔离 worktree 禁止主动收尾询问设计

## 背景

[2026-08-21 隔离 worktree 收尾设计](2026-08-21-openspec-worktree-finish-design.md)
要求 propose / apply / verify / sync / archive 每个入口在准备结束回复时，
若存在本次相关隔离 worktree，必须询问合并、清理或保留。该询问打断各阶段主线，
且用户通常只想在明确需要时才处理 worktree。

本设计取代 2026-08-21 的**触发条件**：默认留下隔离 worktree，各阶段不得主动
询问怎么处理。合并与清理的安全步骤仍保留，仅在用户本轮明确要求时执行。

propose 起始是否使用隔离 worktree 的询问不变，仍以
[2026-08-18 propose worktree 选择设计](2026-08-18-openspec-propose-worktree-choice-design.md)
与 5.1 节 D 段为准。

## 目标

- propose / apply / verify / sync / archive 的 command 与 skill 入口结束时，
  不得询问本次隔离 worktree 如何处理，也不得弹出合并 / 仅清理 / 保留菜单。
- 默认留下本次隔离 worktree 及其分支；不得因此自动提交、合并或删除。
- 仅当本轮用户提示明确要求合并、清理、删除本次 worktree 或结束隔离工作区时，
  才执行既有安全收尾步骤。
- 已接入项目中仍写「结束时必须询问」的 A/B/C、D、E 块必须被检测为 `STALE`
  并整块替换，避免检查显示 `OK` 但正文仍强制询问。
- OpenSpec 官方生成物升级后，仍可检测收尾增强块状态并安全地重新注入。

## 非目标

- 不把官方 command/skill 纳入 Git 跟踪。
- 不修改 OpenSpec CLI 或 `evidence-driven` schema。
- 不改变 propose 起始 worktree 选择（D 节 `AI_TOOLS_PROPOSE_WORKTREE_ASK_ALWAYS_V1`）。
- 不改变 apply、verify、sync、archive 的既有 Verify 门禁语义。
- 不自动 stash、`git reset --hard`、`git worktree remove --force` 或
  `git branch -D`。
- 不对长期手工 worktree，或仓库外且不是本会话创建的托管 worktree 收尾。
- 不把收尾块并入 `AI_TOOLS_PROPOSE_WORKTREE_V1` 或 `AI_TOOLS_VERIFY_GATE_V1`
  的主标记计数；三类规则仍用独立主标记。

## 方案选择

继续向官方生成物追加版本化标记块，主标记仍为 `AI_TOOLS_WORKTREE_FINISH_V1`，
目标文件仍为 2026-08-21 列出的 10 个 command/skill。不删除 E 节，以免用户
事后明确要求合并或清理时缺少安全步骤。

内嵌触发标记由 `AI_TOOLS_WORKTREE_FINISH_ASK_ALWAYS_V1` 改为
`AI_TOOLS_WORKTREE_FINISH_NO_ASK_V1`。仍保留
`AI_TOOLS_WORKTREE_FINISH_SCOPE_V1` 与
`AI_TOOLS_WORKTREE_FINISH_MERGE_CLEANUP_V1`。

为避免旧 A/B/C、D 正文继续写「结束时必须问」而检查仍为 `OK`：

- A/B/C 注入增加 `AI_TOOLS_VERIFY_GATE_NO_FINISH_ASK_V1`，并纳入 8 文件
  检查的 required（含此前 required 为空的 sync/archive）。
- D 注入增加 `AI_TOOLS_PROPOSE_WORKTREE_NO_FINISH_ASK_V1`，并纳入 propose
  2 文件检查的 required。

未采用「删除 E 节」或「只留在 propose」：前者丢失安全步骤，后者无法覆盖
用户在 apply/verify 会话中明确要求收尾的情况。

## 交互与执行流程

### 禁止主动询问

每个入口 Agent 准备结束回复时（官方主体成功、失败停止，apply 已等完衔接的
verify，或本次 worktree 已创建但官方主体未完成）：

1. 若当前 Agent 是实施者、调查者或 apply/verify 阶段子 Agent：不得询问，
   不得合并或删除 worktree。
2. 不得判断「是否询问收尾」。不得提供「合并到主分支并清理 worktree」
   「仅清理 worktree，不合并」「保留 worktree」「提交后合并并清理 worktree」
   或等价选项。
3. 默认保留本次隔离 worktree。可以简短报告路径与分支仍在，不得追问如何处理。
4. 未在本轮收到明确收尾要求时：不得提交、不得合并、不得删除，也不得把
   切回主工作区当作收尾动作。

同一入口命令也不得在结束前「顺便问一次」。apply 衔接 verify 时，链路结束
同样不得主动询问。

### 明确要求的判定

只检查父 Agent 或用户下发给本次任务的提示文本；本规则正文中的标记字符串
不计入判定。

算明确要求的例子：合并并清理、只删 worktree、删除本次隔离工作区、把
worktree 合并回主分支。

不算明确要求：未回答、取消、「下一步呢？」、仅确认官方主体结果、仅回答
propose 起始的「使用隔离 worktree」或「在当前工作区继续」、含糊的
「处理一下 worktree」。含糊要求不得弹出菜单；报告默认保留，并说明只有
明确说合并或清理才会执行。

### 按需执行

仅当本轮存在明确要求时，才解析并冻结收尾对象（范围与 2026-08-21 相同）：

- 本会话 `$SESSION_WORKTREE`，或主工作区下 `.worktrees/` / `.worktree/` /
  `worktrees/`（及项目约定父目录）中的当前路径。
- `git worktree list --porcelain` 路径经 `pwd -P` 后全等匹配，记下
  `$FINISH_REMOVE_PATH`；不得子串包含。
- D 节必须继续冻结 `$SESSION_WORKTREE`（`AI_TOOLS_PROPOSE_WORKTREE_SESSION_V1`）。

用户已明确要求且工作区干净、两分支具名时：直接执行对应动作，不必再问
三选一。

用户要求合并并清理但 `$FINISH_WORKTREE` 不干净：列出未提交改动，仅在用户
明确同意本次提交后才提交并继续；拒绝则停止并保留 worktree。这是对已提出
的合并要求补提交同意，不是阶段结束菜单。提交后（含 hook）仍脏则停止。

用户要求仅清理但工作区不干净：停止并报告，不得删除，不得改问三选一。

`$WORKTREE_BRANCH` 或 `$TARGET_BRANCH` 为 `HEAD` / 空游离时不得合并；
游离 HEAD 若用户要求仅清理且工作区干净，只删 worktree 目录，不得
`branch -d HEAD`。

## 合并与清理

安全步骤与 2026-08-21 相同，仅触发改为按需：

1. 「提交后合并」须先展示 `git -C "$FINISH_WORKTREE" status`，用户明确同意
   后才提交；拒绝则停止。提交后仍脏则停止，不得合并或删除。
2. `$FINISH_WORKTREE` 与 `$MAIN_WORKTREE` 都必须干净才能合并或删除。
3. 先把本会话工作区根目录切到主工作区；仅 shell `cd` 不算成功。
4. `git -C "$MAIN_WORKTREE" merge --no-edit "$WORKTREE_BRANCH"`。
5. 冲突、主工作区脏、游离 HEAD 或失败时保留 worktree，不得继续删除。
6. 断言 `$FINISH_WORKTREE != $MAIN_WORKTREE` 后，
   `git -C "$MAIN_WORKTREE" worktree remove "$FINISH_REMOVE_PATH"`（不得
   `--force`）。仅当 `$WORKTREE_BRANCH` 是具名分支时再
   `git -C "$MAIN_WORKTREE" branch -d`（不得 `-D`，不得对 `HEAD` 执行 `-d`）。

仅清理：worktree 必须干净，同样先切回主工作区再用 `git -C` remove。

用户明确说保留：不提交、不合并、不切换、不删除（与默认行为相同）。

## 状态检测与升级

E 节 10 文件检查的 `STALE` 改为：存在收尾块但缺少
`AI_TOOLS_WORKTREE_FINISH_NO_ASK_V1`、
`AI_TOOLS_WORKTREE_FINISH_SCOPE_V1` 或
`AI_TOOLS_WORKTREE_FINISH_MERGE_CLEANUP_V1`（含仍只有
`AI_TOOLS_WORKTREE_FINISH_ASK_ALWAYS_V1` 的旧块），必须用当前 E 节完整
文本整块替换。

A/B/C 的 8 文件检查增加 required
`AI_TOOLS_VERIFY_GATE_NO_FINISH_ASK_V1`。sync/archive 此前 required 为空，
本改动后缺少该标记即为 `STALE`。

D 的 2 文件检查增加 required
`AI_TOOLS_PROPOSE_WORKTREE_NO_FINISH_ASK_V1`。缺少该标记、或结尾仍要求
「准备结束回复时必须询问收尾」的旧 D 块为 `STALE`。

`OK` / `MISSING` / `DUPLICATE` / `NOFILE` 语义不变。`openspec update` 后
必须重新跑三套检查。

## 错误处理与安全边界

- 不主动询问不等于可以自动收尾；未明确要求时不得提交、合并或删除。
- 明确要求合并时，未同意提交不得在脏工作区继续。
- 不在未切回主工作区时删除当前 worktree。
- 合并、remove、删分支必须 `git -C "$MAIN_WORKTREE"`。
- 只删除本次 `$FINISH_WORKTREE` 与对应具名分支；不得删除兄弟 worktree 或
  父目录。
- 子 Agent 与工作者不得向用户提问，也不得执行收尾。

## 验收

在临时目标项目中安装官方 Cursor 生成物并注入增强块，验证：

1. 10 个目标文件的收尾块均被识别为 `OK`，且含
   `AI_TOOLS_WORKTREE_FINISH_NO_ASK_V1`，不含必须结束询问的旧文案。
2. 8 个 Verify 门禁文件含 `AI_TOOLS_VERIFY_GATE_NO_FINISH_ASK_V1`；2 个
   propose 文件含 `AI_TOOLS_PROPOSE_WORKTREE_NO_FINISH_ASK_V1`。
3. 在本次相关隔离 worktree 中结束 propose / apply / verify / sync / archive
   后都不询问怎么处理；官方主体失败但 worktree 已在时也不问。
4. 结束时可报告路径仍在，但不得出现三选一菜单。
5. 用户本轮明确要求合并并清理时，用 `git -C "$MAIN_WORKTREE"` 先合并再
   删除本次路径。
6. 有未提交改动且用户要求合并时，未同意提交不得合并或删除。
7. 含糊的「下一步」不得触发菜单或收尾。
8. 实施者、调查者与阶段子 Agent 不询问、不收尾。
9. 仍含 `AI_TOOLS_WORKTREE_FINISH_ASK_ALWAYS_V1`、或 A/B/C/D 缺少
   `NO_FINISH_ASK` 标记的旧块为 `STALE` 并可整体替换。
10. 运行 `openspec update` 后重新注入，三套检查恢复 `OK`。
11. `.worktrees/` 下多个实例时，按需清理只删除本次 `$FINISH_REMOVE_PATH`。
12. 缺少 `AI_TOOLS_PROPOSE_WORKTREE_SESSION_V1` 的旧 D 块仍为 `STALE`。

## 文档落点

权威注入正文仍只在 `docs/ai-tools-integration.md` 第 5.1 节。同步更新
`README.md`、`docs/ai-sdd-workflow.md`、`docs/openspec-upgrade-plan.md`。
2026-08-21 设计保留为历史，并在文首标明触发条件已被本文取代。
