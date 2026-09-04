# OpenSpec 场景化工作流

本文按常见工作场景说明 OpenSpec 工作流的选择方式。先判断当前工作处于需求探索、
方案调整、实现、验证还是代码回写阶段，再沿流程图选择对应路径。图中的步骤越多，
通常意味着需要补充或更新的制品越多，整体工作量也越大。

官方入口因助手而异，本文用阶段名（`explore` / `propose` / `apply` 等）描述流程；
实际调用请换成当前助手的写法：Cursor `/opsx-*`，Codex `$openspec-*`。
图中的 `from-code` 是 Cursor / Codex 共用的
`openspec-update-change-from-code` Agent Skill，唯一源位于 `.agents/skills/`。

## 各个场景工作量

下图展示七类场景的推荐路径。其中 `explore` 用于澄清问题，`propose` 用于建立
change，`update` 用于调整已有规划，`apply` 用于实施任务，`verify` 用于核验实现，
`archive` 用于结束 change，`sync` 用于在不归档的情况下将 delta specs 合并到
main specs。手动执行 `sync` 是可选步骤；若归档前尚未同步，`archive` 会提示先同步
delta specs，再完成归档。图中的 `from-code` 是 skill
`openspec-update-change-from-code` 的简称，用于从代码回写已有 active change，
或在没有 active change 且只有一份对应 main spec 时回写该 spec；目标有歧义时先请用户选择。

```mermaid
flowchart TD
    Start{当前场景}

    Start -->|1. 新需求，需要先探索| Explore[explore]
    Explore --> Propose[propose]

    Start -->|2. 已有方案，需要更新| ProposeUpdate[propose<br/>待更新]
    ProposeUpdate --> Update[update]

    Start -->|3. 实施中发现偏差| ApplyDrift[apply<br/>发现偏差]
    ApplyDrift --> Update

    Start -->|4. 验证中发现问题| VerifyFailed[verify<br/>发现问题]
    VerifyFailed --> ProblemType{问题类型}
    ProblemType -->|实现缺陷| Apply
    ProblemType -->|规划错误或制品矛盾| Update
    ProblemType -->|验证证据不足| AddEvidence[补充验证检查]
    AddEvidence --> Verify

    Start -->|5 / 6 / 7. 已有代码| ActiveChange{是否存在对应的<br/>active change?}
    ActiveChange -->|是：场景 5| FromCode[from-code<br/>回写 change]
    FromCode --> Verify
    ActiveChange -->|否| HasSpec{是否存在对应的<br/>main spec?}
    HasSpec -->|是：场景 6| FromCodeSpec[from-code<br/>回写 spec]
    HasSpec -->|否：场景 7| ProposeFromCode[propose<br/>基于代码事实]
    FromCodeSpec --> SpecDone([main spec 已按代码回写])
    Start -->|独立同步 delta specs，不归档| Sync[sync]
    Sync --> Synced([main specs 已同步<br/>change 保持 active])

    Propose --> Apply[apply]
    ProposeFromCode --> Apply
    Update --> Apply
    Apply --> Verify[verify]
    Verify -->|通过后建议归档| Archive[archive]
    Archive --> SyncCheck{delta specs<br/>是否已同步?}
    SyncCheck -->|否：archive 提示同步| ArchiveSync[归档前同步<br/>delta specs]
    SyncCheck -->|是| Done([change 已结束])
    ArchiveSync --> Done
```

## SDD 增强闭环

上一张图用于选择命令场景和推荐路径；下图复用其中的入口，并展开进入 active change
后的增强闭环。目标项目使用本仓库
`evidence-driven` schema，并按[接入文档](ai-tools-integration.md#51-补充-verify-修复闭环与流转门禁)
安装 `AI_TOOLS_VERIFY_GATE_V2` 增强规则后，可形成下面的规格驱动、证据验证和反馈
回流闭环；若同时安装 from-code skill，已有代码也可从对应入口接入。
这些增强不改变 OpenSpec 官方命令的默认语义。

```mermaid
flowchart TD
    Baseline[main specs 与当前代码事实] --> Entry{当前场景}
    Entry -->|需求或方案不明确| Explore[explore]
    Explore --> Plan[propose 或 update]
    Entry -->|新需求或更新已有规划| Plan
    Entry -->|已有代码且存在 active change| FromCodeChange[from-code 回写 change]
    Entry -->|已有代码、无 active change<br/>但存在唯一 main spec| FromCodeSpec[from-code 回写 spec]
    Entry -->|已有代码且无对应 main spec| ProposeFromCode[propose 基于代码事实]

    Plan --> Proposal[proposal]
    ProposeFromCode --> Proposal
    Proposal --> Specs[specs]
    Proposal --> Design[design]
    Specs --> Tasks[tasks]
    Design --> Tasks
    Tasks --> VerificationPlan[verification 计划]
    VerificationPlan --> ApplyLoop[apply 子 Agent]
    ApplyLoop --> VerifyLoop[独立 verify 子 Agent]
    FromCodeChange --> VerifyLoop
    FromCodeSpec --> SpecDone([main spec 已按代码回写])
    VerifyLoop --> Repairable{阻塞可安全修复且<br/>仍可继续尝试?}
    Repairable -->|是| RepairInVerify[verify 子 Agent 修复并完整复验]
    RepairInVerify --> VerifyLoop
    Repairable -->|否| VerifyResult{最终验证结果}

    VerifyResult -->|实现缺陷| ApplyLoop
    VerifyResult -->|规划偏差或制品矛盾| UpdateArtifacts[update 受影响制品]
    UpdateArtifacts --> Proposal
    VerifyResult -->|证据不足| AddChecks[补充并执行检查]
    AddChecks --> VerifyLoop

    VerifyResult -->|通过| Gate{Verify 门禁通过}
    Gate -->|暂不流转| Active[change 保持 active]
    Gate -->|sync| Synced[delta specs 已同步<br/>change 保持 active]
    Gate -->|archive| ArchiveLoop[archive]

    Active --> ActiveNext{active change 后续}
    Synced --> ActiveNext
    ActiveNext -->|继续实施或范围变化| UpdateArtifacts
    ActiveNext -->|发现实现缺陷| ApplyLoop
    ActiveNext -->|证据不足| AddChecks
    ActiveNext -->|无新增变化，准备结束| Gate

    ArchiveLoop --> SyncCheck{delta specs<br/>是否已同步?}
    SyncCheck -->|否：archive 提示同步| ArchiveSync[归档前同步<br/>delta specs]
    SyncCheck -->|是| WorktreeFinish{本轮用户明确要求<br/>收尾 worktree?}
    ArchiveSync --> WorktreeFinish
    WorktreeFinish -->|是：按需合并或清理| Closed
    WorktreeFinish -->|否：默认保留| Closed
    Closed[change 已结束<br/>适用的规格变化已沉淀]
    Closed --> PostRelease{发布后验证是否发现问题?}
    PostRelease -->|否| NewBaseline([形成下一轮基线，等待后续需求])
    PostRelease -->|是| NewChange[建立新 change]
    NewChange --> Proposal
```

场景入口与增强约束说明如下：

- `explore` 只负责澄清需求与方案，不创建 change 制品；结论明确后，根据是否已有
  active change 进入 `propose` 或 `update`。安装 from-code 后，场景 5 回写 active
  change 并进入 verify，场景 7 从 `propose` 进入完整闭环；场景 6 只回写唯一对应的
  main spec，因此在图中直接结束，不进入 active change 闭环。
- `evidence-driven` schema 建立 `proposal / specs / design / tasks / verification`
  之间的制品依赖，要求 `apply` 在 `verification.md` 已存在后实施，并跟踪
  `tasks.md`；紧凑的 `verification.md` 负责保存范围、需求与检查的对应关系、代码
  审查和剩余风险。每轮复验更新原检查行，只保留当前权威证据，不追加完整历史。
- 安装 `AI_TOOLS_PROPOSE_WORKTREE_V1` 后，每次 `propose` 都必须先询问使用隔离
  worktree 还是当前工作区；询问和 worktree 准备发生在创建 change 或写入制品之前。
  选择隔离 worktree 时每次 propose 都必须新建独立 worktree，即使已处于
  linked worktree 也不得复用当前目录；必须先把会话工作区根目录切到新路径，
  切不过去则停止。原生 worktree 可以在仓库外；手工创建才锚定主工作区父目录，
  禁止嵌套。未安装 `AI_TOOLS_PROPOSE_WORKTREE_V1` 时，`propose` 仍以目标项目
  当前 OpenSpec 官方生成物为准。安装 `AI_TOOLS_WORKTREE_FINISH_V1` 后，入口
  Agent 准备结束回复时不得询问隔离 worktree 怎么处理；默认留下本会话创建的
  路径，或主工作区下项目 worktree 父目录中的当前路径。仅当本轮用户明确要求
  合并或清理时才执行收尾。有未提交改动须先经用户明确同意提交。不得自动合并
  或删除，也不得清理兄弟 worktree。主分支指主工作区当前检出分支。未安装收尾
  块时，用户明确要求也没有这套安全步骤。
- 安装 `AI_TOOLS_VERIFY_GATE_V2` 后，入口 Agent 负责编排，不直接执行 apply 或 verify
  主体；apply 子 Agent 成功后才派发独立 verify 子 Agent；单独运行 `/opsx-verify` 时，
  入口 Agent 同样派发 verify 子 Agent。verify 先确认可解析的 baseline 与 change
  范围，再执行检查。图中的“仍可继续尝试”表示未达到三轮上限、未连续两轮无进展，
  且不涉及用户决策、权限或凭据、外部服务故障、破坏性操作或范围外修改。满足条件的
  阻塞由 verify 子 Agent 直接修复并完整复验；每次修改代码后都针对修复后的完整
  diff 重新执行代码审查并更新 verification。不能继续修复的问题再按类型回到
  `apply`、`update` 或补充检查。阶段内并行由入口按会话 skills 目录交接
  `dispatching-parallel-agents`：使用唯一有边界的块传递 AVAILABLE 与绝对 Path，
  或传递 UNAVAILABLE 并串行；交接畸形或读取失败会阻塞，不得静默降级。子 Agent
  回报「阶段内并行：」行。后续安装无需再替换注入。自行扫描磁盘上的 `SKILL.md`
  不足以为可用。
- `sync` 或 `archive` 入口会检查验证状态为通过、阻塞项为无，并复核 V2 范围指纹。
  范围内变化构成范围内阻断；范围外变化只产生范围外告警。若范围外路径属于
  当前 change，必须扩展范围并复验。正常 sync 生成的 main spec 未纳入声明范围时，
  不使 implementation verification 失效；后续没有新增变化时，archive 入口直接复核
  已有门禁与 V2 范围指纹，不重复实现验证。若要继续实施或改变范围，先通过 `update` 调整
  受影响制品，再进入 apply。
- 未安装增强规则时，以上子 Agent 派发、门禁与隔离 worktree 收尾均不成立；`verify`、`sync`、`archive`
  的具体条件与行为仍以目标项目当前 OpenSpec 官方生成物为准。OpenSpec 1.12.0 官方
  `/opsx-verify` 只输出会话记分卡（Completeness / Correctness / Coherence），不写
  `verification.md`；官方 `/opsx-archive` 对未完成制品或任务仅警告并允许用户确认
  继续。项目级 Verify 门禁不是官方行为。
- 发布后发现问题时，不修改已归档 change：change 仍为 active 时通过 `update` /
  `apply` 回流，已经归档时建立新 change，进入下一轮规格驱动闭环。

## 场景说明

### 场景 1：新需求，需要先探索

当需求目标、范围或实现方向尚不明确时，先通过 `explore` 梳理问题、约束和可选方案。
OpenSpec 1.12.0 的官方 `explore` 会在提出事实性问题前只读检查相关 OpenSpec 制品、
源码、测试、文档与配置，并按决策依赖一次聚焦一个问题；开放式讨论不强制变成访谈或产物。
结论明确后使用 `propose` 建立 change，再依次完成实现与验证。
官方 `propose` 在起草制品时会先读取项目 `context` / `rules`，并按需只读检查实现、测试、
配置与文档，以实际发现确定 scope、approach 和 tasks；若规划根与代码项目分离或源码不可用，
应明确目标或说明限制，而不是留下泛化的“探索代码库”实施任务。
`propose` 开始时若已安装 worktree 选择规则，应先选择隔离 worktree 或当前工作区。
若选择隔离 worktree，后续命令跑完后默认留下本次 worktree，不得主动询问怎么处理；
仅当用户明确要求时才合并或清理。

推荐路径：`explore → propose → apply → verify → archive`。

该场景步骤最多，但能在实施前消除关键歧义，适合影响范围较大、存在多种实现方案，
或需要先确认边界的新需求。

### 场景 2：已有方案，需要更新

当 change 已经建立，但 proposal、specs、design、tasks 或 verification 与最新决策
不一致时，使用 `update` 更新规划，再继续实施和验证。

推荐路径：`propose（待更新）→ update → apply → verify → archive`。

更新时应说明变化原因及受影响的制品，确保任务、设计和验证计划仍然相互一致。

### 场景 3：实施中发现偏差

在 `apply` 过程中，如果发现原方案遗漏边界、任务拆分不合理或实现约束发生变化，
应暂停实施并通过 `update` 回写规划，然后基于更新后的 change 继续工作。

推荐路径：`apply（发现偏差）→ update → apply → verify → archive`。

如果偏差来自实现缺陷，应直接修复代码；只有确认规划本身需要变化时，才更新 change，
避免为了迁就错误实现而修改规格。

### 场景 4：验证中发现问题

在 `verify` 阶段发现问题时，应先判断问题类型，再选择处理路径：

- 实现不满足需求：若修复安全、在当前 change 范围内且无需用户决策，由 verify 子
  Agent 直接修复并复验；否则返回 `apply` 修复实现，再重新验证。
- 规划错误或制品之间存在矛盾：使用 `update` 修正规划，再通过 `apply` 完成必要
  修改并重新验证。
- 验证证据不足：补充并执行缺失的检查，再重新验证；不要仅为补证据而修改规划。

重新验证时应覆盖受影响的需求与场景，并保留失败原因、处理结果和剩余风险。

### 场景 5：已有代码，且存在 active change

当代码已经发生变化，同时存在对应的 active change 时，使用
`openspec-update-change-from-code` skill 比较代码事实与现有制品，将确认需要保留的实现回写
到 change，再执行验证。

推荐路径：`openspec-update-change-from-code → verify → archive`。

该路径适用于“实现领先于规划”的情况，不用于把缺陷合理化。若代码行为不正确，
仍应修复代码，而不是将错误行为写入 change。

### 场景 6：已有代码，无 active change，但存在对应 main spec

当代码已经发生变化，没有可更新的 active change，但 `openspec list --specs`
中已有与实现明确对应的 main spec 时，使用 `openspec-update-change-from-code`
直接把确认需要保留的行为回写到该 spec。不要新建空 change，也不要创建缺失的
capability 或 `spec.md`。

推荐路径：`openspec-update-change-from-code`（回写已有 spec）。

该路径只修改已存在的 main spec，不走官方 `/opsx-sync`（sync 是把 change 内
delta specs 合并到 main specs）。不要把错误实现写进规范：代码行为不正确时应
先修代码。若实现引入了新能力、删除了能力，或无法唯一匹配现有 spec，应请用户
选择要回写的已有 spec，或改走场景 7；不要在 from-code 中创建规范，也不要在
未询问时一次回写多份 spec。

### 场景 7：已有代码，无 active change，也无对应 spec

当代码已经存在，却没有可更新的 active change，也没有可匹配的现有 main spec
时，应直接基于可确认的代码事实使用 `propose` 建立完整 change，记录目标、范围
和验证方式，再通过 `apply` 补齐任务或调整实现，最后执行验证。不要先建立空
change 再调用 `openspec-update-change-from-code`：该 skill 只更新已有 change 制品或
已有 main spec，不负责创建缺失制品。
`propose` 开始时若已安装 worktree 选择规则，应先选择隔离 worktree 或当前工作区。
若选择隔离 worktree，该会话在后续命令跑完后默认留下本次 worktree，不得主动询问
怎么处理；仅当用户明确要求时才合并或清理。

推荐路径：`propose（基于代码事实）→ apply → verify → archive`。

新建 change 时应以可确认的代码事实为依据，同时区分“当前已经实现的行为”和
“仍需完成的工作”，避免把现状直接当作正确需求。

## 独立旁路：同步 delta specs

需要将 active change 内的 delta specs 合并到 main specs、但暂不归档时，可独立使用
官方 `/opsx-sync`。该命令只同步规格，不会结束 change。手动执行 sync 是可选步骤；
若直接运行 `/opsx-archive`，archive 会在发现 delta specs 尚未同步时提示先同步，
然后再完成归档。是否需要先执行 `verify`，以及后续何时归档，遵循目标项目当前官方
生成物。若 sync 发生在隔离 worktree 中，
跑完后默认留下本次 worktree，不得主动询问怎么处理；仅当用户明确要求时才合并或清理。
安装 V2 门禁后，sync 会复核 V2 范围指纹；同步生成的 main spec 若未纳入声明
范围，只产生范围外告警，不要求重复实现验证。范围内变化仍构成范围内阻断。

## 使用原则

- 不确定需求或方案时先 `explore`，不要在关键问题未澄清时直接实施。
- 已有 active change 时优先更新该 change，避免为同一工作重复建立规划。
- 实现或验证阶段发现规划偏差时，通过 `update` 保持制品与最新决策一致。
- `openspec-update-change-from-code` 按已确认的代码事实回写：有唯一对应的 active
  change 时只改该 change；没有 change 且只有一份对应 main spec 时只改该 spec。
  归档 change、change 与 spec 冲突、或多份 spec 都能对上时，先请用户选择，不要
  自动执行。不能建立 change、不能创建缺失 spec，也不能替代缺陷修复。
- 编写 `tasks.md` 时，每项任务必须在 `- [ ]` 说明中写明如何验证完成。
- 定位或修改主规范时：有 change 则使用 `openspec instructions apply --change "<name>" --json`
  或 `openspec status --change "<name>" --json` 中的 `planningHome.root`；无 change 的
  spec 回写使用 `openspec list --specs --json` 或 `openspec context --json` 的
  `root.path`。路径为 `<root>/openspec/specs/<capability-path>/spec.md`，不要假设仓库相对路径。
- 实现完成后建议核验。安装 `AI_TOOLS_VERIFY_GATE_V2` 后，apply 与单独
  `/opsx-verify` 均由入口 Agent 派发子 Agent 执行，阶段内并行由入口按会话 skills
  目录以唯一有边界的块交接 `dispatching-parallel-agents`，并通过 Verify 门禁与
  V2 范围指纹约束 sync/archive；范围内阻断，范围外告警。未安装增强规则时，
  `verify`、`sync`、`archive` 的具体条件与行为
  遵循目标项目当前 OpenSpec 官方生成物（1.12.0 官方 verify 仅为会话记分卡，官方
  archive 允许确认绕过）。
- 隔离 worktree 跑完后默认留下现场。安装 `AI_TOOLS_WORKTREE_FINISH_V1` 后，
  入口 Agent 不得主动询问是否合并到主分支并清理；仅当用户明确要求时才执行。
  未同意提交时不得合并或删除。长期手工 worktree 不在收尾范围。
