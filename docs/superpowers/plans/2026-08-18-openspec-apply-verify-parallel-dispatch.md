# OpenSpec apply / verify 阶段内并行派发实施计划

> **供智能体执行者使用：** 必须使用子技能 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans`，逐项实施本计划。步骤使用复选框（`- [ ]`）跟踪。

**目标：** 把 apply / verify 阶段内并行写入 `AI_TOOLS_VERIFY_GATE_V1` 注入：有 `dispatching-parallel-agents` 则按该 skill 并行，没有则走官方串行默认；skill 每次运行时检测。

**架构：** 保持 official-first。入口仍依次派发一个 apply 子 Agent、一个 verify 子 Agent。只改 A/B 注入：阶段子 Agent 可在 skill 可用时派发实施者 / 调查者；缺 skill 时不得为并行再派工作者。新增 `AI_TOOLS_PARALLEL_DISPATCH_V1` 仅供存量检查识别旧注入，不表示 Superpowers 已安装。

**技术栈：** Markdown、Cursor Agent Skills、OpenSpec 官方 command/skill、ripgrep。

## 全局约束

- OpenSpec 相关正文全部使用简体中文。
- 不在本仓库生成、复制或跟踪 OpenSpec 官方 command/skill。
- 不把 `dispatching-parallel-agents` 步骤全文抄进注入。
- 不新增 `.cursor/agents` 或 `.cursor/rules`。
- 不改 `tasks.md` schema，不为并行强制 git worktree。
- 只改 apply/verify 的 A/B 注入；C 节 sync/archive 保持不变。
- 继续使用唯一幂等块标记 `AI_TOOLS_VERIFY_GATE_V1`。
- apply 委派标记固定为 `AI_TOOLS_DELEGATED_APPLY_V1`。
- verify 委派标记固定为 `AI_TOOLS_DELEGATED_VERIFY_V1`。
- 并行开关标记固定为 `AI_TOOLS_PARALLEL_DISPATCH_V1`；该标记不表示 Superpowers 已安装。
- skill 是否可用在每次 apply / verify 运行时判定，不在注入替换时钉死。
- 后续安装 Superpowers 无需再次替换注入。
- 保留最多 3 轮修复复验、工作区指纹和 sync/archive 门禁。
- delegated 判定只读取父 Agent 或用户下发的提示文本；规则正文中的标记字面量不参与判定。
- 未经用户明确要求不创建 Git commit。
- apply 工作者标记固定为 `AI_TOOLS_WORKER_APPLY_V1`；verify 工作者标记固定为 `AI_TOOLS_WORKER_VERIFY_V1`。
- skill 是否可用只认本会话可用 skills 列表；磁盘或插件缓存中的 `SKILL.md` 不足以为可用。

## 审查修订（2026-08-18）

Task 1 正文里的旧 A/B 片段已被代码审查修正。实施时以 `docs/ai-tools-integration.md` 当前 A/B 注入为准，不得把「或能读到对应 SKILL.md」写回注入。关键增量：

- 身份判定增加工作者标记，且必须排在「无阶段委派标记即入口」之前。
- 并行规则写入阶段子 Agent 步骤内部，不得先执行官方主体再读并行小节。
- 重叠定义为同一相对路径被两名及以上工作者改动；不能安全重做则停止并返回入口。
- 工作者不得写 git 索引 / HEAD。
- `STALE` 还要求 apply 含 `AI_TOOLS_WORKER_APPLY_V1`、verify 含 `AI_TOOLS_WORKER_VERIFY_V1`。

---

### Task 1：替换 A/B 注入并扩展 STALE 检查

**文件：**
- 修改：`docs/ai-tools-integration.md` A 节注入（约 271–287 行）
- 修改：`docs/ai-tools-integration.md` B 节注入（约 296–327 行）
- 修改：`docs/ai-tools-integration.md` 存量检查脚本及 `STALE` 说明（约 347–387 行）

**接口：**
- 产生：并行开关标记 `AI_TOOLS_PARALLEL_DISPATCH_V1`
- 保持：`AI_TOOLS_VERIFY_GATE_V1`、`AI_TOOLS_DELEGATED_APPLY_V1`、`AI_TOOLS_DELEGATED_VERIFY_V1`
- 消费：设计 `docs/superpowers/specs/2026-08-18-openspec-apply-verify-parallel-dispatch-design.md`

- [ ] **Step 1：建立旧行为回归检查**

运行：

```bash
rg -n '不得再次派发 apply 或 verify 子 Agent|不得再次派发 verify 子 Agent' \
  docs/ai-tools-integration.md
```

预期：实施完成后这两处旧禁令应变为「阶段子 Agent」表述，或被阶段内并行小节覆盖；若本步仍命中旧句，后续步骤必须改掉。

- [ ] **Step 2：替换 Apply 注入片段**

将 A 节代码块整段替换为：

```markdown
<!-- AI_TOOLS_VERIFY_GATE_V1 -->
## Apply 子 Agent 实施与强制验证

若当前会话已按本节派发过 apply 子 Agent，本节视为已执行，不得因 command 与 skill 同处一个上下文而重复派发。入口 Agent 仍负责等待 apply 子 Agent、在其成功后派发并等待 verify 子 Agent，以及检查 Verify 门禁和工作区指纹，但不得执行官方 apply 主体。

在执行任何 apply 主体步骤前，只检查父 Agent 或用户下发给本次任务的提示文本是否显式包含委派标记；本规则正文中出现的标记字符串不计入判定：

1. 若父 Agent 或用户下发的提示文本未显式包含 `AI_TOOLS_DELEGATED_APPLY_V1`，当前 Agent 是入口编排者，不得直接实施：
   - 派发一个子 Agent，在任务中加入 `AI_TOOLS_DELEGATED_APPLY_V1`，要求其使用 `openspec-apply-change` skill 实施当前 change，且不得派发 apply 或 verify 阶段子 Agent；
   - 等待 apply 子 Agent 返回；失败或阻塞时立即停止，不得启动 verify；
   - apply 成功后派发另一个独立子 Agent，在任务中加入 `AI_TOOLS_DELEGATED_VERIFY_V1`，要求其使用 `openspec-verify-change` skill 执行 verify；
   - 等待 verify 子 Agent 返回，再检查唯一 Verify 门禁及当前工作区指纹。
2. 若父 Agent 或用户下发的提示文本显式包含 `AI_TOOLS_DELEGATED_APPLY_V1`，当前 Agent 是 apply 子 Agent：直接执行官方 apply 主体，针对完整实现 diff 完成首次代码审查并记账，不得再次派发 apply 或 verify 阶段子 Agent；完成后把结果或阻塞返回入口 Agent。
3. 仅当 Verify 门禁为“状态：通过、阻塞项：无”且指纹匹配时，入口 Agent 才可结束 apply 并建议 sync 或 archive。
4. Verify 门禁缺失、状态未通过、存在阻塞、指纹不匹配或 verify 子 Agent 失败时，入口 Agent 不得宣告 apply 完成；change 保持 active，必须报告具体阻塞原因，且不得建议 sync 或 archive。

### 阶段内并行（AI_TOOLS_PARALLEL_DISPATCH_V1）

apply 与 verify 两个阶段必须串行，不得对开。本节只约束 apply 子 Agent 内部。

每次执行官方 apply 主体前，仅当本会话可用 skills 列表中存在名为 `dispatching-parallel-agents` 的 skill 时才读取并遵循；不得因本规则正文出现该 skill 名、也不得因磁盘或插件缓存中能读到 `SKILL.md` 而判定为可用。

- 找得到：读取并遵循该 skill，仅对无共享状态、不会改同一文件或同一制品、互不依赖的独立 task 域，在同一轮派发多个实施者子 Agent。实施者不得再派发 apply 或 verify 阶段子 Agent，也不得勾选 `tasks.md`。实施者返回后，apply 子 Agent 检查 diff 是否重叠；重叠则由 apply 子 Agent 串行重做冲突项。只有 apply 子 Agent 勾选 `tasks.md`。全部 task 结束后仍由 apply 子 Agent 对完整实现 diff 做首次代码审查。
- 找不到：按官方逐项循环由 apply 子 Agent 自己实施；不得为并行派发实施者，不得猜测、不得联网安装该 skill。
- 共享状态、会改同一文件或同一制品、修 A 可能带上 B、或拿不准时：不并行。
```

入口派发句必须写「不得派发 apply 或 verify **阶段**子 Agent」，以便 apply 子 Agent 在 skill 可用时派发实施者。

- [ ] **Step 3：扩展 Verify 注入片段**

将 B 节代码块整段替换为：

```markdown
<!-- AI_TOOLS_VERIFY_GATE_V1 -->
## Verify 入口编排与验证阻塞修复闭环

若当前会话已派发过 verify 子 Agent（无论由本节还是 Apply 节触发），本节视为已执行，不得因 command 与 skill 同处一个上下文而重复派发。入口 Agent 只等待该子 Agent 并读取、汇报最终门禁，不得执行官方 verify 主体。

在执行任何 verify 主体步骤前，只检查父 Agent 或用户下发给本次任务的提示文本是否显式包含委派标记；本规则正文中出现的标记字符串不计入判定：

1. 若父 Agent 或用户下发的提示文本未显式包含 `AI_TOOLS_DELEGATED_VERIFY_V1`，当前 Agent 是入口编排者，不得直接验证：派发一个子 Agent，在任务中加入该标记，要求其使用 `openspec-verify-change` skill 执行当前 change 的完整 verify；等待后读取并汇报最终门禁。
2. 若父 Agent 或用户下发的提示文本显式包含 `AI_TOOLS_DELEGATED_VERIFY_V1`，当前 Agent 是 verify 子 Agent：直接执行以下验证闭环，不得再次派发 verify 阶段子 Agent。
3. 子 Agent 按下方验证闭环中的正式阻塞条件处理；需要停止时把阻塞返回入口 Agent。

### 阶段内并行（AI_TOOLS_PARALLEL_DISPATCH_V1）

apply 与 verify 两个阶段必须串行，不得对开。本节只约束 verify 子 Agent 内部。

每次执行官方 verify 主体前，仅当本会话可用 skills 列表中存在名为 `dispatching-parallel-agents` 的 skill 时才读取并遵循；不得因本规则正文出现该 skill 名、也不得因磁盘或插件缓存中能读到 `SKILL.md` 而判定为可用。

- 找得到：读取并遵循该 skill，仅对只读、互不干扰的检查或独立失败域，在同一轮派发多个调查者子 Agent。调查者不得再派发 apply 或 verify 阶段子 Agent，不得写 `verification.md`，不得写门禁块，不得计算指纹。调查者返回后，verify 子 Agent 汇合结论、检查冲突并写入 `verification.md`。需要安全修复时，仅当修复域独立且无共享状态才可按该 skill 并行修改互不重叠的文件；否则由 verify 子 Agent 串行修复。每一轮修复后的完整复验、完整 diff 审查、门禁与指纹仍由 verify 子 Agent 串行收口。
- 找不到：由 verify 子 Agent 独自完成下方验证闭环；不得为并行派发调查者，不得猜测、不得联网安装该 skill。
- 共享状态、会改同一文件或同一制品、修 A 可能带上 B、或拿不准时：不并行。

### 验证闭环

1. 实际执行验证并检查代码、测试及 change 制品。发现可安全修复的阻塞项时，verify 子 Agent 直接修复，并重新运行受影响的检查和完整 verify。
2. 最多执行 3 轮“验证—修复—重新验证”。同一阻塞连续两轮无进展时提前停止。
3. 遇到需要用户决策、缺少权限或凭据、外部服务故障、破坏性操作，或超出当前 change 范围的修改时，不得自行处理，停止并报告。
4. 将每轮实际命令、结果、修复内容和剩余风险写回当前 change 的 `verification.md`。verify 子 Agent 每次修改代码后，必须针对修复后的完整 diff 重新执行代码审查，并更新 `verification.md` 中的审查范围与结论；存在未处理的 Critical/Important 时不得通过。
5. 全部适用检查已执行、无失败或待执行项，且无未处理的 Critical/Important 与其它阻塞项时，在 `verification.md` 末尾新增或替换以下唯一门禁块，先将验证指纹写为 `PENDING`：

   <!-- AI_TOOLS_VERIFICATION_RESULT_V1_START -->
   ## Verify 门禁
   - 状态：通过
   - 阻塞项：无
   - 验证指纹：PENDING
   <!-- AI_TOOLS_VERIFICATION_RESULT_V1_END -->

6. 运行 `python3 .cursor/scripts/openspec-verification-fingerprint.py "<当前 change 的 verification.md 路径>"`，将 `PENDING` 替换为命令输出的完整 SHA-256。替换后再次运行该命令，输出必须与记录值一致。
7. 未通过时同样新增或替换该门禁块，将状态写为 `阻塞`，在“阻塞项”中列出具体问题，并将验证指纹写为 `无效`；不得保留旧的“通过”结果。

单独运行 `/opsx-verify` 时也执行以上步骤；其最终指纹一致性仍由后续 sync/archive 入口强制重新计算并复核。
```

不得改动验证闭环 1–7 的轮次、指纹命令或门禁块格式。C 节注入一字不改。

- [ ] **Step 4：扩展存量检查脚本**

将 5.1 节检查脚本中 `count` 为 `1` 的分支替换为同时检查委派标记与并行标记：

```bash
      required=""
      case "$file" in
        *opsx-apply.md|*openspec-apply-change/SKILL.md)
          required="AI_TOOLS_DELEGATED_APPLY_V1 AI_TOOLS_PARALLEL_DISPATCH_V1 AI_TOOLS_WORKER_APPLY_V1"
          ;;
        *opsx-verify.md|*openspec-verify-change/SKILL.md)
          required="AI_TOOLS_DELEGATED_VERIFY_V1 AI_TOOLS_PARALLEL_DISPATCH_V1 AI_TOOLS_WORKER_VERIFY_V1"
          ;;
      esac
      stale_missing=""
      for marker in $required; do
        if ! rg -q --fixed-strings "$marker" "$file"; then
          stale_missing="$marker"
          break
        fi
      done
      if [ -n "$stale_missing" ]; then
        echo "STALE     $file (missing $stale_missing)"
      else
        echo "OK        $file"
      fi
```

脚本其余部分（`command -v rg`、8 文件循环、`MISSING` / `DUPLICATE` / `NOFILE`）保持不变。sync/archive 的 `required` 仍为空，缺并行标记不得标 `STALE`。

将脚本后的说明改为：

```text
`MISSING` 表示尚无增强块，只向这些文件追加当前 A/B/C 节的对应完整文本。`STALE` 表示文件只有一个 `AI_TOOLS_VERIFY_GATE_V1` 标记，但 apply/verify 块缺少当前委派标记或 `AI_TOOLS_PARALLEL_DISPATCH_V1`；必须用当前 A/B 节的完整注入文本替换旧块，不得再次追加。缺少 Superpowers 或缺少 `dispatching-parallel-agents` 不得标为 `STALE`。出现 `DUPLICATE` 时先清理重复块，再按当前文本保留唯一一块。`NOFILE` 表示官方文件不存在，应先恢复官方生成层。若官方模板升级后结构发生变化，应先人工确认追加位置是否仍适用。该同一脚本也直接验收 apply 两个文件的 APPLY 与并行标记、verify 两个文件的 VERIFY 与并行标记，无需维护第二套检查逻辑。
```

- [ ] **Step 5：验收注入与检查脚本**

运行：

```bash
rg -n 'AI_TOOLS_PARALLEL_DISPATCH_V1|dispatching-parallel-agents|阶段子 Agent|不得联网安装|只有 apply 子 Agent 勾选' \
  docs/ai-tools-integration.md

rg -n 'Dispatch multiple agents in parallel|Core principle: Dispatch one agent per independent problem domain' \
  docs/ai-tools-integration.md

rg -n 'AI_TOOLS_PARALLEL_DISPATCH_V1' docs/ai-tools-integration.md
```

预期：

- 第一条在 A 节、B 节和存量说明中均有命中；
- 第二条无命中（未抄 skill 正文）；
- 第三条至少出现在 A 注入、B 注入和检查脚本的 apply/verify 分支中；
- C 节代码块仍不含 `AI_TOOLS_PARALLEL_DISPATCH_V1`。

- [ ] **Step 6：提交（仅当用户要求提交时）**

```bash
git add docs/ai-tools-integration.md
git commit -m "$(cat <<'EOF'
docs(openspec): 在 verify 门禁注入中加入阶段内并行开关

apply/verify 子 Agent 在运行时检测 dispatching-parallel-agents；缺 skill 时回退官方串行，存量检查将缺少并行标记视为 STALE。
EOF
)"
```

---

### Task 2：同步接入文档叙述、升级说明与 FAQ

**文件：**
- 修改：`docs/ai-tools-integration.md:31-47`（1.1）
- 修改：`docs/ai-tools-integration.md:404-408`（5.3）
- 修改：`docs/ai-tools-integration.md:484-495`（6.3）
- 修改：`docs/ai-tools-integration.md:509-541`（7.1 / 7.2）
- 修改：`docs/ai-tools-integration.md:548-565`（验收清单）
- 修改：`docs/ai-tools-integration.md:577-585`（FAQ）

**接口：**
- 消费：Task 1 的注入语义与 `AI_TOOLS_PARALLEL_DISPATCH_V1`
- 产生：接入文档中与注入一致的运行时开关说明

- [ ] **Step 1：更新 1.1 能力摘要**

将 1.1 中「入口 Agent 先派发 apply 子 Agent…」那一条改为：

```markdown
- 入口 Agent 先派发 apply 子 Agent；成功后再派发独立 verify 子 Agent。单独运行 `/opsx-verify` 时，入口 Agent 同样派发 verify 子 Agent。apply / verify 阶段仍串行。阶段子 Agent 每次运行时检测当前会话能否用到 `dispatching-parallel-agents`：能用到则按该 skill 对独立域并行派发实施者 / 调查者；用不了则按官方默认串行，不得为并行再派工作者。后续安装该 skill 无需再次替换注入。verify 子 Agent 仅直接修复可安全、在当前 change 范围内且无需用户决策的阻塞并重新验证（最多 3 轮）；遇正式规则列出的其它情况停止并返回入口 Agent。verification 完成且无阻塞项后，才可进入 sync 或 archive。
```

- [ ] **Step 2：更新 5.3 与 6.3**

5.3 中「入口 Agent 先派发 apply 子 Agent…」段落后追加一句：

```markdown
阶段内并行由运行时是否能用到 `dispatching-parallel-agents` 决定；缺少该 skill 时行为与仅派发阶段子 Agent 的串行路径相同。
```

6.3 表格「apply 结束后强制独立子 Agent verify…」的「迁移后」列改为：

```markdown
入口 Agent 先派发 apply 子 Agent，成功后再派发独立 verify 子 Agent；单独运行 `/opsx-verify` 时也由入口 Agent 派发 verify 子 Agent。阶段内是否并行取决于运行时能否用到 `dispatching-parallel-agents`（按 5.1 节追加验证闭环、委派标记与并行开关标记）
```

- [ ] **Step 3：更新 7.1 / 7.2 与验收清单**

7.1 / 7.2 中处理 `STALE` 的句子改为明确：旧 V1 块若缺 `AI_TOOLS_PARALLEL_DISPATCH_V1` 也是 `STALE`，用当前 A/B 节完整文本替换。

验收清单中 5.1 脚本那一条改为：

```markdown
- [ ] 运行 5.1 节同一脚本，8 个文件均输出 `OK`，没有 `MISSING`、`STALE`、`DUPLICATE` 或 `NOFILE`；其中 apply command/skill 含 `AI_TOOLS_DELEGATED_APPLY_V1` 与 `AI_TOOLS_PARALLEL_DISPATCH_V1`，verify command/skill 含 `AI_TOOLS_DELEGATED_VERIFY_V1` 与 `AI_TOOLS_PARALLEL_DISPATCH_V1`。
```

- [ ] **Step 4：新增 FAQ**

在「接入后官方 verify 变「弱」了？」之后新增：

```markdown
### 安装增强规则后还要再装 Superpowers 吗？注入要不要再替换？

不必。`AI_TOOLS_PARALLEL_DISPATCH_V1` 只表示注入已包含阶段内并行规则，不表示 Superpowers 已安装。每次 apply / verify 运行时检测当前会话能否用到 `dispatching-parallel-agents`：没有则走官方串行默认；之后自行安装 Superpowers，无需再次替换注入，下一轮即可启用阶段内并行。卸掉后自动回到串行。只有注入文本过期（5.1 节脚本报 `STALE`）才需要用当前 A/B 节替换。
```

- [ ] **Step 5：验收叙述一致性**

运行：

```bash
rg -n '必须已有 Superpowers|安装注入时必须|替换后才启用内部并行' \
  docs/ai-tools-integration.md

rg -n '后续安装|运行时|AI_TOOLS_PARALLEL_DISPATCH_V1' \
  docs/ai-tools-integration.md
```

预期：第一条无命中；第二条在 1.1、FAQ、验收清单或存量说明中有命中。

- [ ] **Step 6：提交（仅当用户要求提交时）**

```bash
git add docs/ai-tools-integration.md
git commit -m "$(cat <<'EOF'
docs(openspec): 说明阶段内并行是运行时开关

接入摘要、升级说明与 FAQ 写明缺 skill 则串行，后续安装 Superpowers 无需再替换注入。
EOF
)"
```

---

### Task 3：同步 README 与场景工作流

**文件：**
- 修改：`README.md:119-147`
- 修改：`docs/ai-sdd-workflow.md:104-114`
- 修改：`docs/ai-sdd-workflow.md:197-200`

**接口：**
- 消费：Task 1 / Task 2 的运行时开关语义
- 产生：对外文档与注入一致的能力摘要

- [ ] **Step 1：更新 README 接入步骤与标准主线**

将「增强规则同时提供 apply 子 Agent 派发…」一段改为：

```markdown
   command/skill 文件幂等追加 `AI_TOOLS_VERIFY_GATE_V1` 规则。增强规则同时提供
   apply 子 Agent 派发、独立 verify 子 Agent 派发、防递归标记（
   `AI_TOOLS_DELEGATED_APPLY_V1`、`AI_TOOLS_DELEGATED_VERIFY_V1`）与阶段内并行开关
   （`AI_TOOLS_PARALLEL_DISPATCH_V1`）：apply 时入口 Agent 先派发 apply 子 Agent，
   成功后再派发 verify 子 Agent；用户单独运行 `/opsx-verify` 时，入口 Agent 同样
   派发 verify 子 Agent。阶段子 Agent 每次运行时检测 `dispatching-parallel-agents`：
   能用到则对独立域并行派发工作者；用不了则按官方默认串行。后续安装该 skill
   无需再次替换注入。未安装增强规则时，这些派发行为不成立。仅复制 schema 不会
   自动获得这些流转门禁与子 Agent 编排。
```

标准主线代码块后追加：

```markdown
apply 与 verify 两个阶段始终串行。阶段内并行不是接入时开关：当前会话能用到
`dispatching-parallel-agents` 时由阶段子 Agent 按该 skill 派发工作者；否则与现网
串行路径相同。
```

- [ ] **Step 2：更新场景工作流约束**

将 `docs/ai-sdd-workflow.md` 中「安装 `AI_TOOLS_VERIFY_GATE_V1` 后，入口 Agent 负责编排…」那一条改为在现有句子后追加：

```markdown
  阶段内是否并行由每次运行时能否用到 `dispatching-parallel-agents` 决定；缺 skill
  时与仅派发阶段子 Agent 的串行行为相同，后续安装无需再替换注入。
```

「使用原则」中「apply 与单独 `/opsx-verify` 均由入口 Agent 派发子 Agent 执行」一句后追加「阶段内并行取决于运行时是否能用到 `dispatching-parallel-agents`」。

- [ ] **Step 3：验收对外文档**

运行：

```bash
rg -n 'AI_TOOLS_PARALLEL_DISPATCH_V1|dispatching-parallel-agents|运行时' \
  README.md docs/ai-sdd-workflow.md

rg -n '必须先安装 Superpowers|安装注入时必须已有' \
  README.md docs/ai-sdd-workflow.md docs/ai-tools-integration.md
```

预期：第一条均有命中；第二条无命中。

- [ ] **Step 4：提交（仅当用户要求提交时）**

```bash
git add README.md docs/ai-sdd-workflow.md
git commit -m "$(cat <<'EOF'
docs(openspec): 在 README 与工作流中同步阶段内并行开关

对外说明 apply/verify 阶段仍串行，阶段内并行随会话是否能用到 dispatching-parallel-agents 切换。
EOF
)"
```

---

### Task 4：对照设计做最终核对

**文件：**
- 只读：`docs/superpowers/specs/2026-08-18-openspec-apply-verify-parallel-dispatch-design.md`
- 只读：`docs/ai-tools-integration.md`
- 只读：`README.md`
- 只读：`docs/ai-sdd-workflow.md`

**接口：**
- 消费：设计文档「验证」与「非目标」清单
- 产生：无代码；本任务只确认覆盖

- [ ] **Step 1：按设计验证清单逐项搜索**

运行：

```bash
rg -n 'AI_TOOLS_PARALLEL_DISPATCH_V1|dispatching-parallel-agents|阶段子 Agent|不得联网安装|只有 apply 子 Agent 勾选|不得写 `verification.md`|运行时' \
  docs/ai-tools-integration.md README.md docs/ai-sdd-workflow.md

rg -n 'Core principle: Dispatch one agent per independent problem domain|Dispatch multiple agents in parallel' \
  docs/ai-tools-integration.md README.md docs/ai-sdd-workflow.md

rg -n '不得对开|两个阶段必须串行' docs/ai-tools-integration.md

rg -n 'AI_TOOLS_PARALLEL_DISPATCH_V1' docs/ai-tools-integration.md
```

预期：

- 注入含并行标记与 skill 名，不含 skill 正文步骤；
- apply 与 verify 阶段「不得对开」有明文；
- 并行标记出现在 A、B 与检查脚本，不出现在 C 节代码块；
- 文档写明运行时判定，且后续安装 Superpowers 无需再替换注入。

- [ ] **Step 2：确认非目标未被引入**

运行：

```bash
rg -n 'tasks.md schema|并行组|worktree|custom agent' \
  docs/ai-tools-integration.md README.md docs/ai-sdd-workflow.md
```

预期：无「为并行新增 tasks schema / 并行组 / 强制 worktree / 具名 custom agent」的实现表述。C 节仍不是子 Agent 执行。Verify 门禁仍不可用户确认绕过。

- [ ] **Step 3：提交（仅当用户要求提交时）**

若 Task 1–3 仍有未提交改动，一并提交；无改动则跳过。

```bash
git add docs/ai-tools-integration.md README.md docs/ai-sdd-workflow.md
git commit -m "$(cat <<'EOF'
docs(openspec): 完成 apply/verify 阶段内并行注入核对

对照设计确认运行时开关、STALE 语义与阶段串行边界均已写入接入文档。
EOF
)"
```
