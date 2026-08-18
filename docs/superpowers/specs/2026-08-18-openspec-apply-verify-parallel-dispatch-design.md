# OpenSpec apply / verify 阶段内并行派发设计

## 背景

当前 `AI_TOOLS_VERIFY_GATE_V1` 要求入口 Agent 派发 **一个** apply 子 Agent，成功后再派发
**一个**独立 verify 子 Agent。apply 子 Agent 执行官方逐项循环；verify 子 Agent 单独完成
验证闭环。两者均不得再派发 apply / verify 阶段子 Agent。

目标项目若已安装 Superpowers 的 `dispatching-parallel-agents`，apply 内部的独立 task
与 verify 内部的独立失败域可以并行，但现有注入禁止阶段内再派发工作者，且未说明
skill 缺失时如何回退。

本次调整要求：

1. 入口编排不变：apply 阶段与 verify 阶段仍串行，各派一个阶段子 Agent；
2. 阶段子 Agent 在**当前会话能用到** `dispatching-parallel-agents` 时，按该 skill
   对独立域并行派发工作者；
3. 当前会话用不了该 skill 时，走现有官方默认（apply 逐项、verify 单 Agent），不得为
   并行再派工作者；
4. skill 是否可用在**每次** apply / verify **运行时**判定，不在注入替换时钉死。

## 约束

- 继续采用 official-first：不在本仓库分发 OpenSpec 官方 command/skill 副本，也不把
  `dispatching-parallel-agents` 全文抄进注入。
- 只改目标项目官方 apply、verify command/skill 的 A/B 注入；C 节 sync/archive 不变。
  完整接入仍检查 apply、verify、sync、archive 共 8 个文件。
- 不新增专用 `.cursor/agents`、全局 `.cursor/rules`，不改 `tasks.md` schema，不为并行
  强制 git worktree。
- 继续使用唯一幂等块标记 `AI_TOOLS_VERIFY_GATE_V1`。
- 新增运行时并行开关标记 `AI_TOOLS_PARALLEL_DISPATCH_V1`，仅用于存量检查识别旧注入；
  该标记不表示 Superpowers 已安装。
- 保留现有防递归标记、最多 3 轮修复复验、工作区指纹以及 sync/archive 门禁。
- delegated 判定仍只读取父 Agent 或用户下发给本次任务的提示文本；规则正文中的标记
  字符串不计入判定。

## 设计

### 运行时开关，而非安装时开关

注入替换只把规则改成「有 skill 则阶段内并行，无 skill 则串行默认」。**不**在替换时
记录目标项目是否安装 Superpowers。

每次执行 `/opsx-apply` 或 `/opsx-verify`（含 apply 成功后衔接的 verify）时，由对应
阶段子 Agent 判定：

- 当前会话可用 skills 中存在名为 `dispatching-parallel-agents` 的 skill，或能读到
  对应 `SKILL.md` → 读取并遵循该 skill，对独立域并行派发工作者；
- 找不到 → 不猜测、不联网安装、不把规则正文里出现的 skill 名当作已可用，按官方
  默认串行执行。

因此：

- 先替换注入、当时没有 Superpowers：行为与替换前相同（串行）；
- 之后用户自行安装 Superpowers：无需再次替换注入，下一轮 apply / verify 启用阶段内
  并行；
- 卸掉 Superpowers：自动回到串行；
- 需要再替换注入的，只有注入文本过期（缺 `AI_TOOLS_PARALLEL_DISPATCH_V1` 等当前标记）。

`STALE` 只表示门禁注入仍是旧文案，与 Superpowers 是否安装无关。

### 派发角色

入口 Agent 仍是阶段编排者，不直接实施或验证：

- `/opsx-apply`：依次派发 apply 子 Agent、verify 子 Agent，并等待两者完成；
- `/opsx-verify`：派发 verify 子 Agent 并等待完成；
- apply 子 Agent、verify 子 Agent：在当前工作区执行对应官方 skill，并在 skill
  可用时按该 skill 派发工作者；只向入口 Agent 返回阶段结果。

工作者角色仅在 `dispatching-parallel-agents` 可用时出现：

- **实施者**（apply 内部）：只做被分配的独立 task 域；
- **调查者**（verify 内部）：只做被分配的独立失败域或只读检查域，按该 skill 调查
  或在无共享状态时修改互不重叠的文件。

入口 Agent 仍处理需要用户决策、权限或凭据、外部服务故障、破坏性操作及超出
change 范围的修改。阶段子 Agent 或工作者遇到这些情况时停止并返回明确阻塞，不直接
询问用户。

### 防递归与阶段边界

入口派发阶段子 Agent 的标记不变：

- apply：`AI_TOOLS_DELEGATED_APPLY_V1`
- verify：`AI_TOOLS_DELEGATED_VERIFY_V1`

「不得再派发 apply 或 verify 子 Agent」指不得再派发 **阶段**子 Agent，不禁止在
skill 可用时派发实施者 / 调查者。

始终生效，与 skill 是否可用无关：

1. apply 与 verify **之间**必须串行；verify 不得与未完成的 apply 对开。
2. 阶段子 Agent 不得再派发 apply / verify 阶段子 Agent。
3. 实施者、调查者不得再派发 apply / verify 阶段子 Agent。
4. 只有 apply 子 Agent 勾选 `tasks.md`。
5. 只有 verify 子 Agent 写 `verification.md`、执行修复复验收口、写入门禁块并计算
   指纹；每次代码被修改后，由 verify 子 Agent 针对修复后的完整 diff 重新审查。
6. 共享状态、会改同一文件或同一制品、修 A 可能带上 B、或拿不准时：不并行，与
   `dispatching-parallel-agents` 自身的 Don't use 条件一致。

### apply 内部

apply 子 Agent 仍执行官方 `openspec-apply-change` 主体，并在全部 task 结束后对完整
实现 diff 做首次代码审查。

skill 可用时：

1. 读取 `dispatching-parallel-agents`，按独立域把 pending task 分组；
2. 同一轮发出多个实施者子 Agent；每个实施者只得到自己的 task、拟改范围和约束；
3. 实施者返回后，apply 子 Agent 检查 diff 是否重叠；重叠则由 apply 子 Agent 串行
   重做冲突项；
4. apply 子 Agent 勾选已完成且无冲突的 `tasks.md` 项。

skill 不可用时：官方逐项循环，apply 子 Agent 自己实施，不得为并行派发实施者。

### verify 内部

verify 子 Agent 仍执行官方 `openspec-verify-change` 主体与现有验证闭环（最多 3 轮
验证—修复—重新验证、写 `verification.md`、未处理 Critical/Important 不得通过、
指纹 PENDING 再替换为 SHA-256）。

skill 可用时：

1. 对只读、互不干扰的检查或独立失败域，按该 skill 同一轮派发调查者；
2. 调查者不得写 `verification.md`、不得写门禁块、不得计算指纹；
3. 调查者返回后，verify 子 Agent 汇合结论、检查冲突、写入 `verification.md`；
4. 需要安全修复时，若修复域独立且无共享状态，可按该 skill 并行修复互不重叠的文件；
   否则由 verify 子 Agent 串行修复；
5. 每一轮修复后的完整复验、完整 diff 审查、门禁与指纹仍由 verify 子 Agent 串行收口。

skill 不可用时：verify 子 Agent 独自完成闭环，不得为并行派发调查者。

### 注入形态

向 apply、verify 的 A/B 注入追加「阶段内并行」小节，必须同时出现：

- `AI_TOOLS_PARALLEL_DISPATCH_V1`（存量检查用）
- skill 名 `dispatching-parallel-agents`
- 运行时判定步骤（找得到才遵循，找不到则默认串行，不安装）
- 上文「始终生效」的制品与阶段边界

不粘贴该 skill 的步骤全文。不把 skill 名或并行标记当作 delegated 判定的一部分。

### 存量检查

保留 8 文件、每文件唯一 `AI_TOOLS_VERIFY_GATE_V1` 的检查。apply 两个文件在已有
`AI_TOOLS_DELEGATED_APPLY_V1` 之外，还必须含 `AI_TOOLS_PARALLEL_DISPATCH_V1`；
verify 两个文件在已有 `AI_TOOLS_DELEGATED_VERIFY_V1` 之外，同样必须含该并行标记。
缺任一当前标记即 `STALE`，用当前 A/B 节完整文本替换，不得追加。sync/archive 不要求
并行标记。

### 文档范围

需要更新：

- `docs/ai-tools-integration.md`：替换 A/B 注入、扩展存量检查、升级说明、验收清单
  与 FAQ；
- `docs/ai-sdd-workflow.md`：说明阶段内并行是运行时开关，缺 skill 则与现网串行相同；
- `README.md`：同步能力摘要，避免写成「安装注入时必须已有 Superpowers」。

## 异常处理

- 阶段子 Agent 判定 skill 不可用：静默走默认串行，不向用户报错，不阻塞 apply/verify。
- 实施者或调查者返回冲突、重叠 diff 或共享制品改动：阶段子 Agent 串行重做冲突项；
  不能安全重做时停止并返回入口 Agent。
- 工作者缺少必要上下文：返回阶段子 Agent 补齐后重派或改串行；不得猜测 change。
- apply 子 Agent 未成功返回：不派发 verify，change 保持 active。
- verify 子 Agent 未成功返回或门禁失败：apply 不得宣告完成，change 保持 active。
- 子 Agent 工具不可用：入口 Agent 报告环境能力不足，不回退为入口 Agent 直接执行
  官方 apply/verify 主体。阶段内并行工具不可用时，退回该阶段的默认串行。

## 验证

- 检查 A/B 注入含 `AI_TOOLS_PARALLEL_DISPATCH_V1`，且不包含 `dispatching-parallel-agents`
  skill 正文步骤。
- 检查存量脚本：apply/verify 缺并行标记为 `STALE`；仅缺 Superpowers 不得标 `STALE`。
- 检查入口路径仍是「apply 子 Agent → verify 子 Agent → 门禁」，二者不对开。
- 检查「不得再派发 apply/verify 子 Agent」不会禁止 skill 可用时的实施者 / 调查者。
- 检查 `tasks.md` 仅由 apply 子 Agent 勾选；`verification.md`、门禁与指纹仅由
  verify 子 Agent 写入。
- 检查文档明确：skill 可用性每次运行时判定；后续安装 Superpowers 无需再替换注入。
- 检查缺 skill 时的默认路径与本次变更前的串行语义一致。
- 检查 C 节、3 轮修复复验、完整 diff 代码审查、指纹与 sync/archive 门禁语义不变。

## 非目标

- 不把 apply 与 verify 两个阶段并行。
- 不在 `tasks.md` 增加并行组标注或新 schema 字段。
- 不把 Superpowers skill 安装进 ai-tools 或目标项目接入清单。
- 不新增具名 Cursor custom agents。
- 不将 sync 或 archive 改为子 Agent 执行。
- 不新增用户可绕过的 Verify 门禁。
