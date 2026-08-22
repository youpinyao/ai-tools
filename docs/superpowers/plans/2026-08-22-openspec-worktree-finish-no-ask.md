# OpenSpec 隔离 worktree 禁止主动收尾询问实施计划

> **供智能体执行者使用：** 必须使用子技能 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans`，逐项实施本计划。步骤使用复选框（`- [ ]`）跟踪。未经用户明确要求不创建 Git commit。

**目标：** 各 OpenSpec 入口结束时不再询问隔离 worktree 怎么处理；默认留下 worktree；仅在用户本轮明确要求时才按既有安全步骤合并或清理。

**架构：** 保持 official-first。不跟踪官方生成物。改写 5.1 节 E 段触发条件，并把 A/B/C、D 中「结束时必须问」改为禁止主动问且可被 `STALE` 检测。权威正文仍只在 `docs/ai-tools-integration.md`。

**技术栈：** Markdown、Cursor Agent Skills、OpenSpec 官方 command/skill、ripgrep。

## 全局约束

- OpenSpec 相关正文全部使用简体中文。
- 不在本仓库生成、复制或跟踪 OpenSpec 官方 command/skill。
- 不修改 OpenSpec CLI 或 `evidence-driven` schema。
- 不改变 propose 起始 worktree 选择。
- 不改变 Verify 门禁语义。
- 不自动提交、合并或删除 worktree。
- 未经用户明确要求不创建 Git commit。
- 消费设计：`docs/superpowers/specs/2026-08-22-openspec-worktree-finish-no-ask-design.md`

## 文件结构

| 文件 | 职责 |
|------|------|
| `docs/superpowers/specs/2026-08-22-openspec-worktree-finish-no-ask-design.md` | 已批准设计（已写入） |
| `docs/ai-tools-integration.md` | 权威注入正文、检查脚本、FAQ |
| `README.md` | 安装与标准主线 |
| `docs/ai-sdd-workflow.md` | 场景说明 |
| `docs/openspec-upgrade-plan.md` | 升级清单 |
| `docs/superpowers/specs/2026-08-21-openspec-worktree-finish-design.md` | 文首标明触发条件已被取代 |
| `docs/superpowers/specs/2026-08-18-openspec-propose-worktree-choice-design.md` | 非目标改为指向按需收尾 |

不修改：`openspec/schemas/`、`.cursor/skills/openspec-update-change-from-code/`、`.gitignore`。

---

### Task 1：改写 5.1 节 A/B/C/D/E 注入与检查

**文件：**
- 修改：`docs/ai-tools-integration.md`

- [ ] **Step 1：A/B/C 去掉结束询问，加入 `AI_TOOLS_VERIFY_GATE_NO_FINISH_ASK_V1`**

Apply 第 6 条替换为：入口结束时不得询问隔离 worktree 如何处理（`AI_TOOLS_VERIFY_GATE_NO_FINISH_ASK_V1`）；仅当本轮用户明确要求合并或清理时，才按同文件收尾节执行。实施者与 apply 子 Agent 不得询问、不得合并或删除。

Verify 与 Sync/Archive 末句做同样替换。

8 文件检查：apply/verify 的 required 追加该标记；sync/archive 的 required 设为该标记。`STALE` 说明同步更新。

- [ ] **Step 2：D 节禁止结束询问**

失败处理与收口句改为：结束时不得询问（`AI_TOOLS_PROPOSE_WORKTREE_NO_FINISH_ASK_V1`）；可报告路径仍在；仅本轮明确要求才执行收尾节。propose 2 文件 required 追加该标记。`STALE` 说明同步更新。

- [ ] **Step 3：E 节改为禁止主动问、按需执行**

标题与触发段使用 `AI_TOOLS_WORKTREE_FINISH_NO_ASK_V1`。删除「准备结束回复时必须先判断是否询问」。保留 SCOPE 与 MERGE_CLEANUP。询问选项改为：无明确要求则跳过；含糊要求不弹菜单；明确要求且干净则直接执行。10 文件检查 required 改为 `NO_ASK` + `SCOPE` + `MERGE_CLEANUP`。合成检查预期改为 `STALE (missing AI_TOOLS_WORKTREE_FINISH_NO_ASK_V1)`。

- [ ] **Step 4：第 1 节、5.3、6.3、7.1/7.2、第 8 节、FAQ 与叙述对齐**

入口结束必须问 → 不得主动问、默认留下、按需执行。试跑改为：propose 结束后不得出现收尾菜单。

- [ ] **Step 5：对照扫描**

运行：

```bash
rg -n '结束回复时必须|必须先询问是否合并|ASK_ALWAYS_V1' \
  docs/ai-tools-integration.md README.md docs/ai-sdd-workflow.md docs/openspec-upgrade-plan.md
```

预期：接入/用户文档中不再要求各阶段结束时询问；`ASK_ALWAYS_V1` 只作为旧块 `STALE` 识别出现。

---

### Task 2：同步 README、场景、升级清单与历史设计

- [ ] **Step 1：README** 安装步骤与标准主线去掉「跑完后询问合并」；改为默认留下、用户明确要求才收尾。
- [ ] **Step 2：`docs/ai-sdd-workflow.md`** 闭环约束与场景 1/6/7、sync 旁路、使用原则对齐。
- [ ] **Step 3：`docs/openspec-upgrade-plan.md`** 5.3 预期改为禁止主动询问、按需收尾。
- [ ] **Step 4：2026-08-21 文首标明触发条件被 2026-08-22 取代；2026-08-18 非目标改为指向按需收尾。**

---

### Task 3：标记与检查脚本对照

运行设计验收用的合成检查（E 块 `NO_ASK` 为 OK，仅 `ASK_ALWAYS` 为 STALE；D 缺 `NO_FINISH_ASK` 为 STALE；sync 缺 `VERIFY_GATE_NO_FINISH_ASK` 为 STALE）。确认 schema 与官方 propose 路径仍未被跟踪。

## 自我审查

1. **规格覆盖：** 禁止主动问、按需执行、A/B/C/D STALE 标记、E 标记替换、文档落点分别由 Task 1–2 覆盖。
2. **占位符：** 无 TBD。
3. **名称一致：** `AI_TOOLS_WORKTREE_FINISH_NO_ASK_V1`、`AI_TOOLS_VERIFY_GATE_NO_FINISH_ASK_V1`、`AI_TOOLS_PROPOSE_WORKTREE_NO_FINISH_ASK_V1`。
