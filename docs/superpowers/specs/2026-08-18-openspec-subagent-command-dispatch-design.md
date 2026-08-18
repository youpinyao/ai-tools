# OpenSpec apply / verify 子 Agent 派发设计

## 背景

当前增强规则只要求 apply 完成后派发独立子 Agent 执行 verify。apply 本身由入口
Agent 执行；用户单独运行 `/opsx-verify` 时，也由入口 Agent 直接执行 verify。

本次调整要求：

1. `/opsx-apply` 的实施工作由子 Agent 执行；
2. 用户单独运行 `/opsx-verify` 时，验证工作也由子 Agent 执行；
3. 主 Agent 继续负责顺序编排、等待结果、检查门禁以及与用户交互。

## 约束

- 继续采用 official-first：不在本仓库分发 OpenSpec 官方 command/skill 的完整副本。
- 本次只改变目标项目官方 apply、verify command/skill 的 A/B 注入；sync/archive 既有
  C 节注入保持不变。完整接入仍须检查 apply、verify、sync、archive 共 8 个文件。
- 不新增专用 `.cursor/agents` 或全局 `.cursor/rules`。
- `openspec update` 刷新官方生成物或 ai-tools 自定义层升级后，目标项目都必须重新
  执行存量检查。
- 继续使用唯一 `AI_TOOLS_VERIFY_GATE_V1` 幂等标记；检查必须识别缺失、重复及缺少
  当前 delegated 标记的 `STALE` 旧 V1 块。
- 保留现有验证修复轮次、工作区指纹以及 sync/archive 门禁。
- delegated 判定只读取父 Agent 或用户下发给本次任务的提示文本；规则正文中的标记
  字面量不参与判定。

## 设计

### 派发角色

入口 Agent 是编排者，不直接实施 apply 或执行 verify：

- `/opsx-apply`：依次派发 apply 子 Agent、verify 子 Agent，并等待两者完成；
- `/opsx-verify`：派发 verify 子 Agent 并等待完成；
- 子 Agent：在当前工作区执行对应官方 skill，只向入口 Agent 返回结果。

入口 Agent 负责处理需要用户决策、权限或凭据、外部服务故障、破坏性操作及超出
change 范围的修改。子 Agent 遇到这些情况时停止并返回明确阻塞，不直接询问用户。

### 防递归标记

入口 Agent 派发任务时，在子 Agent 提示中加入不可省略的上下文标记：

- apply：`AI_TOOLS_DELEGATED_APPLY_V1`
- verify：`AI_TOOLS_DELEGATED_VERIFY_V1`

追加到 command/skill 的入口规则必须在执行官方主体步骤前检查标记。判定对象仅为
父 Agent 或用户下发给本次任务的提示文本；规则正文中出现的标记字符串不计入判定：

- 提示文本未显式包含对应标记：当前 Agent 只负责派发并等待，不执行对应主体；
- 提示文本显式包含对应标记：当前 Agent 直接执行对应官方 skill，不再派发同类子
  Agent。

若当前会话已派发过同类子 Agent，该节视为已执行，不得因 command 与 skill 同处一个
上下文而重复派发。verify 子 Agent 无论由 Verify 节还是 Apply 节触发，都满足该会话
守卫。apply 入口仍负责等待 apply 子 Agent、派发并等待 verify 子 Agent 及检查门禁，
但不得执行官方 apply 主体。

### apply 流程

1. 入口 Agent 解析 change，并派发携带 `AI_TOOLS_DELEGATED_APPLY_V1` 的子 Agent。
2. apply 子 Agent 执行官方 `openspec-apply-change` skill，针对完整实现 diff 完成首次
   代码审查并记账，完成任务和制品更新后返回；它不派发 verify。
3. apply 失败或阻塞时，入口 Agent 停止流程并汇报，不启动 verify。
4. apply 成功后，入口 Agent 派发携带 `AI_TOOLS_DELEGATED_VERIFY_V1` 的独立子 Agent。
5. verify 子 Agent 执行官方 `openspec-verify-change` skill，按现有规则最多进行 3 轮
   “验证—修复—重新验证”，并更新 `verification.md`；每次修改代码后，必须针对修复
   后的完整 diff 重新执行代码审查并更新审查范围与结论。存在未处理的
   Critical/Important 时不得通过。
6. 入口 Agent 读取 Verify 门禁和工作区指纹；仅在状态通过、无阻塞且指纹匹配时结束
   apply 并建议进入 sync 或 archive。
7. 门禁失败时不得宣告 apply 完成；change 保持 active，入口 Agent 报告阻塞原因，
   不得建议 sync 或 archive。

### 单独 verify 流程

1. 用户运行 `/opsx-verify`。
2. 入口 Agent 派发携带 `AI_TOOLS_DELEGATED_VERIFY_V1` 的子 Agent 并等待。
3. verify 子 Agent 执行验证、允许范围内的安全修复、复验及 `verification.md` 更新。
4. 入口 Agent 读取并汇报最终门禁；若子 Agent 返回阻塞，则由入口 Agent 向用户说明。
5. 单独 verify 记录的最终指纹仍由后续 sync/archive 入口强制重新计算并复核。

### 文档与注入范围

需要更新：

- `docs/ai-tools-integration.md`：替换 apply 注入片段，扩展 verify 注入片段，并更新
  安装检查、升级说明和 FAQ；
- `docs/ai-sdd-workflow.md`：明确 apply 与 verify 均由独立子 Agent 执行，主 Agent 负责
  编排；
- `README.md`：同步能力摘要和接入边界。

## 异常处理

- apply 子 Agent 未成功返回：不派发 verify，change 保持 active。
- verify 子 Agent 未成功返回或门禁失败：apply 不得宣告完成，change 保持 active，
  报告阻塞原因且不得建议 sync/archive。
- 子 Agent 缺少必要上下文：返回入口 Agent 重新派发；不得猜测 change。
- 工作区在 verify 后发生变化：旧指纹失效，必须重新派发 verify。
- 子 Agent 工具不可用：入口 Agent 报告环境能力不足，不回退为主 Agent 直接执行。

## 验证

- 检查 apply、verify 的 command/skill 注入文本都包含对应防递归标记。
- 检查存量安装脚本能区分 `MISSING`、`STALE`、`DUPLICATE`、`NOFILE` 与 `OK`，且
  `STALE` 旧 V1 块采用完整替换而不是再次追加。
- 检查 apply 路径严格按“apply 子 Agent → verify 子 Agent → 门禁检查”排序。
- 检查单独 verify 路径不会由入口 Agent 直接执行 verify。
- 检查子 Agent 上下文不会再次派发同类子 Agent；verify 会话守卫同时覆盖 Verify 节
  与 Apply 节触发的派发，且判定不受规则正文中的标记字面量影响。
- 检查代码审查职责为双阶段：apply 子 Agent 首审完整实现 diff 并记账；verify 子
  Agent 每次安全修复代码后重审修复后的完整 diff 并更新结论。
- 检查门禁失败时 change 保持 active、报告阻塞，且不建议 sync/archive。
- 检查 verify 子 Agent 每次修复代码后都针对修复后的完整 diff 重做代码审查并更新
  `verification.md`，未处理 Critical/Important 时不得通过。
- 检查现有最多 3 轮修复复验、工作区指纹、sync/archive 门禁语义保持不变。
- 搜索并修正文档中“apply 会话直接实施”或“单独 verify 由当前 Agent 执行”等旧描述。

## 非目标

- 不新增具名 Cursor custom agents。
- 不改变 OpenSpec 官方 skill 的主体业务语义。
- 不将 sync 或 archive 改为子 Agent 执行。
- 不新增用户可绕过的 Verify 门禁。
