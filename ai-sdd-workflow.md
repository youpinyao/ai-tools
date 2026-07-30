# OpenSpec 场景化工作流

## 这份文档解决什么问题

本文面向日常使用 OpenSpec 的研发团队，帮助你根据当前场景选择正确的
`/opsx-*` 命令，并知道何时进入下一步。

项目默认使用 `evidence-driven` schema。它在 OpenSpec 的提案、规范、设计和任务
基础上增加验证计划、实现证据与独立验证门禁。所有 OpenSpec 对话、规划产物、
验证结论和归档说明都使用简体中文。

## 先判断你现在要做什么

```text
需求或方案还不清楚？
  └─ /opsx-explore

准备为一项新需求或修复建立完整规划？
  └─ /opsx-propose

已有 change，需要调整规划，但不改代码？
  └─ /opsx-update

准备开始或继续实现 tasks？
  └─ /opsx-apply

代码已经先于规划变化，需要让 change 反映代码现状？
  └─ /opsx-update-change-from-code

只想把 delta specs 合并到 main specs，不归档？
  └─ /opsx-sync

实现与实现侧检查已完成，需要独立复验？
  └─ 优先：/opsx-apply 证据门禁后自动 Task 派发独立子 Agent 跑 /opsx-verify
  └─ 备选：在全新 Agent 会话中手动运行 /opsx-verify

独立验证已通过，需要结束 change？
  └─ /opsx-archive
```

## 标准主线

```text
[可选] explore
    ↓
propose
    ↓
apply（实现 tasks，并记录实现侧验证证据）
    ↓
verify（未参与实现的 Agent 独立复验；优先由 apply 自动派发子 Agent）
    ↓
archive（可在归档时同步 delta specs）
```

这不是只能单向前进的瀑布流程。实现过程中发现需求、设计或任务有问题时，应暂停
实现，回到 `explore` 或 `update`；修订完成后再继续 `apply`。

规划产物的依赖关系如下：

```text
proposal
  ├─→ specs ─┐
  └─→ design ─┴─→ tasks → verification → apply
```

`specs` 与 `design` 都以 `proposal` 为前提；`tasks` 依赖二者；`verification.md`
在实现前创建，先记录验证计划。`apply` 完成实现后，才把真实执行结果写入其中。

## 场景一：需求不清，先探索

使用：

```text
/opsx-explore [change-name]
```

适合以下情况：

- 只有模糊想法，还不能确定是否值得建立 change。
- 需要调研现有代码、约束、风险或多个技术方案。
- 实现过程中发现原方案可能不成立，需要先想清楚。

`explore` 是思考模式，不是实现阶段。它可以读取代码和已有 change 产物，也可以
帮助形成决策，但不应修改业务代码。探索结果足够明确后：

- 新工作进入 `/opsx-propose`。
- 已有 change 的规划需要修订时进入 `/opsx-update`。
- 只需澄清问题时可以结束，不强制生成产物。

## 场景二：为新工作建立完整 change

使用：

```text
/opsx-propose <change-name 或需求描述>
```

它会按 schema 生成达到实施条件所需的全部产物：

- `proposal.md`：为什么做、做什么、影响什么。
- `specs/<capability>/spec.md`：系统必须表现出的行为和可测试场景。
- `design.md`：关键技术决策、权衡、风险和迁移方案。
- `tasks.md`：可逐项执行和勾选的实现任务。
- `verification.md`：实现后要执行的检查；此时结果必须保持“待执行”。

完成标志是 OpenSpec 状态显示实施所需产物均已就绪。下一步运行
`/opsx-apply <change-name>`。

如果一项新诉求改变了原 change 的核心意图，而不是细化原方案，应使用新的
change 名重新运行 `/opsx-propose`，不要把不相关的目标塞进旧 change。

## 场景三：已有 change，只调整规划

使用：

```text
/opsx-update <change-name>
```

适合需求变化、设计决策调整、任务拆分不合理，或多个已有产物互相矛盾的情况。
此操作只修改已有规划产物，不修改实现代码。

工作方式：

1. 读取 change 的全部已有产物。
2. 找出请求涉及的修改，以及由此产生的跨产物不一致。
3. 逐个说明拟修改的产物和原因。
4. 用户确认后写入，并重新检查整体一致性。

如果规划调整意味着代码也要变化，完成 `update` 后运行 `/opsx-apply`。如果
change 尚未生成完整规划产物，应先补齐规划，而不是直接实施。

## 场景四：正常开始或继续实现

使用：

```text
/opsx-apply <change-name>
```

`apply` 会读取 CLI 返回的上下文文件，按 `tasks.md` 逐项实施，并在每项完成后
立即勾选对应复选框。它既可开始新实现，也可继续部分完成的 change。

所有实现任务完成后，实现 Agent 必须：

1. 执行 `verification.md` 中每个适用的自动化命令和人工检查。
2. 记录真实命令、步骤、结果和简洁证据。
3. 将适用检查更新为“通过”或“失败”。
4. 对“不适用”项写明具体原因。
5. 记录跳过项、失败项和剩余风险。

实现 Agent 不得填写或修改“独立验证结论”。证据门禁完成后，应**优先**用 Task
派发独立子 Agent 执行 `/opsx-verify`（隔离上下文，不继承实现会话历史）；若无法
派发，再提示用户新开会话手动 verify。只要必需检查仍为“待执行”或“失败”，就应
暂停并处理阻塞，不能进入归档。

## 场景五：实现过程中发现规划有问题

不要猜测，也不要为了继续勾任务而绕开规划。根据问题类型选择回路：

- 问题尚不明确：暂停 `apply`，运行 `/opsx-explore <change-name>`。
- 已明确需求或设计应如何修改：运行 `/opsx-update <change-name>`。
- 规划已修订：重新运行 `/opsx-apply <change-name>`，实现新增或变化的任务。

典型流程：

```text
apply → explore → update → apply
```

如果只是代码缺陷，且规划没有变化，直接留在 `apply` 中修复并重新验证。

## 场景六：代码已先改，规划落后

使用：

```text
/opsx-update-change-from-code <change-name>
```

适合实现已发生且被确认应保留，但 active change 与代码事实不一致的情况。此时
以代码证据和用户明确决策为真源，回写 change 产物及允许范围内的相关仓库文档。

该操作会：

- 检查 Git 变更、实现代码、测试、配置、迁移和相关文档。
- 比较实现与 proposal、specs、design、tasks、verification 的偏差。
- 直接处理事实明确的小偏差；复杂的需求、范围或架构变化先征求确认。
- 严格校验更新后的 change。

该操作不会：

- 实现新功能或重构业务代码。
- 修改 main specs。
- 归档 change。

如果代码偏离规划是缺陷，而不是被接受的新行为，不应回写规划，应回到
`/opsx-apply` 修复代码。

## 场景七：只同步主规格，不归档

使用：

```text
/opsx-sync <change-name>
```

它把 change 中的 delta specs 智能合并到 main specs，处理新增、修改、移除和
重命名的需求，同时保留 delta 未涉及的原有内容。

适合以下情况：

- change 仍需保持 active，但团队需要先更新主规格。
- 多个 change 依赖最新的主规格。
- 归档前希望单独检查规格合并结果。

`sync` 只更新 main specs，不代表实现完成，也不会归档 change。重复执行应得到
相同结果。

## 场景八：独立验证实现

前提：`apply` 已完成 tasks 和实现侧检查。

独立验证可以由以下方式启动（优先 1）：

1. `/opsx-apply` 在实现证据门禁完成后，用 Task 自动派发独立子 Agent 跑 verify。
2. 用户打开未参与实现的全新 Agent 会话，手动运行：

```text
/opsx-verify <change-name>
```

独立 Agent 不信任已记录的成功结果，而是重新执行适用检查，并从三个维度复验：

- 完整性：任务是否全部完成，规范中的需求是否都有实现。
- 正确性：实现是否符合需求意图，每个场景是否有代码和测试覆盖。
- 一致性：实现是否遵循设计决策和项目既有模式。

问题分为：

- `CRITICAL`：归档前必须修复。
- `WARNING`：应修复；只有明确记录并接受剩余风险时才可通过。
- `SUGGESTION`：不阻塞归档的改进建议。

独立 Agent 必须把结论写入 `verification.md` 的“独立验证结论”：

- 无 CRITICAL、无失败检查、无适用的待执行检查时，写
  `验证结论：通过`。
- 其他情况写 `验证结论：阻塞`。
- `验证者` 填写 `独立 Agent（子 Agent）`（Task 派发）或
  `独立 Agent（新会话）`（用户手开）。

聊天中的“验证通过”不算归档证据，结论必须持久化到 `verification.md`。

## 场景九：验证失败或被阻塞

先判断什么需要成为真源：

- 实现有缺陷，规划正确：回到 `/opsx-apply` 修复代码和测试。
- 需求或设计已改变，代码还未跟上：先 `/opsx-update`，再 `/opsx-apply`。
- 当前代码行为已被确认接受，但 change 落后：运行
  `/opsx-update-change-from-code`。
- 验证环境或权限缺失：保留阻塞结论，补齐环境后重新独立验证（子 Agent 或新会话）。

修复后必须重新运行 `/opsx-verify`。不能通过接受 CRITICAL、忽略失败检查或手工
改写结论来绕过门禁。

## 场景十：归档已完成的 change

使用：

```text
/opsx-archive <change-name>
```

归档前必须同时满足：

- 所有规划产物状态为完成。
- `tasks.md` 中没有未完成任务。
- 实现侧适用检查没有“待执行”或“失败”。
- `verification.md` 包含独立 Agent（子 Agent 或新会话）写入的
  `验证结论：通过`。
- 没有未解决的 CRITICAL 问题。

只要一项不满足，归档就会停止，且不能确认覆盖。存在 delta specs 时，归档流程
会先展示同步影响，并让用户选择立即同步或不经同步直接归档。

## 三个容易混淆的操作

### `update`

真源是用户确认后的新规划。它修改 active change 的已有规划产物，不改代码。

### `update-change-from-code`

真源是已实现代码和用户明确决策。它把 active change 及相关文档回写到代码现状，
但不改 main specs。

### `sync`

真源是 change 中的 delta specs。它把需求变化合并到 main specs，不改实现代码，
也不归档。

## 日常状态与校验命令

```bash
# 查看 active changes
openspec list --json

# 查看某个 change 的产物和进度
openspec status --change "<change-name>"
openspec status --change "<change-name>" --json

# 查看某项操作解析出的上下文与动态指令
openspec instructions apply --change "<change-name>" --json

# 严格校验 change
openspec validate "<change-name>" --type change --strict

# 校验项目默认 schema
openspec schema validate evidence-driven
```

不要硬编码 change 或产物路径。Agent 应从 `openspec status --json` 返回的
`planningHome`、`changeRoot`、`artifactPaths` 和 `actionContext` 解析实际位置。

如果工作位于已注册的独立 OpenSpec store，先明确 store；后续支持 store 的 CLI
调用应持续携带同一个 `--store <id>`。
