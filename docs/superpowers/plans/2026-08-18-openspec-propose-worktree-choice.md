# OpenSpec propose worktree 选择实施计划

> **供智能体执行者使用：** 必须使用子技能 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans`，逐项实施本计划。步骤使用复选框（`- [ ]`）跟踪。

**目标：** 让每次 `/opsx-propose` 与 `openspec-propose` skill 在写入任何 change 制品前，询问用户是否使用隔离 worktree，并按选择准备工作区。

**架构：** 保持 official-first。不跟踪官方 propose 生成物，也不改 schema。向目标项目的官方 propose command/skill 追加独立标记块 `AI_TOOLS_PROPOSE_WORKTREE_V1`；接入文档维护唯一权威正文，并提供与 5.1 节同构的 `OK` / `MISSING` / `STALE` / `DUPLICATE` / `NOFILE` 检查。

**技术栈：** Markdown、Cursor Agent Skills、OpenSpec 官方 command/skill、ripgrep、git worktree。

## 全局约束

- OpenSpec 相关正文全部使用简体中文。
- 不在本仓库生成、复制或跟踪 OpenSpec 官方 command/skill。
- 不修改 OpenSpec CLI 或 `evidence-driven` schema。
- 不把官方 propose 文件纳入 Git 跟踪。
- 不新增 `.cursor/rules`、全局 Cursor rule 或独立 propose skill。
- 不改变 apply、verify、sync、archive 的既有 `AI_TOOLS_VERIFY_GATE_V1` 语义。
- propose 增强使用独立标记 `AI_TOOLS_PROPOSE_WORKTREE_V1`，不得并入 verify 门禁块。
- 每次 propose 都必须询问，不得因工作区干净或已处于 worktree 而跳过。
- 不得自动替用户选择 worktree。
- 不得静默从 worktree 失败退回当前工作区。
- 不自动提交、合并或删除 worktree 中的变更。
- 未经用户明确要求不创建 Git commit。

## 文件结构

| 文件 | 职责 |
|------|------|
| `docs/ai-tools-integration.md` | 权威注入正文、状态检查脚本、接入/升级/验收步骤 |
| `README.md` | 安装步骤与标准主线提示 propose 起始询问 |
| `docs/ai-sdd-workflow.md` | 场景说明：propose 开始前选择工作区 |
| `docs/openspec-upgrade-plan.md` | 官方升级时复核 propose 注入点 |
| `docs/superpowers/specs/2026-08-18-openspec-propose-worktree-choice-design.md` | 已批准设计；本计划实现它，不改设计文件 |

不修改：`openspec/schemas/`、`.cursor/skills/openspec-update-change-from-code/`、`.gitignore`、`docs/graphify-integration.md`。

---

### Task 1：写入 propose worktree 权威注入与检查脚本

**文件：**
- 修改：`docs/ai-tools-integration.md` 第 5.1 节末尾（约 419–421 行，检查脚本说明之后、5.2 之前）

**接口：**
- 产生：标记 `AI_TOOLS_PROPOSE_WORKTREE_V1`
- 产生：内嵌识别标记 `AI_TOOLS_PROPOSE_WORKTREE_ASK_ALWAYS_V1`、`AI_TOOLS_PROPOSE_WORKTREE_INDEPENDENT_V1`、`AI_TOOLS_PROPOSE_WORKTREE_WORKSPACE_ROOT_V1`、`AI_TOOLS_PROPOSE_WORKTREE_NO_DOWNGRADE_V1`
- 产生：目标文件 `.cursor/commands/opsx-propose.md`、`.cursor/skills/openspec-propose/SKILL.md`
- 保持：`AI_TOOLS_VERIFY_GATE_V1` 的 8 文件检查脚本一字不改
- 消费：设计 `docs/superpowers/specs/2026-08-18-openspec-propose-worktree-choice-design.md`

- [ ] **Step 1：确认 5.1 节插入点仍在 C 节检查说明之后**

运行：

```bash
rg -n '^这是对官方生成物的项目级追加|^### 5.2 已有 active change' \
  docs/ai-tools-integration.md
```

预期：先出现「这是对官方生成物的项目级追加」，紧接着是 `### 5.2`。D 节必须插在这两行之间。

- [ ] **Step 2：在 5.1 节末尾、5.2 之前插入 D 节**

将下面整段插入「这是对官方生成物的项目级追加……」之前。不要改 A/B/C 注入正文，也不要改现有 8 文件检查脚本。注入正文内部不要再套一层 ` ```bash ` 围栏，以免提前结束 `docs/ai-tools-integration.md` 里与 A/B/C 相同的 ` ```markdown ` 代码块。

````markdown
#### D. Propose：起始 worktree 选择

向以下两个文件追加或替换为以下内容（`STALE` 时替换旧块）：

- `.cursor/commands/opsx-propose.md`
- `.cursor/skills/openspec-propose/SKILL.md`

command 与 skill 使用同一规则正文；仅当官方文件标题层级会与本节冲突时，才把本节 `##` / `###` 降一级，不得改语义。

```markdown
<!-- AI_TOOLS_PROPOSE_WORKTREE_V1 -->
## Propose 起始工作区选择（AI_TOOLS_PROPOSE_WORKTREE_ASK_ALWAYS_V1）

在执行任何官方 propose 主体步骤前，必须先完成工作区选择。不得创建 change、不得分配 change 名称、不得写入 `openspec/changes/` 下任何制品，也不得运行 `openspec new change`。

无论工作区是否干净、是否已经处于 linked worktree，每次 `/opsx-propose` 或 `openspec-propose` skill 调用都必须询问，不得根据状态跳过，不得替用户选择。

向用户说明并提供两个选项：

- `使用隔离 worktree`：新建独立 worktree 后再继续官方 propose。每次 propose 使用尚未占用的新路径和新分支，即使当前已处于 linked worktree 也不得复用。新分支默认基于当前 `HEAD`；若当前已在某个 propose worktree 且该分支已有提交，新 change 会带上这些提交，工作区独立不等于 Git 历史独立。当前工作区的未提交改动不会自动出现在新 worktree。必须先把本会话工作区根目录切到新 worktree，切不过去则停止。
- `在当前工作区继续`：保留当前目录和分支，继续官方 propose。

用户取消、拒绝回答或未明确选择时立即停止，不得继续官方 propose。

### 选择当前工作区

保留当前目录和分支，进入官方 propose。不得创建 worktree，不得切换分支。

### 选择隔离 worktree（AI_TOOLS_PROPOSE_WORKTREE_INDEPENDENT_V1）

1. 先检测当前 Git 布局，且必须排除 submodule 误判。依次取：
   `GIT_DIR=$(cd "$(git rev-parse --git-dir)" && pwd -P)`；
   `GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" && pwd -P)`；
   `SUPERPROJECT=$(git rev-parse --show-superproject-working-tree 2>/dev/null || true)`；
   `CURRENT_WORKTREE=$(cd "$(git rev-parse --show-toplevel)" && pwd -P)`。
2. 若 `SUPERPROJECT` 非空：当前是 submodule，按普通仓库处理，不得当作 linked worktree。
3. 每次选择隔离 worktree 都必须新建独立 worktree（尚未占用的新路径 + 新分支），不得复用当前目录或任一已有 worktree，不得把本次 change 写入已有 worktree。普通 checkout、submodule、已处于 linked worktree 均适用本条。
4. 解析主工作区路径：`MAIN_WORKTREE=$(git worktree list --porcelain | awk '/^worktree / {print substr($0,10); exit}')`。若无法解析主工作区或当前工作区，立即停止并报告，不得继续。
5. 任何新建路径都必须是绝对路径，经 `pwd -P` 后：不得等于 `$CURRENT_WORKTREE`，也不得位于 `$CURRENT_WORKTREE/` 之下（禁止嵌套）。已处于 linked worktree（`GIT_DIR != GIT_COMMON` 且 `SUPERPROJECT` 为空）时仍须按第 3 条新建，不得因「已在 worktree 中」而跳过。
6. 优先使用运行环境已有的原生 worktree 能力（例如 `EnterWorktree`、`WorktreeCreate`、`/worktree`）。原生能力只需满足：新路径、新分支、不复用、不嵌套（第 3、5 条）。不要求落在主工作区 `.worktrees/` 或其它项目内父目录；仓库外的托管目录可以。若没有原生能力，或原生结果不满足第 3、5 条，改用下方手工 `git worktree`，不得因此停止。
7. 手工 `git worktree` 时：
   - 目录锚定主工作区，不得相对当前 CWD。优先顺序（均相对 `$MAIN_WORKTREE`）：项目明确约定 > 已有 `.worktrees/` > 已有 `worktrees/` > 默认 `.worktrees/`。两者都存在时用 `.worktrees/`。
   - 必须先运行 `git -C "$MAIN_WORKTREE" check-ignore -q <相对主工作区的目录>`；未忽略则立即停止并报告，不得在未忽略目录创建 worktree，不得擅自修改 `.gitignore`。
   - 使用尚未占用的临时工作分支和绝对路径，例如 `NEW_PATH="$MAIN_WORKTREE/.worktrees/openspec/propose-<YYYYMMDD-HHMMSS>"`。创建前断言 `$NEW_PATH` 满足第 5 条。最终 change 名称仍由官方 propose 流程确定，不得预先用 change 名称命名分支。
   - 基于当前 `HEAD` 创建：`git worktree add -b "<branch>" "$NEW_PATH" HEAD`。不得把未提交改动自动搬运到新 worktree。
   - 不得使用 `git reset --hard`、强制删除分支、`git worktree remove --force` 或其它破坏性清理。

### 进入目标 worktree（AI_TOOLS_PROPOSE_WORKTREE_WORKSPACE_ROOT_V1）

创建完成后必须把**本会话的工作区根目录**切到新 worktree，优先使用原生切换能力（例如 `EnterWorktree`）。仅在 shell 中 `cd`、但编辑器或文件工具仍写入旧根目录，视为未切换成功。

进入官方 propose、执行 setup / 基线检查、或写入任何制品前，确认工作区根（当前 Cursor workspace / 打开的项目根，经 `pwd -P`）等于新 worktree 路径（经 `pwd -P`）。切不过去：立即停止并报告新旧路径，不得在旧 worktree 继续 propose，不得写入 `openspec/changes/`。

切换确认后，执行项目可识别的基础 setup：存在 `package.json` 则安装依赖；存在 `Cargo.toml` 则构建；存在 `requirements.txt` / `pyproject.toml` / `go.mod` 则按对应工具安装。没有这些文件则跳过该项。

再执行项目可识别的基线检查：仓库已有明确测试命令时才运行。没有可识别测试命令则跳过。setup 或基线检查失败时暂停并报告原因；在用户明确同意继续前，不得进入官方 propose。

### 失败处理（AI_TOOLS_PROPOSE_WORKTREE_NO_DOWNGRADE_V1）

用户取消、worktree 创建失败、目录未被忽略、sandbox 拒绝、会话工作区未切到新 worktree、setup 失败或基线检查失败且用户未明确同意继续时，立即停止并报告原因；不得静默退回当前工作区继续 propose。所有阻塞必须发生在 OpenSpec change 和制品创建之前。

准备完成后，才进入官方 propose 主体。
```

首次接入、追加或替换前，以及每次 `openspec update` 或 ai-tools 自定义层升级后，在目标项目根目录运行：

```bash
command -v rg >/dev/null || {
  echo 'ERROR: ripgrep (rg) is required'
  exit 1
}

for file in \
  .cursor/commands/opsx-propose.md \
  .cursor/skills/openspec-propose/SKILL.md
do
  if [ ! -f "$file" ]; then
    echo "NOFILE    $file"
    continue
  fi
  count="$( { rg -o --fixed-strings 'AI_TOOLS_PROPOSE_WORKTREE_V1' "$file" || true; } | wc -l | tr -d ' ')"
  case "$count" in
    0) echo "MISSING   $file" ;;
    1)
      required="AI_TOOLS_PROPOSE_WORKTREE_ASK_ALWAYS_V1 AI_TOOLS_PROPOSE_WORKTREE_INDEPENDENT_V1 AI_TOOLS_PROPOSE_WORKTREE_WORKSPACE_ROOT_V1 AI_TOOLS_PROPOSE_WORKTREE_NO_DOWNGRADE_V1"
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
      ;;
    *) echo "DUPLICATE $file ($count markers)" ;;
  esac
done
```

`MISSING` 表示尚无增强块，只向这两个文件追加当前 D 节完整文本。`STALE` 表示文件只有一个 `AI_TOOLS_PROPOSE_WORKTREE_V1` 标记，但缺少 `AI_TOOLS_PROPOSE_WORKTREE_ASK_ALWAYS_V1`、`AI_TOOLS_PROPOSE_WORKTREE_INDEPENDENT_V1`、`AI_TOOLS_PROPOSE_WORKTREE_WORKSPACE_ROOT_V1` 或 `AI_TOOLS_PROPOSE_WORKTREE_NO_DOWNGRADE_V1`（含仍只有旧标记 `AI_TOOLS_PROPOSE_WORKTREE_REUSE_V1` 的块）；必须用当前 D 节完整注入文本替换旧块，不得再次追加。出现 `DUPLICATE` 时先清理重复块，再按当前文本保留唯一一块。`NOFILE` 表示官方 propose 文件不存在，应先运行 `openspec init --tools cursor` 或 `openspec update`。不要把 propose 块写入 apply/verify/sync/archive 文件，也不要把 `AI_TOOLS_VERIFY_GATE_V1` 写入 propose 文件。
````

- [ ] **Step 3：扩展 5.1 节收口句，要求路径 A/B/C 同时注入 D 节**

把紧随其后的收口句：

```text
这是对官方生成物的项目级追加，不要用旧版完整文件覆盖新版官方模板。路径 A、B 均须执行本节；路径 C 在重新生成官方层后也须执行本节。
```

替换为：

```text
这是对官方生成物的项目级追加，不要用旧版完整文件覆盖新版官方模板。路径 A、B 均须执行本节的 A/B/C 与 D；路径 C 在重新生成官方层后也须执行本节的 A/B/C 与 D。仅复制 schema 不会自动获得 propose worktree 选择。
```

- [ ] **Step 4：用合成文件验证检查脚本的五种状态**

在临时目录运行（不要改本仓库官方忽略路径）：

```bash
tmp="$(mktemp -d)"
mkdir -p "$tmp/.cursor/commands" "$tmp/.cursor/skills/openspec-propose"
cd "$tmp"

# NOFILE：缺少 skill
printf '%s\n' '<!-- AI_TOOLS_PROPOSE_WORKTREE_V1 -->' > .cursor/commands/opsx-propose.md
# 只测 command 时先补一个空 skill 再分别断言

python3 - <<'PY'
from pathlib import Path
root = Path('.')
cmd = root / '.cursor/commands/opsx-propose.md'
skill = root / '.cursor/skills/openspec-propose/SKILL.md'

def check(path: Path) -> str:
    if not path.exists():
        return f'NOFILE    {path}'
    text = path.read_text()
    count = text.count('AI_TOOLS_PROPOSE_WORKTREE_V1')
    if count == 0:
        return f'MISSING   {path}'
    if count != 1:
        return f'DUPLICATE {path} ({count} markers)'
    for marker in [
        'AI_TOOLS_PROPOSE_WORKTREE_ASK_ALWAYS_V1',
        'AI_TOOLS_PROPOSE_WORKTREE_INDEPENDENT_V1',
        'AI_TOOLS_PROPOSE_WORKTREE_WORKSPACE_ROOT_V1',
        'AI_TOOLS_PROPOSE_WORKTREE_NO_DOWNGRADE_V1',
    ]:
        if marker not in text:
            return f'STALE     {path} (missing {marker})'
    return f'OK        {path}'

# 1) skill 缺失
cmd.write_text('<!-- AI_TOOLS_PROPOSE_WORKTREE_V1 -->\n')
print(check(cmd))
print(check(skill))

# 2) MISSING
skill.write_text('# propose\n')
print(check(skill))

# 3) STALE：有主标记但缺内嵌标记
skill.write_text('<!-- AI_TOOLS_PROPOSE_WORKTREE_V1 -->\n旧块\n')
print(check(skill))

# 3b) STALE：完整旧版复用块
reuse = '''<!-- AI_TOOLS_PROPOSE_WORKTREE_V1 -->
## Propose 起始工作区选择（AI_TOOLS_PROPOSE_WORKTREE_ASK_ALWAYS_V1）
### 选择隔离 worktree（AI_TOOLS_PROPOSE_WORKTREE_REUSE_V1）
### 失败处理（AI_TOOLS_PROPOSE_WORKTREE_NO_DOWNGRADE_V1）
'''
skill.write_text(reuse)
print(check(skill))

# 4) DUPLICATE
skill.write_text('<!-- AI_TOOLS_PROPOSE_WORKTREE_V1 -->\n<!-- AI_TOOLS_PROPOSE_WORKTREE_V1 -->\n')
print(check(skill))

# 5) OK
ok = '''<!-- AI_TOOLS_PROPOSE_WORKTREE_V1 -->
## Propose 起始工作区选择（AI_TOOLS_PROPOSE_WORKTREE_ASK_ALWAYS_V1）
### 选择隔离 worktree（AI_TOOLS_PROPOSE_WORKTREE_INDEPENDENT_V1）
### 进入目标 worktree（AI_TOOLS_PROPOSE_WORKTREE_WORKSPACE_ROOT_V1）
### 失败处理（AI_TOOLS_PROPOSE_WORKTREE_NO_DOWNGRADE_V1）
'''
skill.write_text(ok)
cmd.write_text(ok)
print(check(cmd))
print(check(skill))
PY
```

把 `print(check(cmd))` 的第一次调用理解为「仅主标记」用例，预期该行是 `STALE` 而不是 `OK`。完整预期：

```text
STALE     .cursor/commands/opsx-propose.md (missing AI_TOOLS_PROPOSE_WORKTREE_ASK_ALWAYS_V1)
NOFILE    .cursor/skills/openspec-propose/SKILL.md
MISSING   .cursor/skills/openspec-propose/SKILL.md
STALE     .cursor/skills/openspec-propose/SKILL.md (missing AI_TOOLS_PROPOSE_WORKTREE_ASK_ALWAYS_V1)
STALE     .cursor/skills/openspec-propose/SKILL.md (missing AI_TOOLS_PROPOSE_WORKTREE_INDEPENDENT_V1)
DUPLICATE .cursor/skills/openspec-propose/SKILL.md (2 markers)
OK        .cursor/commands/opsx-propose.md
OK        .cursor/skills/openspec-propose/SKILL.md
```

另外确认：含 `AI_TOOLS_PROPOSE_WORKTREE_ASK_ALWAYS_V1` 的完整块中，`AI_TOOLS_PROPOSE_WORKTREE_V1` 的固定字符串计数仍为 1，不得被内嵌标记抬成 `DUPLICATE`。

- [ ] **Step 5：确认 8 文件 verify 检查未被改动**

运行：

```bash
rg -n 'AI_TOOLS_VERIFY_GATE_V1|AI_TOOLS_PROPOSE_WORKTREE_V1' \
  docs/ai-tools-integration.md | head -n 80
```

预期：`AI_TOOLS_VERIFY_GATE_V1` 仍出现在 A/B/C 注入与 8 文件循环中；`AI_TOOLS_PROPOSE_WORKTREE_V1` 只出现在 D 节及其 2 文件循环中。

---

### Task 2：把 D 节接入安装、升级与验收叙述

**文件：**
- 修改：`docs/ai-tools-integration.md` 第 1 节、1.1、5.1 开篇、5.3、6.1、6.2、6.3、7.1、7.2、第 8 节、第 9 节

**接口：**
- 消费：Task 1 的 D 节标记与两个目标文件
- 产生：接入文档中所有「只提 8 个 verify 文件」的步骤改为同时处理 2 个 propose 文件

- [ ] **Step 1：更新第 1 节分层说明**

把：

```text
**不要**再把本仓库里的官方 skill/command 副本拷进业务仓覆盖官方文件。应先由 `openspec init` / `openspec update` 生成官方层，再按本文向 apply、verify、sync、archive 的 command/skill 追加项目规则。本仓库 `.gitignore` 已忽略那 7 组官方路径。
```

替换为：

```text
**不要**再把本仓库里的官方 skill/command 副本拷进业务仓覆盖官方文件。应先由 `openspec init` / `openspec update` 生成官方层，再按本文向 propose、apply、verify、sync、archive 的 command/skill 追加项目规则。本仓库 `.gitignore` 已忽略那 7 组官方路径。
```

把表格「官方生成层」那一行：

```text
| 官方生成层 | OpenSpec CLI 为基线，项目补充验证闭环与流转门禁 | explore / propose / update / apply / verify / archive / sync |
| 自定义层 | ai-tools | `evidence-driven` schema（含 `verification`）、验证闭环与流转门禁、工作区指纹脚本、中文规则、from-code 旁路 |
```

替换为：

```text
| 官方生成层 | OpenSpec CLI 为基线，项目补充 propose worktree 选择、验证闭环与流转门禁 | explore / propose / update / apply / verify / archive / sync |
| 自定义层 | ai-tools | `evidence-driven` schema（含 `verification`）、propose worktree 选择、验证闭环与流转门禁、工作区指纹脚本、中文规则、from-code 旁路 |
```

在 `### 1.1 相对纯官方 OpenSpec，你多得到什么` 的 apply 子 Agent 条目之前插入：

```text
- 每次 `/opsx-propose` 或 `openspec-propose` skill 启动时，必须先询问使用隔离 worktree 还是当前工作区；该询问发生在创建 change 或写入任何制品之前。未安装增强规则时，该询问不成立。
```

把 1.2 的：

```text
当前版本不再分发整套分叉模板，仅要求在官方生成物上追加验证闭环与流转门禁。
```

替换为：

```text
当前版本不再分发整套分叉模板，仅要求在官方生成物上追加 propose worktree 选择、验证闭环与流转门禁。
```

- [ ] **Step 2：更新 5.1 开篇，使本节同时覆盖 propose**

把：

```text
安装或更新 OpenSpec 官方 command/skills 后，必须确保 apply、verify、sync、archive 都含当前规则。每个文件只保留一个增强块；`AI_TOOLS_VERIFY_GATE_V1` 是唯一幂等标记。
```

替换为：

```text
安装或更新 OpenSpec 官方 command/skills 后，必须确保 propose、apply、verify、sync、archive 都含当前规则。apply、verify、sync、archive 每个文件只保留一个 `AI_TOOLS_VERIFY_GATE_V1` 增强块；propose command/skill 每个文件只保留一个 `AI_TOOLS_PROPOSE_WORKTREE_V1` 增强块。两套标记不得混写。
```

- [ ] **Step 3：更新 5.3、路径 C 与 6.3 行为表**

在 5.3 段落后增加一句：

```text
propose 的 worktree 选择按 5.1 节 D 段注入，发生在官方 propose 主体之前，不改变后续制品依赖。
```

把 6.1 第 2 条：

```text
2. **自定义层只留明确约定的内容**：`evidence-driven`、5.1 节的验证闭环与流转门禁及工作区指纹脚本、中文规则、from-code。
```

替换为：

```text
2. **自定义层只留明确约定的内容**：`evidence-driven`、5.1 节的 propose worktree 选择、验证闭环与流转门禁及工作区指纹脚本、中文规则、from-code。
```

把 6.2 末尾：

```text
重新生成官方层后，还必须按 5.1 节向 apply、verify、sync、archive 的 command/skill 追加验证闭环与流转门禁。
```

替换为：

```text
重新生成官方层后，还必须按 5.1 节向 propose、apply、verify、sync、archive 的 command/skill 追加 propose worktree 选择以及验证闭环与流转门禁。
```

在 6.3 表中 `verification.md` 那一行之前插入：

```text
| propose 直接在当前工作区创建 change | 每次 propose 先询问隔离 worktree 或当前工作区；选择 worktree 时每次都新建独立 worktree（已处于 linked worktree 也不得复用；须切到新工作区根目录，切不过去则停止；原生可在仓库外，手工才锚定主工作区绝对路径），失败不得静默降级（按 5.1 节 D 段追加） |
```

- [ ] **Step 4：更新 7.1 / 7.2 升级后检查**

把 7.1 中：

```text
`openspec update` 可能刷新官方 skills/commands。升级完成后必须运行 5.1 节的检查并处理 `MISSING`、`STALE`、`DUPLICATE` 或 `NOFILE`：仅 `MISSING` 追加；`STALE` 表示旧 V1 块缺少当前委派标记、`AI_TOOLS_PARALLEL_DISPATCH_V1` 或对应工作者标记，须用当前 A/B 节完整文本替换旧块；`DUPLICATE` 先清理；全部文件最终必须为 `OK`。
```

替换为：

```text
`openspec update` 可能刷新官方 skills/commands。升级完成后必须运行 5.1 节的两套检查并处理 `MISSING`、`STALE`、`DUPLICATE` 或 `NOFILE`：apply/verify/sync/archive 仅 `MISSING` 追加；其 `STALE` 表示旧 V1 块缺少当前委派标记、`AI_TOOLS_PARALLEL_DISPATCH_V1` 或对应工作者标记，须用当前 A/B 节完整文本替换旧块。propose 仅 `MISSING` 追加；其 `STALE` 表示旧块缺少 `AI_TOOLS_PROPOSE_WORKTREE_ASK_ALWAYS_V1`、`AI_TOOLS_PROPOSE_WORKTREE_INDEPENDENT_V1`、`AI_TOOLS_PROPOSE_WORKTREE_WORKSPACE_ROOT_V1` 或 `AI_TOOLS_PROPOSE_WORKTREE_NO_DOWNGRADE_V1`（含仍只有 `AI_TOOLS_PROPOSE_WORKTREE_REUSE_V1` 的块），须用当前 D 节完整文本替换旧块。`DUPLICATE` 先清理；10 个文件最终必须全部为 `OK`。
```

把 7.2 中：

```text
ai-tools 自定义层升级后也必须运行 5.1 节同一检查脚本，识别并替换 `STALE` 的旧 V1 apply/verify 块（含缺少 `AI_TOOLS_PARALLEL_DISPATCH_V1` 或工作者标记的情况）；验收前所有文件都应输出 `OK`。
```

替换为：

```text
ai-tools 自定义层升级后也必须运行 5.1 节两套检查脚本，识别并替换 `STALE` 的旧 V1 apply/verify 块（含缺少 `AI_TOOLS_PARALLEL_DISPATCH_V1` 或工作者标记的情况）以及 `STALE` 的旧 propose worktree 块；验收前 10 个文件都应输出 `OK`。
```

- [ ] **Step 5：更新第 8 节验收清单并新增 FAQ**

把第 8 节开篇：

```text
首次接入或任何升级后，必须在目标项目实际运行 5.1 节脚本并处理所有异常状态，直到
8 个文件全部输出 `OK`，然后确认：
```

替换为：

```text
首次接入或任何升级后，必须在目标项目实际运行 5.1 节两套脚本并处理所有异常状态，直到
apply/verify/sync/archive 8 个文件以及 propose 2 个文件全部输出 `OK`，然后确认：
```

把：

```text
- [ ] 运行 5.1 节同一脚本，8 个文件均输出 `OK`，没有 `MISSING`、`STALE`、`DUPLICATE` 或 `NOFILE`；其中 apply command/skill 含 `AI_TOOLS_DELEGATED_APPLY_V1`、`AI_TOOLS_PARALLEL_DISPATCH_V1` 与 `AI_TOOLS_WORKER_APPLY_V1`，verify command/skill 含 `AI_TOOLS_DELEGATED_VERIFY_V1`、`AI_TOOLS_PARALLEL_DISPATCH_V1` 与 `AI_TOOLS_WORKER_VERIFY_V1`。
```

替换为：

```text
- [ ] 运行 5.1 节两套脚本，8 个 verify 门禁文件与 2 个 propose 文件均输出 `OK`，没有 `MISSING`、`STALE`、`DUPLICATE` 或 `NOFILE`；其中 apply command/skill 含 `AI_TOOLS_DELEGATED_APPLY_V1`、`AI_TOOLS_PARALLEL_DISPATCH_V1` 与 `AI_TOOLS_WORKER_APPLY_V1`，verify command/skill 含 `AI_TOOLS_DELEGATED_VERIFY_V1`、`AI_TOOLS_PARALLEL_DISPATCH_V1` 与 `AI_TOOLS_WORKER_VERIFY_V1`，propose command/skill 含 `AI_TOOLS_PROPOSE_WORKTREE_ASK_ALWAYS_V1`、`AI_TOOLS_PROPOSE_WORKTREE_INDEPENDENT_V1`、`AI_TOOLS_PROPOSE_WORKTREE_WORKSPACE_ROOT_V1` 与 `AI_TOOLS_PROPOSE_WORKTREE_NO_DOWNGRADE_V1`。
```

把：

```text
- [ ] 8 个定制文件各自仅有一个 `AI_TOOLS_VERIFY_GATE_V1` 标记；旧 V1 块已按 `STALE` 规则替换而非重复追加。
- [ ] 仍需要时：中文规则、`openspec-update-change-from-code` 可用。
- [ ] 试跑：`/opsx-propose` 小 change，确认生成 `verification.md`，且 apply 前依赖满足。
```

替换为：

```text
- [ ] 8 个 verify 门禁文件各自仅有一个 `AI_TOOLS_VERIFY_GATE_V1` 标记；2 个 propose 文件各自仅有一个 `AI_TOOLS_PROPOSE_WORKTREE_V1` 标记；旧块已按 `STALE` 规则替换而非重复追加。
- [ ] 仍需要时：中文规则、`openspec-update-change-from-code` 可用。
- [ ] 试跑：`/opsx-propose` 小 change，确认启动后先询问隔离 worktree 或当前工作区，生成 `verification.md`，且 apply 前依赖满足。
```

在第 9 节 `### 安装增强规则后还要再装 Superpowers 吗？` 之前插入：

```markdown
### 每次 propose 都要选 worktree 吗？已经在 worktree 里呢？

要。安装 5.1 节 D 段后，每次 `/opsx-propose` 或 `openspec-propose` skill 都必须先问，即使工作区干净或已经处于 linked worktree。选择「在当前工作区继续」则原地创建 change。选择「使用隔离 worktree」时：每次都新建独立 worktree（新路径 + 新分支），并必须先把本会话工作区根目录切到新路径；仅 shell `cd` 不算切换成功，切不过去则停止，不得在旧目录写 change。已处于 linked worktree 也不得复用。原生 worktree 可以建在仓库外，只要不嵌套、不复用；手工 `git worktree` 才锚定主工作区父目录并用绝对路径。新分支默认基于当前 `HEAD`，因此工作区独立不等于 Git 历史独立。未提交改动不会自动进入新 worktree。创建失败不得静默改在当前目录继续。未安装该增强块时，官方 propose 仍直接在当前工作区执行。
```

- [ ] **Step 6：回归 5.1 节 A/B/C 正文未被改写**

运行：

```bash
rg -n 'AI_TOOLS_DELEGATED_APPLY_V1|AI_TOOLS_DELEGATED_VERIFY_V1|AI_TOOLS_PARALLEL_DISPATCH_V1|AI_TOOLS_WORKER_APPLY_V1|AI_TOOLS_WORKER_VERIFY_V1' \
  docs/ai-tools-integration.md
```

预期：这些标记仍只出现在 A/B 注入、8 文件检查与相关说明中，不出现在 D 节注入正文里。

---

### Task 3：同步 README、场景文档与升级清单

**文件：**
- 修改：`README.md` 安装步骤 5、标准主线
- 修改：`docs/ai-sdd-workflow.md` 闭环约束与场景 1 / 场景 6
- 修改：`docs/openspec-upgrade-plan.md` 第 5.3 步

**接口：**
- 消费：5.1 节 D 段标记与行为
- 产生：用户可见的安装/场景/升级说明与接入文档一致

- [ ] **Step 1：更新 README 安装步骤 5**

把：

```text
5. 要完成当前 ai-tools 接入，必须继续执行
   [接入文档 5.1 节](docs/ai-tools-integration.md#51-补充-verify-修复闭环与流转门禁)：
   创建统一工作区指纹脚本，并向 apply、verify、sync、archive 的 8 个官方
   command/skill 文件幂等追加 `AI_TOOLS_VERIFY_GATE_V1` 规则。
```

替换为：

```text
5. 要完成当前 ai-tools 接入，必须继续执行
   [接入文档 5.1 节](docs/ai-tools-integration.md#51-补充-verify-修复闭环与流转门禁)：
   创建统一工作区指纹脚本，向 apply、verify、sync、archive 的 8 个官方
   command/skill 文件幂等追加 `AI_TOOLS_VERIFY_GATE_V1` 规则，并向 propose 的 2 个
   官方 command/skill 文件幂等追加 `AI_TOOLS_PROPOSE_WORKTREE_V1` 规则。
```

在同一段「仅复制 schema 不会自动获得这些流转门禁与子 Agent 编排。」之后追加：

```text
   也必须注入 propose worktree 选择，否则 `/opsx-propose` 会跳过起始询问，直接在当前
   工作区创建 change。
```

- [ ] **Step 2：更新 README 标准主线**

把：

```text
官方 explore（可选）
  → 官方 propose
  → evidence-driven 制品（含 verification 计划）
```

替换为：

```text
官方 explore（可选）
  → 官方 propose（先询问隔离 worktree 或当前工作区）
  → evidence-driven 制品（含 verification 计划）
```

在「未安装增强规则时，apply/verify 子 Agent 派发及 sync/archive 门禁均不成立」一句改为：

```text
未安装增强规则时，propose 起始 worktree 询问、apply/verify 子 Agent 派发及 sync/archive 门禁均不成立；
```

- [ ] **Step 3：更新场景工作流约束与场景说明**

在 `docs/ai-sdd-workflow.md` 闭环约束中，`安装 AI_TOOLS_VERIFY_GATE_V1 后` 那条之前插入：

```text
- 安装 `AI_TOOLS_PROPOSE_WORKTREE_V1` 后，每次 `propose` 都必须先询问使用隔离
  worktree 还是当前工作区；询问和 worktree 准备发生在创建 change 或写入制品之前。
  选择隔离 worktree 时每次 propose 都必须新建独立 worktree，即使已处于
  linked worktree 也不得复用当前目录；必须先把会话工作区根目录切到新路径，
  切不过去则停止。未安装该增强块时，
  `propose` 仍以目标项目当前 OpenSpec 官方生成物为准。
```

在场景 1「结论明确后使用 `propose` 建立 change」后追加：

```text
`propose` 开始时若已安装 worktree 选择规则，应先选择隔离 worktree 或当前工作区。
```

在场景 6「应直接基于可确认的代码事实使用 `propose` 建立完整 change」后追加同样一句。

- [ ] **Step 4：更新 OpenSpec 升级清单 5.3**

把 `docs/openspec-upgrade-plan.md` 中：

```text
- [ ] **5.3 复核 `AI_TOOLS_VERIFY_GATE_V1` 追加点**

阅读新版 apply、verify、sync、archive 的 command 和 skill，逐项判断 `docs/ai-tools-integration.md` 第 5.1 节的追加内容是否仍有有效插入点、是否与新版官方行为冲突。
```

替换为：

```text
- [ ] **5.3 复核 `AI_TOOLS_VERIFY_GATE_V1` 与 `AI_TOOLS_PROPOSE_WORKTREE_V1` 追加点**

阅读新版 propose、apply、verify、sync、archive 的 command 和 skill，逐项判断 `docs/ai-tools-integration.md` 第 5.1 节 A/B/C 与 D 的追加内容是否仍有有效插入点、是否与新版官方行为冲突。
```

并在该步预期列表增加：

```text
- propose 的 worktree 询问仍必须发生在官方 propose 主体与任何制品写入之前；
```

- [ ] **Step 5：全文扫描不得把官方 propose 重新纳入跟踪**

运行：

```bash
rg -n 'git add .cursor/skills/openspec-propose|跟踪.*openspec-propose|复制官方.*propose' \
  README.md docs/ai-tools-integration.md docs/ai-sdd-workflow.md docs/openspec-upgrade-plan.md \
  docs/superpowers/plans/2026-08-18-openspec-propose-worktree-choice.md
```

预期：无「把官方 propose 生成物纳入本仓库跟踪」的实现表述。`.gitignore` 中现有忽略行保持不变。

---

### Task 4：按设计验收条目做文档与脚本对照

**文件：**
- 检查：`docs/superpowers/specs/2026-08-18-openspec-propose-worktree-choice-design.md`
- 检查：`docs/ai-tools-integration.md`
- 检查：`README.md`
- 检查：`docs/ai-sdd-workflow.md`
- 检查：`docs/openspec-upgrade-plan.md`

**接口：**
- 消费：设计「目标 / 交互与执行流程 / 状态检测与升级 / 错误处理 / 验收」
- 产生：一份可勾选的对照结果；缺口必须在本任务内修回文档，而不是留下 TODO

- [ ] **Step 1：对照设计目标**

运行：

```bash
rg -n 'AI_TOOLS_PROPOSE_WORKTREE_V1|每次|/opsx-propose|openspec-propose|写入任何|官方 propose 主体' \
  docs/ai-tools-integration.md README.md docs/ai-sdd-workflow.md
```

预期：注入正文明确覆盖 command 与 skill、每次询问、写入制品之前完成选择。

- [ ] **Step 2：对照 worktree 检测与失败路径**

运行：

```bash
rg -n 'show-superproject-working-tree|GIT_DIR|GIT_COMMON|check-ignore|git reset --hard|不得静默|未提交改动' \
  docs/ai-tools-integration.md
```

预期：D 节注入同时包含 submodule 守卫、每次新建独立 worktree、禁止嵌套、原生可回退手工、`git -C` 忽略检查、绝对路径、会话工作区切换门禁、禁止 hard reset、禁止静默降级、未提交改动不会自动进入新 worktree。

- [ ] **Step 3：对照状态机**

运行：

```bash
rg -n 'OK|MISSING|STALE|DUPLICATE|NOFILE' docs/ai-tools-integration.md
```

预期：propose 2 文件检查脚本与 5.1 节 D 段说明完整覆盖五种状态；升级 7.1/7.2 与验收第 8 节都要求处理非 `OK`。

- [ ] **Step 4：确认非目标未被破坏**

运行：

```bash
rg -n 'schema: evidence-driven|generates: proposal.md' openspec/schemas/evidence-driven/schema.yaml openspec/config.yaml
rg -n 'AI_TOOLS_VERIFY_GATE_V1' docs/ai-tools-integration.md | wc -l
git ls-files '.cursor/skills/openspec-propose/*' '.cursor/commands/opsx-propose.md'
```

预期：schema 与 config 未改；verify 门禁标记仍大量存在；官方 propose 路径仍不被 Git 跟踪。

- [ ] **Step 5：设计验收 1–9 的文档落点**

确认 D 节、检查脚本、README 试跑说明共同覆盖：

1. 两文件各一块且检查为 `OK`
2. 每次询问，含干净工作区与已有 worktree
3. 选择当前工作区则原地继续
4. 普通 checkout 选择 worktree 则先进入新 worktree
5. 已处于 linked worktree 则新建独立 worktree、不复用、不嵌套；手工用绝对路径
6. submodule 不误判
7. 未忽略 / 创建失败 / 会话工作区未切换 / 基线失败时，写入 change 前停止
8. 重复注入不产生重复块；完整旧版复用块与缺 `WORKSPACE_ROOT` 均为 `STALE` 并整体替换
9. `openspec update` 后重新检查并注入，两文件恢复 `OK`
10. 原生 worktree 可在仓库外；仅 shell `cd` 不得视为已进入

若某条只存在于设计文档、未写入接入文档，必须补进 D 节或第 8 节，不得只在计划里备注。

---

## 自我审查

1. **规格覆盖：** 设计中的目标、非目标、交互流程、状态检测、错误处理、验收 1–9 分别由 Task 1 注入、Task 2 安装/升级/FAQ、Task 3 用户文档、Task 4 对照覆盖。
2. **占位符：** 注入正文、检查脚本和替换片段均为完整文本，无 TBD。
3. **名称一致：** 主标记固定为 `AI_TOOLS_PROPOSE_WORKTREE_V1`；内嵌标记四枚名称在 Task 1–4 中保持不变；目标文件始终是 `opsx-propose.md` 与 `openspec-propose/SKILL.md`。
