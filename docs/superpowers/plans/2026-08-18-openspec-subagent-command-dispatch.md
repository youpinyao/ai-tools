# OpenSpec apply / verify 子 Agent 派发实施计划

> **供智能体执行者使用：** 必须使用子技能 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans`，逐项实施本计划。步骤使用复选框（`- [ ]`）跟踪。

**目标：** 让增强后的 `/opsx-apply` 与单独 `/opsx-verify` 都由入口 Agent 派发子 Agent 执行，同时防止子 Agent 递归派发。

**架构：** 保持 official-first，不新增 custom agent 或 rule。只修改接入文档提供的 `AI_TOOLS_VERIFY_GATE_V1` 注入片段：入口 Agent 通过父 Agent 或用户下发的提示文本中的显式标记，把 apply、verify 主体委派给通用子 Agent，自己负责顺序编排、阻塞转交和 Verify 门禁检查；规则正文中的标记字面量不参与判定。

**技术栈：** Markdown、Cursor Agent Skills、OpenSpec 官方 command/skill、ripgrep。

## 全局约束

- OpenSpec 相关正文全部使用简体中文。
- 不在本仓库生成、复制或跟踪 OpenSpec 官方 command/skill。
- 不新增 `.cursor/agents` 或 `.cursor/rules`。
- 本次只改变 apply/verify 的 A/B 注入，sync/archive 既有 C 节注入保持不变；完整
  接入仍检查 8 个文件。
- apply 标记固定为 `AI_TOOLS_DELEGATED_APPLY_V1`。
- verify 标记固定为 `AI_TOOLS_DELEGATED_VERIFY_V1`。
- 保留 `AI_TOOLS_VERIFY_GATE_V1` 幂等标记、最多 3 轮修复复验、工作区指纹和 sync/archive 门禁。
- 不新增第二套幂等标记；存量检查必须识别 `STALE` 旧 V1 块并完整替换。
- 未经用户明确要求不创建 Git commit。

---

### Task 1：改造 command/skill 注入规则

**文件：**
- 修改：`docs/ai-tools-integration.md:31-47`
- 修改：`docs/ai-tools-integration.md:169-309`
- 修改：`docs/ai-tools-integration.md:329-370`

**接口：**
- 产生：apply 入口标记 `AI_TOOLS_DELEGATED_APPLY_V1`
- 产生：verify 入口标记 `AI_TOOLS_DELEGATED_VERIFY_V1`
- 保持：门禁标记 `AI_TOOLS_VERIFY_GATE_V1`

- [ ] **Step 1：建立旧行为回归检查**

运行：

```bash
rg -n 'apply 完成后由独立子 Agent 执行 verify|完成所有 apply 任务|当前任务上下文|只执行一次入口检查' \
  docs/ai-tools-integration.md
```

预期：最终实现中无命中；若实施前命中，必须在后续步骤清除。

- [ ] **Step 2：替换 Apply 注入片段**

将 A 节改为“Apply：派发实施与独立验证”。注入文本必须明确：

```markdown
<!-- AI_TOOLS_VERIFY_GATE_V1 -->
## Apply 子 Agent 实施与强制验证

若当前会话已按本节派发过 apply 子 Agent，本节视为已执行，不得因 command 与 skill 同处一个上下文而重复派发。入口 Agent 仍负责等待 apply 子 Agent、派发并等待 verify 子 Agent 以及检查门禁，但不得执行官方 apply 主体。

在执行任何 apply 主体步骤前，只检查父 Agent 或用户下发给本次任务的提示文本是否显式包含委派标记；本规则正文中出现的标记字符串不计入判定：

1. 若父 Agent 或用户下发的提示文本未显式包含 `AI_TOOLS_DELEGATED_APPLY_V1`，当前 Agent 是入口编排者，不得直接实施：
   - 派发一个子 Agent，在任务中加入 `AI_TOOLS_DELEGATED_APPLY_V1`，要求其使用 `openspec-apply-change` skill 实施当前 change，且不得派发 apply 或 verify 子 Agent；
   - 等待 apply 子 Agent 返回；失败或阻塞时立即停止，不得启动 verify；
   - apply 成功后派发另一个独立子 Agent，在任务中加入 `AI_TOOLS_DELEGATED_VERIFY_V1`，要求其使用 `openspec-verify-change` skill 执行 verify；
   - 等待 verify 子 Agent 返回，再检查唯一 Verify 门禁及当前工作区指纹。
2. 若父 Agent 或用户下发的提示文本显式包含 `AI_TOOLS_DELEGATED_APPLY_V1`，当前 Agent 是 apply 子 Agent：直接执行官方 apply 主体，针对完整实现 diff 完成首次代码审查并记账，不得再次派发 apply 或 verify 子 Agent；完成后把结果或阻塞返回入口 Agent。
3. 仅当 Verify 门禁为“状态：通过、阻塞项：无”且指纹匹配时，入口 Agent 才可结束 apply 并建议 sync 或 archive。
4. 门禁失败时不得宣告 apply 完成；change 保持 active，报告具体阻塞原因，且不得建议 sync 或 archive。
```

同时明确当前会话已派发时不得重复派发；派发后入口 Agent 不得继续执行官方 apply 主体。

- [ ] **Step 3：扩展 Verify 注入片段**

在原有验证修复闭环前增加入口判断：

```markdown
若当前会话已派发过 verify 子 Agent（无论由本节还是 Apply 节触发），本节视为已执行，不得因 command 与 skill 同处一个上下文而重复派发。

在执行任何 verify 主体步骤前，只检查父 Agent 或用户下发给本次任务的提示文本是否显式包含委派标记；本规则正文中出现的标记字符串不计入判定：

1. 若父 Agent 或用户下发的提示文本未显式包含 `AI_TOOLS_DELEGATED_VERIFY_V1`，当前 Agent 是入口编排者，不得直接验证：派发一个子 Agent，在任务中加入该标记，要求其使用 `openspec-verify-change` skill 执行当前 change 的完整 verify；等待后读取并汇报最终门禁。
2. 若父 Agent 或用户下发的提示文本显式包含 `AI_TOOLS_DELEGATED_VERIFY_V1`，当前 Agent 是 verify 子 Agent：直接执行以下验证闭环，不得再次派发 verify 子 Agent。
```

保留下方原有 3 轮修复复验、`verification.md` 记账、门禁块和指纹计算步骤，不改变其顺序和判定。每次安全修复代码后，verify 子 Agent 必须针对修复后的完整 diff 重新执行代码审查并更新审查范围与结论；存在未处理的 Critical/Important 时不得通过。正式阻塞条件只在验证闭环中保留一处完整清单。单独 verify 的最终指纹仍由 sync/archive 入口强制复核。

- [ ] **Step 4：更新章节摘要与幂等说明**

将“apply 完成后再派发 verify”统一改为：

```text
入口 Agent 先派发 apply 子 Agent；成功后再派发独立 verify 子 Agent。单独运行
/opsx-verify 时，入口 Agent 同样派发 verify 子 Agent。
```

保留 8 个官方文件和每文件唯一一个 `AI_TOOLS_VERIFY_GATE_V1` 的检查脚本。循环前先用 `command -v rg` 检查 ripgrep，缺失时输出明确错误并退出；count 命令不得吞掉 stderr。数量为 0 输出 `MISSING`，大于 1 输出 `DUPLICATE`；数量为 1 时，apply 两文件缺 APPLY 标记或 verify 两文件缺 VERIFY 标记输出 `STALE`，sync/archive 直接输出 `OK`，文件不存在输出 `NOFILE`。`STALE` 必须用当前 A/B 节完整文本替换，不得追加。

- [ ] **Step 5：验证注入规则完整**

运行：

```bash
rg -n 'AI_TOOLS_DELEGATED_APPLY_V1|AI_TOOLS_DELEGATED_VERIFY_V1|STALE|command -v rg|规则正文中出现的标记字符串不计入判定|无论由本节还是 Apply 节触发|不得重复派发|首次代码审查|最多执行 3 轮|修复后的完整 diff|openspec-verification-fingerprint.py' \
  docs/ai-tools-integration.md
```

预期：两个 delegated 标记均出现在对应注入片段；旧块识别、字面量排除、递归保护、门禁失败 active 分支、修复后代码审查、3 轮限制和指纹步骤均存在。

### Task 2：同步安装、迁移、验收和 FAQ

**文件：**
- 修改：`docs/ai-tools-integration.md:430-559`
- 修改：`README.md:25-153`

**接口：**
- 消费：Task 1 定义的两个 delegated 标记和派发顺序
- 产生：面向接入者的一致行为说明

- [ ] **Step 1：更新迁移行为和验收清单**

把迁移行为表及验收项更新为：

```text
apply 由子 Agent 实施；成功后由另一个独立子 Agent 执行 verify。
单独运行 /opsx-verify 时也由入口 Agent 派发 verify 子 Agent。
```

验收清单必须复用 5.1 节脚本，检查 apply/verify command 与 skill 含对应 delegated 标记，并继续检查 8 个文件各有唯一 `AI_TOOLS_VERIFY_GATE_V1`；首次接入、`openspec update` 和 ai-tools 自定义层升级后都必须实际运行，处理 `STALE` 等状态直到 8 个文件全部输出 `OK`。

- [ ] **Step 2：更新 FAQ**

将 verify FAQ 明确为：

```text
verify 主体仍跟随官方生成物；增强规则要求无论由 apply 衔接还是单独运行
/opsx-verify，都由入口 Agent 派发独立 verify 子 Agent 执行。
```

保留 verify 子 Agent 直接安全修复并复验、修复后完整 diff 代码审查、最多 3 轮以及 sync/archive 强制门禁说明。

- [ ] **Step 3：更新 README 能力摘要和主线**

将标准主线中的 apply、verify 表述改为：

```text
  → apply 子 Agent（实施并记录真实结果）
  → 独立 verify 子 Agent
```

在安装说明中补充：增强规则同时提供 apply/verify 子 Agent 派发与防递归标记；未安装时这些派发行为不成立。

- [ ] **Step 4：检查 README 与接入文档一致**

运行：

```bash
rg -n 'apply 子 Agent|verify 子 Agent|AI_TOOLS_DELEGATED_(APPLY|VERIFY)_V1|未安装增强规则' \
  README.md docs/ai-tools-integration.md
```

预期：README 与接入文档都说明 apply、单独 verify 的子 Agent 行为；标记只在需要指导注入和验收的位置出现。

### Task 3：同步场景工作流并执行全局校验

**文件：**
- 修改：`docs/ai-sdd-workflow.md:50-113`
- 修改：`docs/ai-sdd-workflow.md:186-194`
- 验证：`docs/superpowers/specs/2026-08-18-openspec-subagent-command-dispatch-design.md`

**接口：**
- 消费：Task 1 的“入口编排者 → apply 子 Agent → verify 子 Agent → 门禁”流程
- 产生：与接入文档一致的场景流程图和约束说明

- [ ] **Step 1：更新增强闭环流程图**

将节点调整为：

```mermaid
VerificationPlan --> ApplyLoop[apply 子 Agent]
ApplyLoop --> VerifyLoop[独立 verify 子 Agent]
VerifyLoop --> Repairable{存在可安全修复的阻塞?}
Repairable -->|是| RepairInVerify[verify 子 Agent 直接修复并复验]
```

保持失败后回到 apply/update/补充检查的现有分支不变。

- [ ] **Step 2：更新闭环约束**

明确：

- 入口 Agent 负责编排，不直接执行 apply 或 verify 主体；
- apply 子 Agent 成功后才派发 verify 子 Agent；
- 单独 `/opsx-verify` 也派发 verify 子 Agent，最终指纹仍由 sync/archive 入口强制复核；
- 未安装增强规则时，以上子 Agent 派发与门禁均不成立。

- [ ] **Step 3：扫描冲突旧描述**

运行：

```bash
rg -n 'apply 完成后由独立子 Agent|apply 完成时会派发|当前 Agent 直接执行 verify|apply 会话' \
  README.md docs/ai-tools-integration.md docs/ai-sdd-workflow.md
```

预期：无冲突旧描述；若命中历史背景或对比语句，语义必须明确为旧行为。

- [ ] **Step 4：扫描占位符与关键约束**

运行：

```bash
rg -n 'T[B]D|T[O]DO|待[定]' \
  docs/superpowers/specs/2026-08-18-openspec-subagent-command-dispatch-design.md \
  docs/superpowers/plans/2026-08-18-openspec-subagent-command-dispatch.md \
  README.md docs/ai-tools-integration.md docs/ai-sdd-workflow.md

rg -n 'AI_TOOLS_VERIFY_GATE_V1|AI_TOOLS_DELEGATED_APPLY_V1|AI_TOOLS_DELEGATED_VERIFY_V1|STALE|规则正文中出现的标记字符串不计入判定|change 保持 active|修复后的完整 diff|最多执行 3 轮|指纹|sync/archive' \
  README.md docs/ai-tools-integration.md docs/ai-sdd-workflow.md \
  docs/superpowers/specs/2026-08-18-openspec-subagent-command-dispatch-design.md \
  docs/superpowers/plans/2026-08-18-openspec-subagent-command-dispatch.md
```

预期：无计划占位符；门禁、两个委派标记、`STALE` 识别、规则正文字面排除、门禁失败 active 分支、修复后完整 diff 代码审查、3 轮限制、指纹和 sync/archive 强制复核均保留。

- [ ] **Step 5：检查最终差异**

运行：

```bash
git diff --check
git diff -- README.md docs/ai-tools-integration.md docs/ai-sdd-workflow.md \
  docs/superpowers/specs/2026-08-18-openspec-subagent-command-dispatch-design.md \
  docs/superpowers/plans/2026-08-18-openspec-subagent-command-dispatch.md
```

预期：`git diff --check` 无输出且退出码为 0；差异只包含本设计范围内的文档变更。
