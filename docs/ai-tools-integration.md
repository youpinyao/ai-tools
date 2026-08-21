# 将 ai-tools 接入目标项目

本文面向**其它业务仓库**：说明如何从「仅有官方 OpenSpec」或「旧版 ai-tools（本地定制 skills/commands）」升级并接入当前 `ai-tools`。

当前语义基线为 OpenSpec **1.10.0** 官方 `spec-driven`（以 `openspec --version` 与 `npm view @fission-ai/openspec version` 为准）。后续升级须重新查询最新稳定版，不得永久假定该版本细节。

场景化日常用法见 [ai-sdd-workflow.md](./ai-sdd-workflow.md)。Graphify 可选增强见 [graphify-integration.md](./graphify-integration.md)。

## 1. 当前 ai-tools 是什么

当前仓库采用**官方优先（official-first）**分层：

```text
目标项目
├── OpenSpec 官方生成层（openspec init / update 管理）
│   ├── .cursor/skills/openspec-{explore,propose,update-change,apply-change,verify-change,archive-change,sync-specs}/
│   └── .cursor/commands/opsx-{explore,propose,update,apply,verify,archive,sync}.md
│
└── ai-tools 自定义层（从本仓库复制或安装）
    ├── openspec/schemas/evidence-driven/
    ├── openspec/config.yaml 中的 schema: evidence-driven
    ├── .cursor/rules/openspec-chinese.mdc          （可选）
    └── openspec-update-change-from-code             （可选旁路）
```

| 层级 | 谁维护 | 内容 |
|------|--------|------|
| 官方生成层 | OpenSpec CLI 为基线，项目补充 propose worktree 选择、隔离 worktree 收尾、验证闭环与流转门禁 | explore / propose / update / apply / verify / archive / sync |
| 自定义层 | ai-tools | `evidence-driven` schema（含 `verification`）、propose worktree 选择、隔离 worktree 收尾、验证闭环与流转门禁、工作区指纹脚本、中文规则、from-code 旁路 |

**不要**再把本仓库里的官方 skill/command 副本拷进业务仓覆盖官方文件。应先由 `openspec init` / `openspec update` 生成官方层，再按本文向 propose、apply、verify、sync、archive 的 command/skill 追加项目规则。本仓库 `.gitignore` 已忽略那 7 组官方路径。

### 1.1 相对纯官方 OpenSpec，你多得到什么

- 默认 schema：`evidence-driven`（官方默认多为 `spec-driven`）。
- 额外制品：`verification.md`（验证计划 + 实现侧真实结果记录，含必做代码审查）。
- 制品依赖：`tasks → verification`，且 `apply` 依赖 `verification`；该 schema 依赖只表示制品已创建，流转门禁另以 verification 中的 Verify 门禁标记为准。
- 代码审查在 verification 中必做：apply 子 Agent 针对完整实现 diff 执行首次审查并记账；verify 子 Agent 每次安全修复代码后，必须针对修复后的完整 diff 重新执行审查并更新结论。未处理的 Critical/Important 会使 Verify 门禁失败，因此也是项目级 sync/archive 流转条件。
- 每次 `/opsx-propose` 或 `openspec-propose` skill 启动时，必须先询问使用隔离 worktree 还是当前工作区；该询问发生在创建 change 或写入任何制品之前。未安装增强规则时，该询问不成立。
- 入口 Agent 准备结束 propose / apply / verify / sync / archive 时，若存在本次相关隔离 worktree（本会话创建，或位于项目 worktree 父目录），必须先询问是否合并到主分支并清理，再结束回复。不得自动合并或删除。未提交改动须先经用户明确同意提交。未安装收尾增强块时，该询问不成立。
- 入口 Agent 先派发 apply 子 Agent；成功后再派发独立 verify 子 Agent。单独运行 `/opsx-verify` 时，入口 Agent 同样派发 verify 子 Agent。apply / verify 阶段仍串行。阶段子 Agent 每次运行时仅当本会话可用 skills 列表中存在 `dispatching-parallel-agents` 时，才对独立域并行派发带工作者身份标记的实施者 / 调查者；列表中没有则按官方默认串行，不得因磁盘或插件缓存中能读到 `SKILL.md` 而启用并行。后续安装该 skill 无需再次替换注入。verify 子 Agent 仅直接修复可安全、在当前 change 范围内且无需用户决策的阻塞并重新验证（最多 3 轮）；遇正式规则列出的其它情况停止并返回入口 Agent。verification 完成且无阻塞项后，才可进入 sync 或 archive。
- 可选：简体中文强制规则、`/opsx-update-change-from-code`。

### 1.2 相对旧版 ai-tools，你不再从本仓库获得什么

旧版曾在仓库内跟踪并深度定制官方 skills/commands（含 Code Review 归档硬门禁、Superpowers finishing 等）。当前版本不再分发整套分叉模板，仅要求在官方生成物上追加 propose worktree 选择、隔离 worktree 收尾、验证闭环与流转门禁。

接入后：

- apply / verify / archive / sync 的主体行为仍以目标项目中**当前官方生成物**为准；项目追加规则负责入口编排（派发 apply/verify 子 Agent）、修复验证阻塞、强制检查流转门禁，以及隔离 worktree 跑完后的收尾询问。
- 若业务仍需要旧硬门禁，应另立项目内规则或独立 skill，而不是期待本仓库继续提供分叉模板。

## 2. 前置条件

- Node.js 满足 OpenSpec CLI 要求（官方要求 Node.js ≥ 20.19.0）。
- Python 3.8+（用于计算 verify、sync、archive 共用的确定性工作区指纹）。
- 支持 [Agent Skills](https://agentskills.io) 的助手（本文以 Cursor 为主）。
- 能在目标项目根目录执行 shell。

建议固定变量：

```bash
AI_TOOLS_DIR="/absolute/path/to/ai-tools"          # 本仓库克隆路径
TARGET_PROJECT="/absolute/path/to/target-project"  # 业务项目根目录
```

也可不克隆本仓库，仅用 GitHub / skills.sh 安装可选 skill；schema 仍需从本仓库（或发布物）复制。

```bash
npm install --global @fission-ai/openspec@latest
openspec --version
# 建议与 npm 最新稳定版一致后再接入
```

团队执行升级时应记录并固定解析出的精确版本，避免 `@latest` 在执行过程中再次漂移：

```bash
TARGET_VERSION="$(npm view @fission-ai/openspec version)"
npm install --global "@fission-ai/openspec@$TARGET_VERSION"
test "$(openspec --version)" = "$TARGET_VERSION"
```

## 3. 先判断你属于哪条路径

```text
目标项目里有没有 openspec/ ？
  ├─ 没有 → A. 全新接入（官方 OpenSpec + ai-tools）
  └─ 有
       ├─ 仅有官方 skills/commands，schema 多为 spec-driven
       │     → B. 已有官方 OpenSpec，叠加 ai-tools
       └─ 曾复制旧 ai-tools（本地改过 opsx-* / openspec-* skill）
             → C. 从旧版 ai-tools 迁移到 official-first
```

可用快速探测：

```bash
cd "$TARGET_PROJECT"

# 是否已有 OpenSpec 根
test -f openspec/config.yaml && echo "has-openspec-config" || echo "no-config"

# 当前默认 schema
grep -E '^schema:' openspec/config.yaml 2>/dev/null || true

# 是否像「旧版本地定制」：官方 skill 被 Git 跟踪，或含本仓库旧门禁关键词
git ls-files '.cursor/skills/openspec-apply-change/*' '.cursor/commands/opsx-apply.md' 2>/dev/null
rg -n "独立验证结论|代码审查（归档硬门禁）|Superpowers 对接" \
  .cursor/skills/openspec-apply-change \
  .cursor/commands/opsx-apply.md 2>/dev/null || true
```

- 若官方路径被 Git **跟踪**，或文件中出现上述旧门禁文案 → 走 **路径 C**。
- 若只有 `openspec/` + 未被定制的官方生成物 → 走 **路径 B**。
- 若几乎没有 OpenSpec → 走 **路径 A**。

## 4. 路径 A：全新项目接入

在业务项目根目录：

```bash
cd "$TARGET_PROJECT"

# 1) 生成官方 Cursor skills / commands
openspec init --tools cursor

# 2) 安装 evidence-driven schema
mkdir -p openspec/schemas
cp -R \
  "$AI_TOOLS_DIR/openspec/schemas/evidence-driven" \
  openspec/schemas/

# 3) 启用 schema（新建或合并，勿盲目整文件覆盖）
# openspec/config.yaml 至少包含：
#   schema: evidence-driven

# 4) 校验
openspec schema validate evidence-driven
```

可选：

```bash
# 中文规则
mkdir -p .cursor/rules
cp \
  "$AI_TOOLS_DIR/.cursor/rules/openspec-chinese.mdc" \
  .cursor/rules/openspec-chinese.mdc

# from-code 旁路
npx skills add youpinyao/ai-tools --skill openspec-update-change-from-code
```

建议在目标项目 `.gitignore` 中**不要**忽略官方 skills（它们通常需要提交给团队共用）；本 `ai-tools` 仓库自身忽略它们，是因为工具包仓库不负责分发官方副本。业务仓按团队惯例选择是否提交官方生成物即可。

## 5. 路径 B：已有官方 OpenSpec，叠加 ai-tools

适用于：项目已 `openspec init`，默认 `spec-driven`，未深度分叉官方 skill。

```bash
cd "$TARGET_PROJECT"

# 1) 先把官方生成物升到当前 CLI 对应版本
npm install --global @fission-ai/openspec@latest
openspec --version
# 团队升级请改用精确版本，见 7.1 节
openspec update

# 2) 安装 / 覆盖自定义 schema（只覆盖 evidence-driven 目录）
mkdir -p openspec/schemas
rm -rf openspec/schemas/evidence-driven
cp -R \
  "$AI_TOOLS_DIR/openspec/schemas/evidence-driven" \
  openspec/schemas/

# 3) 合并配置：只改 schema 字段，保留 context / rules / operations 等项目配置
# schema: evidence-driven

# 4) 校验
openspec schema validate evidence-driven
```

### 5.1 补充 verify 修复闭环与流转门禁

安装或更新 OpenSpec 官方 command/skills 后，必须确保 propose、apply、verify、sync、archive 都含当前规则。apply、verify、sync、archive 每个文件只保留一个 `AI_TOOLS_VERIFY_GATE_V1` 增强块；propose command/skill 每个文件只保留一个 `AI_TOOLS_PROPOSE_WORKTREE_V1` 增强块；上述 10 个文件每个还只保留一个 `AI_TOOLS_WORKTREE_FINISH_V1` 收尾块。三套标记不得混写：Verify 门禁不得写入 propose，propose worktree 选择不得写入 apply/verify/sync/archive，收尾块必须同时出现在全部 10 个文件且不得并入另外两套块的正文。

插入位置：YAML frontmatter 之后、官方正文（含 Store selection 与 **Steps**）之前，使 Agent 先读到项目规则。1.10.0 的 `openspec init --tools cursor` 仍生成下列 10 个目标文件；官方 apply 在制品缺失时可能提示未随 init 生成的 `/opsx-continue`，不要把它纳入本仓库 `.gitignore` 或本节幂等清单。官方流程本身不提供 worktree 选择、隔离 worktree 收尾、子 Agent 编排、`verification.md` 持久化门禁或工作区指纹；下列 A/B/C/D/E 仍是项目级追加，不是官方已实现能力。

#### 统一工作区指纹

先创建 `.cursor/scripts/openspec-verification-fingerprint.py`：

```python
#!/usr/bin/env python3
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys

START = b"<!-- AI_TOOLS_VERIFICATION_RESULT_V1_START -->"
END = b"<!-- AI_TOOLS_VERIFICATION_RESULT_V1_END -->"
GATE_PATTERN = re.compile(
    rb"(?ms)^[ \t]*" + re.escape(START) + rb".*?^[ \t]*"
    + re.escape(END) + rb"[ \t]*\r?\n?"
)


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=root)


def add_frame(digest: "hashlib._Hash", label: bytes, data: bytes) -> None:
    digest.update(len(label).to_bytes(8, "big"))
    digest.update(label)
    digest.update(len(data).to_bytes(8, "big"))
    digest.update(data)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: openspec-verification-fingerprint.py <verification.md>")

    root = Path(os.fsdecode(git(Path.cwd(), "rev-parse", "--show-toplevel").strip())).resolve()
    verification = Path(sys.argv[1]).resolve()
    try:
        verification_relative = verification.relative_to(root)
    except ValueError as error:
        raise SystemExit("verification.md must be inside the Git repository") from error

    raw_paths = git(root, "ls-files", "-co", "--exclude-standard", "-z").split(b"\0")
    digest = hashlib.sha256()
    add_frame(digest, b"HEAD", git(root, "rev-parse", "HEAD").strip())
    add_frame(
        digest,
        b"STATUS",
        git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all"),
    )
    add_frame(digest, b"INDEX", git(root, "ls-files", "--stage", "-z"))

    verification_key = os.fsencode(verification_relative.as_posix())
    for raw_path in sorted(path for path in raw_paths if path):
        path = root / os.fsdecode(raw_path)
        if path.is_symlink():
            data = b"<SYMLINK>" + os.fsencode(os.readlink(path))
        elif path.is_dir():
            relative = os.fsdecode(raw_path)
            submodule_status = git(root, "submodule", "status", "--", relative)
            nested_status = git(
                path,
                "status",
                "--porcelain=v1",
                "-z",
                "--untracked-files=all",
            )
            if not submodule_status.startswith(b" ") or nested_status:
                raise SystemExit(
                    f"submodule must be initialized and clean before verify: {relative}"
                )
            data = b"<SUBMODULE>" + submodule_status
        elif path.exists():
            data = path.read_bytes()
        else:
            data = b"<MISSING>"
        if raw_path == verification_key:
            data = GATE_PATTERN.sub(b"", data)
        add_frame(digest, b"PATH", raw_path)
        add_frame(digest, b"CONTENT", data)

    print(digest.hexdigest())


if __name__ == "__main__":
    main()
```

该脚本对 `HEAD`、索引元数据、工作区状态及所有 tracked/untracked 非忽略文件进行确定性计算。对于当前 `verification.md`，仅排除 `AI_TOOLS_VERIFICATION_RESULT_V1` 门禁块自身；验证证据、失败记录或剩余风险的任何变化仍会改变指纹。Git submodule 必须已初始化且工作区干净，脚本会将其固定提交纳入指纹，否则直接阻塞流转。

#### A. Apply：派发实施与独立验证

向以下两个文件追加或替换为以下内容（`STALE` 时替换旧块）：

- `.cursor/commands/opsx-apply.md`
- `.cursor/skills/openspec-apply-change/SKILL.md`

插入位置：YAML frontmatter 之后、官方 **Steps** 第 1 步（Select the change）之前。1.10.0 官方 apply 是串行任务循环，不含子 Agent；在 `state: "all_done"` 与完成输出中会建议 `/opsx-archive`。以本块第 4–5 条为准，门禁通过前不得按官方文案建议 sync 或 archive。

```markdown
<!-- AI_TOOLS_VERIFY_GATE_V1 -->
## Apply 子 Agent 实施与强制验证

若当前会话已按本节派发过 apply 子 Agent，本节视为已执行，不得因 command 与 skill 同处一个上下文而重复派发。入口 Agent 仍负责等待 apply 子 Agent、在其成功后派发并等待 verify 子 Agent，以及检查 Verify 门禁和工作区指纹，但不得执行官方 apply 主体。官方 apply 在 `state: "all_done"` 或任务全部完成后会建议 `/opsx-archive`；在 Verify 门禁通过前，不得按该官方文案建议 sync 或 archive。

在执行任何 apply 主体步骤前，只检查父 Agent 或用户下发给本次任务的提示文本；本规则正文中出现的标记字符串不计入判定。按下列顺序判定，命中即停：

1. 若提示文本显式包含 `AI_TOOLS_WORKER_APPLY_V1`，当前 Agent 是 apply 实施者，不是入口也不是 apply 阶段子 Agent：
   - 只实施任务给出的独立 task 域和拟改路径；
   - 不得派发 apply / verify 阶段子 Agent，不得再派实施者或调查者；
   - 不得勾选 `tasks.md`，不得写 `verification.md`、门禁块或计算指纹；
   - 不得执行 git add、commit、stash 或其它索引 / HEAD 写入；
   - 即使提示中还出现 `AI_TOOLS_DELEGATED_APPLY_V1` 或 `AI_TOOLS_DELEGATED_VERIFY_V1`，仍按实施者执行；
   - 完成后把结果或阻塞返回 apply 子 Agent，不得向用户提问。
2. 若提示文本未显式包含 `AI_TOOLS_DELEGATED_APPLY_V1`，当前 Agent 是入口编排者，不得直接实施：
   - 派发一个子 Agent，在任务中加入 `AI_TOOLS_DELEGATED_APPLY_V1`，要求其使用 `openspec-apply-change` skill 实施当前 change，且不得派发 apply 或 verify 阶段子 Agent；
   - 等待 apply 子 Agent 返回；失败或阻塞时立即停止，不得启动 verify；
   - apply 成功后派发另一个独立子 Agent，在任务中加入 `AI_TOOLS_DELEGATED_VERIFY_V1`，要求其使用 `openspec-verify-change` skill 执行 verify；
   - 等待 verify 子 Agent 返回，再检查唯一 Verify 门禁及当前工作区指纹。
3. 若提示文本显式包含 `AI_TOOLS_DELEGATED_APPLY_V1`，当前 Agent 是 apply 子 Agent，不得再次派发 apply 或 verify 阶段子 Agent。apply 与 verify 两个阶段必须串行，不得对开。执行官方 apply 主体前，仅当本会话可用 skills 列表中存在名为 `dispatching-parallel-agents` 的 skill 时，才读取并遵循该 skill；不得因本规则正文出现该 skill 名、也不得因磁盘或插件缓存中能读到 `SKILL.md` 而判定为可用。阶段内并行（AI_TOOLS_PARALLEL_DISPATCH_V1）：
   - skill 在会话列表中：仅对无共享状态、不会改同一相对路径或同一制品、互不依赖的独立 task 域，在同一轮派发实施者。每个实施者任务必须包含 `AI_TOOLS_WORKER_APPLY_V1`，且不得包含 `AI_TOOLS_DELEGATED_APPLY_V1` 或 `AI_TOOLS_DELEGATED_VERIFY_V1`。实施者返回后，以本阶段开始时的路径集合为基线，若两名及以上实施者改动了同一相对路径，则视为重叠，由 apply 子 Agent 串行重做冲突项。无法还原该基线或无法分离已混写内容时，停止并把阻塞返回入口 Agent，不得勾选冲突项。只有 apply 子 Agent 勾选 `tasks.md`。全部 task 结束后仍由 apply 子 Agent 对完整实现 diff 做首次代码审查。
   - skill 不在会话列表中：按官方逐项循环由 apply 子 Agent 自己实施；不得为并行派发实施者；静默串行，不向用户报错，不得猜测、不得联网安装该 skill。
   - 阶段内并行派发工具不可用：退回本阶段官方串行，不得改由入口执行官方 apply 主体。
   - 共享状态、会改同一路径或同一制品、修 A 可能带上 B、或拿不准时：不并行。
   - 实施者缺少必要上下文：由 apply 子 Agent 补齐后重派或改串行，不得让实施者猜测 change。
   完成后把结果或阻塞返回入口 Agent。
4. 仅当 Verify 门禁为“状态：通过、阻塞项：无”且指纹匹配时，入口 Agent 才可结束 apply 并建议 sync 或 archive。
5. Verify 门禁缺失、状态未通过、存在阻塞、指纹不匹配或 verify 子 Agent 失败时，入口 Agent 不得宣告 apply 完成；change 保持 active，必须报告具体阻塞原因，且不得建议 sync 或 archive。
6. 入口 Agent 准备结束本命令（含成功后的 verify、apply/verify 失败停止，或会话 worktree 已创建但官方主体未完成）时，必须按同文件「隔离 worktree 收尾」节询问用户。实施者与 apply 子 Agent 不得询问、不得合并或删除 worktree。
```

#### B. Verify：修复、复验并持久化结论

向以下两个文件追加或替换为以下内容（`STALE` 时替换旧块）：

- `.cursor/commands/opsx-verify.md`
- `.cursor/skills/openspec-verify-change/SKILL.md`

插入位置：YAML frontmatter 之后、官方 **Steps** 第 1 步（Select the change）之前。1.10.0 官方 verify 只在会话中输出 Completeness / Correctness / Coherence 记分卡，不写 `verification.md`、不修复、不算指纹；官方「Ready for archive」不是项目硬门禁，不得替代下方闭环。

```markdown
<!-- AI_TOOLS_VERIFY_GATE_V1 -->
## Verify 入口编排与验证阻塞修复闭环

若当前会话已派发过 verify 子 Agent（无论由本节还是 Apply 节触发），本节视为已执行，不得因 command 与 skill 同处一个上下文而重复派发。入口 Agent 只等待该子 Agent 并读取、汇报最终门禁，不得执行官方 verify 主体。官方 verify 的会话记分卡（CRITICAL / WARNING / SUGGESTION）和「Ready for archive」文案不是本项目硬门禁，不得替代下方闭环；必须写入 `verification.md` 并计算指纹。

在执行任何 verify 主体步骤前，只检查父 Agent 或用户下发给本次任务的提示文本；本规则正文中出现的标记字符串不计入判定。按下列顺序判定，命中即停：

1. 若提示文本显式包含 `AI_TOOLS_WORKER_VERIFY_V1`，当前 Agent 是 verify 调查者，不是入口也不是 verify 阶段子 Agent：
   - 只做任务给出的独立失败域或只读检查域；
   - 不得派发 apply / verify 阶段子 Agent，不得再派实施者或调查者；
   - 不得写 `verification.md`、门禁块或计算指纹；
   - 不得执行 git add、commit、stash 或其它索引 / HEAD 写入；
   - 即使提示中还出现 `AI_TOOLS_DELEGATED_APPLY_V1` 或 `AI_TOOLS_DELEGATED_VERIFY_V1`，仍按调查者执行；
   - 完成后把结果或阻塞返回 verify 子 Agent，不得向用户提问。
2. 若提示文本未显式包含 `AI_TOOLS_DELEGATED_VERIFY_V1`，当前 Agent 是入口编排者，不得直接验证：派发一个子 Agent，在任务中加入该标记，要求其使用 `openspec-verify-change` skill 执行当前 change 的完整 verify；等待后读取并汇报最终门禁。
3. 若提示文本显式包含 `AI_TOOLS_DELEGATED_VERIFY_V1`，当前 Agent 是 verify 子 Agent，不得再次派发 verify 阶段子 Agent。apply 与 verify 两个阶段必须串行，不得对开。执行官方 verify 主体前，仅当本会话可用 skills 列表中存在名为 `dispatching-parallel-agents` 的 skill 时，才读取并遵循该 skill；不得因本规则正文出现该 skill 名、也不得因磁盘或插件缓存中能读到 `SKILL.md` 而判定为可用。阶段内并行（AI_TOOLS_PARALLEL_DISPATCH_V1）：
   - skill 在会话列表中：仅对只读、互不干扰的检查或独立失败域，在同一轮派发调查者。每个调查者任务必须包含 `AI_TOOLS_WORKER_VERIFY_V1`，且不得包含 `AI_TOOLS_DELEGATED_APPLY_V1` 或 `AI_TOOLS_DELEGATED_VERIFY_V1`。调查者返回后，verify 子 Agent 汇合结论；以本阶段开始时的路径集合为基线，若两名及以上调查者改动了同一相对路径，则视为重叠，由 verify 子 Agent 串行重做冲突项。无法还原该基线或无法分离已混写内容时，停止并把阻塞返回入口 Agent，不得写通过门禁。需要安全修复时，仅当修复域独立且无共享状态才可按该 skill 并行修改互不重叠的路径；否则由 verify 子 Agent 串行修复。每一轮修复后的完整复验、完整 diff 审查、门禁与指纹仍由 verify 子 Agent 串行收口。同一轮内对独立域的并行修复只计 1 轮；必须等该轮全部修复返回并由 verify 子 Agent 做完整复验后，才可进入下一轮。
   - skill 不在会话列表中：由 verify 子 Agent 独自完成下方验证闭环；不得为并行派发调查者；静默串行，不向用户报错，不得猜测、不得联网安装该 skill。
   - 阶段内并行派发工具不可用：退回本阶段官方串行，不得改由入口执行官方 verify 主体。
   - 共享状态、会改同一路径或同一制品、修 A 可能带上 B、或拿不准时：不并行。
   - 调查者缺少必要上下文：由 verify 子 Agent 补齐后重派或改串行，不得让调查者猜测 change。
4. 子 Agent 按下方验证闭环中的正式阻塞条件处理；需要停止时把阻塞返回入口 Agent。

### 验证闭环

1. 实际执行验证并检查代码、测试及 change 制品。发现可安全修复的阻塞项时，按第 3 步已判定的方式修复（verify 子 Agent 串行修复，或对独立修复域派带 `AI_TOOLS_WORKER_VERIFY_V1` 的调查者），并重新运行受影响的检查和完整 verify。
2. 最多执行 3 轮“验证—修复—重新验证”。同一轮内并行修复只计 1 轮。同一阻塞连续两轮无进展时提前停止。
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

入口 Agent 准备结束本命令（含验证失败停止）时，必须按同文件「隔离 worktree 收尾」节询问用户。调查者与 verify 子 Agent 不得询问、不得合并或删除 worktree。
```

#### C. Sync / Archive：入口处强制检查

向以下四个文件追加或替换为以下内容（`STALE` 时替换旧块）：

- `.cursor/commands/opsx-sync.md`
- `.cursor/skills/openspec-sync-specs/SKILL.md`
- `.cursor/commands/opsx-archive.md`
- `.cursor/skills/openspec-archive-change/SKILL.md`

插入位置：YAML frontmatter 之后、官方 **Steps** 第 1 步（Select the change，含 archive 的 advisory `openspec instructions archive`）之前。1.10.0 官方 archive 对未完成制品或任务仅警告并允许用户确认继续，且 `openspec instructions archive --json` 被标明为不得阻断归档的 advisory 输入；这些官方行为不得用来绕过本项目 Verify 门禁。

```markdown
<!-- AI_TOOLS_VERIFY_GATE_V1 -->
## Verification 流转门禁

执行任何 sync 或 archive 操作前，必须读取当前 change 的 `verification.md`，并检查唯一的 `AI_TOOLS_VERIFICATION_RESULT_V1` 门禁块。运行 `python3 .cursor/scripts/openspec-verification-fingerprint.py "<当前 change 的 verification.md 路径>"` 重新计算当前工作区指纹；只有门禁块同时包含 `状态：通过`、`阻塞项：无`，且记录的验证指纹与命令输出完全一致时才可继续。

本门禁发生在官方 sync / archive 主体之前。官方 archive 对未完成制品或任务仅警告并允许用户确认继续，且 `openspec instructions archive --json` 被标明为不得阻断归档的 advisory 输入；上述官方行为不得用来绕过本门禁。

门禁块缺失、状态不是“通过”、阻塞项不是“无”、验证指纹不匹配，或存在多个门禁块时，立即停止；不得通过用户确认绕过。验证后发生的任何代码或制品变化都会使旧门禁失效，应先重新执行 verify，修复阻塞并刷新门禁结果。

官方 sync / archive 主体结束后，或门禁拦住导致官方主体未开始时，入口 Agent 必须按同文件「隔离 worktree 收尾」节询问用户。
```

首次接入、追加或替换前，以及每次 `openspec update` 或 ai-tools 自定义层升级后，在目标项目根目录运行：

```bash
command -v rg >/dev/null || {
  echo 'ERROR: ripgrep (rg) is required'
  exit 1
}

for file in \
  .cursor/commands/opsx-{apply,verify,sync,archive}.md \
  .cursor/skills/openspec-{apply-change,verify-change,sync-specs,archive-change}/SKILL.md
do
  if [ ! -f "$file" ]; then
    echo "NOFILE    $file"
    continue
  fi
  count="$( { rg -o --fixed-strings 'AI_TOOLS_VERIFY_GATE_V1' "$file" || true; } | wc -l | tr -d ' ')"
  case "$count" in
    0) echo "MISSING   $file" ;;
    1)
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
      ;;
    *) echo "DUPLICATE $file ($count markers)" ;;
  esac
done
```

`MISSING` 表示尚无增强块，只向这些文件追加当前 A/B/C 节的对应完整文本。`STALE` 表示文件只有一个 `AI_TOOLS_VERIFY_GATE_V1` 标记，但 apply/verify 块缺少当前委派标记、`AI_TOOLS_PARALLEL_DISPATCH_V1` 或对应工作者标记（apply 为 `AI_TOOLS_WORKER_APPLY_V1`，verify 为 `AI_TOOLS_WORKER_VERIFY_V1`）；必须用当前 A/B 节的完整注入文本替换旧块，不得再次追加。缺少 Superpowers 或缺少 `dispatching-parallel-agents` 不得标为 `STALE`。出现 `DUPLICATE` 时先清理重复块，再按当前文本保留唯一一块。`NOFILE` 表示官方文件不存在，应先恢复官方生成层。若官方模板升级后结构发生变化，应先人工确认追加位置是否仍适用。上述检查同时验收 apply 两个文件的 APPLY、并行与工作者标记，以及 verify 两个文件的 VERIFY、并行与工作者标记，无需维护第二套检查逻辑。

#### D. Propose：起始 worktree 选择

向以下两个文件追加或替换为以下内容（`STALE` 时替换旧块）：

- `.cursor/commands/opsx-propose.md`
- `.cursor/skills/openspec-propose/SKILL.md`

command 与 skill 使用同一规则正文；仅当官方文件标题层级会与本节冲突时，才把本节 `##` / `###` 降一级，不得改语义。1.10.0 官方 propose 正文使用加粗小节而非 `##` 标题，本节标题层级无需降级。

插入位置：YAML frontmatter 之后、官方 Planning boundary、Store selection 与 **Steps** 第 1 步（理解需求并推导 kebab-case 名称）之前。1.10.0 官方仍无 worktree 选择；首次写入发生在 Step 3 的 `openspec new change`。

```markdown
<!-- AI_TOOLS_PROPOSE_WORKTREE_V1 -->
## Propose 起始工作区选择（AI_TOOLS_PROPOSE_WORKTREE_ASK_ALWAYS_V1）

在执行任何官方 propose 主体步骤前，必须先完成工作区选择。本询问必须发生在官方 Planning boundary、Store selection、Step 1（理解需求并推导 kebab-case 名称）以及 `openspec new change` 之前。不得创建 change、不得分配 change 名称、不得写入 `openspec/changes/` 下任何制品，也不得运行 `openspec new change`。

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
8. 创建成功后（原生或手工）必须冻结 `$SESSION_WORKTREE`（新路径经 `pwd -P`）与 `$SESSION_BRANCH`（新分支名），供同文件收尾节使用（AI_TOOLS_PROPOSE_WORKTREE_SESSION_V1）。未冻结不得进入官方 propose。

### 进入目标 worktree（AI_TOOLS_PROPOSE_WORKTREE_WORKSPACE_ROOT_V1）

创建完成后必须把**本会话的工作区根目录**切到新 worktree，优先使用原生切换能力（例如 `EnterWorktree`）。仅在 shell 中 `cd`、但编辑器或文件工具仍写入旧根目录，视为未切换成功。

进入官方 propose、执行 setup / 基线检查、或写入任何制品前，确认工作区根（当前 Cursor workspace / 打开的项目根，经 `pwd -P`）等于新 worktree 路径（经 `pwd -P`）。切不过去：立即停止并报告新旧路径，不得在旧 worktree 继续 propose，不得写入 `openspec/changes/`。

切换确认后，执行项目可识别的基础 setup：存在 `package.json` 则安装依赖；存在 `Cargo.toml` 则构建；存在 `requirements.txt` / `pyproject.toml` / `go.mod` 则按对应工具安装。没有这些文件则跳过该项。

再执行项目可识别的基线检查：仓库已有明确测试命令时才运行。没有可识别测试命令则跳过。setup 或基线检查失败时暂停并报告原因；在用户明确同意继续前，不得进入官方 propose。

### 失败处理（AI_TOOLS_PROPOSE_WORKTREE_NO_DOWNGRADE_V1）

用户取消、worktree 创建失败、目录未被忽略、sandbox 拒绝、会话工作区未切到新 worktree、setup 失败或基线检查失败且用户未明确同意继续时，立即停止并报告原因；不得静默退回当前工作区继续 propose。所有阻塞必须发生在 OpenSpec change 和制品创建之前。若 `$SESSION_WORKTREE` 已存在，入口 Agent 准备结束回复时仍须按同文件「隔离 worktree 收尾」节询问本次 worktree 的清理或保留。

准备完成后，才进入官方 propose 主体。无论官方 propose 是否完成，入口 Agent 准备结束回复时必须按同文件「隔离 worktree 收尾」节询问。
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
      required="AI_TOOLS_PROPOSE_WORKTREE_ASK_ALWAYS_V1 AI_TOOLS_PROPOSE_WORKTREE_INDEPENDENT_V1 AI_TOOLS_PROPOSE_WORKTREE_WORKSPACE_ROOT_V1 AI_TOOLS_PROPOSE_WORKTREE_NO_DOWNGRADE_V1 AI_TOOLS_PROPOSE_WORKTREE_SESSION_V1"
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

`MISSING` 表示尚无增强块，只向这两个文件追加当前 D 节完整文本。`STALE` 表示文件只有一个 `AI_TOOLS_PROPOSE_WORKTREE_V1` 标记，但缺少 `AI_TOOLS_PROPOSE_WORKTREE_ASK_ALWAYS_V1`、`AI_TOOLS_PROPOSE_WORKTREE_INDEPENDENT_V1`、`AI_TOOLS_PROPOSE_WORKTREE_WORKSPACE_ROOT_V1`、`AI_TOOLS_PROPOSE_WORKTREE_NO_DOWNGRADE_V1` 或 `AI_TOOLS_PROPOSE_WORKTREE_SESSION_V1`（含仍只有旧标记 `AI_TOOLS_PROPOSE_WORKTREE_REUSE_V1`、或未冻结 `$SESSION_WORKTREE` 的块）；必须用当前 D 节完整注入文本替换旧块，不得再次追加。出现 `DUPLICATE` 时先清理重复块，再按当前文本保留唯一一块。`NOFILE` 表示官方 propose 文件不存在，应先运行 `openspec init --tools cursor` 或 `openspec update`。不要把 propose 块写入 apply/verify/sync/archive 文件，也不要把 `AI_TOOLS_VERIFY_GATE_V1` 写入 propose 文件。不要把 `AI_TOOLS_WORKTREE_FINISH_V1` 写入 D 节正文；收尾使用独立的 E 节块。

#### E. 隔离 worktree 收尾

向以下 10 个文件追加或替换为以下内容（`STALE` 时替换旧收尾块）。每个文件在已有 A/B/C 或 D 块之后再追加本块，不得把本块并入 `AI_TOOLS_VERIFY_GATE_V1` 或 `AI_TOOLS_PROPOSE_WORKTREE_V1` 正文。

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

command 与 skill 使用同一规则正文；仅当官方文件标题层级会与本节冲突时，才把本节 `##` / `###` 降一级，不得改语义。插入位置：已有项目增强块之后、官方 **Steps** 之前；若尚无项目增强块，则紧接 YAML frontmatter 之后。本块约束入口 Agent 在准备结束回复时的收尾，包括官方主体未完成但本次 worktree 已存在的路径；不替代 D 节起始询问，也不替代 A/B/C 的 Verify 门禁。

```markdown
<!-- AI_TOOLS_WORKTREE_FINISH_V1 -->
## 隔离 worktree 收尾（AI_TOOLS_WORKTREE_FINISH_ASK_ALWAYS_V1）

当入口 Agent 准备结束回复时，必须先判断是否询问本次隔离 worktree 收尾。触发包括：官方主体成功结束；apply 入口已等完衔接的 verify 或 apply/verify 失败停止；以及本次 worktree 已创建或已切入，但官方主体未完成（setup / 基线失败、Verify 门禁拦住 sync/archive、用户在官方主体前取消）。本询问不得发生在官方主体或已衔接的 verify 仍在执行时。

只检查父 Agent 或用户下发给本次任务的提示文本；本规则正文中出现的标记字符串不计入判定。若提示文本显式包含 `AI_TOOLS_WORKER_APPLY_V1`、`AI_TOOLS_WORKER_VERIFY_V1`、`AI_TOOLS_DELEGATED_APPLY_V1` 或 `AI_TOOLS_DELEGATED_VERIFY_V1`，当前不是入口 Agent：不得询问用户，不得合并或删除 worktree，把结果返回上级后结束。

同一入口命令在本会话中只询问一次。apply 入口衔接 verify 时，只在整条链路结束后询问，不得在 verify 开始前询问。用户在本命令中选择「保留 worktree」后，本命令不得再次追问。

### 收尾对象（AI_TOOLS_WORKTREE_FINISH_SCOPE_V1）

询问前一次性解析并冻结下列变量；之后不得因切换工作区而重新用 `git rev-parse --show-toplevel` 覆盖 `$FINISH_WORKTREE`：

`GIT_DIR=$(cd "$(git rev-parse --git-dir)" && pwd -P)`；
`GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" && pwd -P)`；
`SUPERPROJECT=$(git rev-parse --show-superproject-working-tree 2>/dev/null || true)`；
`CURRENT_WORKTREE=$(cd "$(git rev-parse --show-toplevel)" && pwd -P)`；
`MAIN_WORKTREE=$(git worktree list --porcelain | awk '/^worktree / {print substr($0,10); exit}')`；
`MAIN_WORKTREE=$(cd "$MAIN_WORKTREE" && pwd -P)`；
`CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)`；
`TARGET_BRANCH=$(git -C "$MAIN_WORKTREE" rev-parse --abbrev-ref HEAD)`。

若本会话按 D 节新建过隔离 worktree，使用当时冻结的 `$SESSION_WORKTREE` 与 `$SESSION_BRANCH`（均须已经 `pwd -P` / 具名分支）。

对 `git worktree list --porcelain` 中每条 `worktree ` 注册路径做 `cd <路径> && pwd -P`，得到规范路径。判断某条已注册 worktree 是否等于 `$SESSION_WORKTREE` 或 `$FINISH_WORKTREE` 时，必须用规范路径全等比较，不得用 `git worktree list` 原文做子串包含。命中后把该条原始注册路径记为 `$FINISH_REMOVE_PATH`，供随后的 `worktree remove` 使用。

按下列顺序确定 `$FINISH_WORKTREE` 与 `$WORKTREE_BRANCH`，只收尾这一对：

1. `$SESSION_WORKTREE` 非空，且存在规范路径与它全等的已注册 worktree：`$FINISH_WORKTREE=$SESSION_WORKTREE`，`$WORKTREE_BRANCH=$SESSION_BRANCH`，`$FINISH_REMOVE_PATH` 为该条注册路径。即使当前已回到主工作区，也收尾这个未清理的会话 worktree。
2. 否则 `$CURRENT_WORKTREE` 不等于 `$MAIN_WORKTREE`，且位于 `$MAIN_WORKTREE/.worktrees/`、`$MAIN_WORKTREE/.worktree/`、`$MAIN_WORKTREE/worktrees/` 或项目明确约定的 worktree 父目录之下：`$FINISH_WORKTREE=$CURRENT_WORKTREE`，`$WORKTREE_BRANCH=$CURRENT_BRANCH`，`$FINISH_REMOVE_PATH` 为规范路径与 `$CURRENT_WORKTREE` 全等的那条注册路径。
3. 其它情况（主工作区且无会话 worktree、submodule、长期手工 worktree、仓库外且不是 `$SESSION_WORKTREE` 的托管 worktree）：跳过询问，不得合并或删除。

满足以下任一也跳过：无法解析 `$MAIN_WORKTREE`；`SUPERPROJECT` 非空且没有 `$SESSION_WORKTREE`；`$FINISH_WORKTREE` 经 `pwd -P` 后等于 `$MAIN_WORKTREE`。

不得把其它已注册路径列入清理范围，不得删除父目录。仓库外的原生 worktree 只在规范路径等于本会话 `$SESSION_WORKTREE` 时收尾。

向用户说明本次 `$FINISH_WORKTREE`、`$WORKTREE_BRANCH`、主工作区、主分支（`$TARGET_BRANCH` 的实际名称），以及该 worktree 是否有未提交改动。

若 `$WORKTREE_BRANCH` 或 `$TARGET_BRANCH` 为 `HEAD`、空或游离：不得提供合并选项，只在该 worktree 干净时提供 `仅清理 worktree，不合并`，并始终提供 `保留 worktree`，同时报告原因。此后清理只删除 worktree 目录，不得执行 `git branch -d HEAD` 或对其它非具名分支名执行 `-d`。

### 询问选项

`$FINISH_WORKTREE` 干净（`git -C "$FINISH_WORKTREE" status --porcelain=v1` 为空）且两分支都是具名分支时提供：

- `合并到主分支并清理 worktree`
- `仅清理 worktree，不合并`
- `保留 worktree`

`$FINISH_WORKTREE` 不干净时不得直接合并或删除。先列出未提交改动，提供：

- `提交后合并到主分支并清理 worktree`：仅在用户明确同意本次提交后，在 `$FINISH_WORKTREE` 提交，再合并并清理
- `保留 worktree`：不提交、不合并、不删除
- 不提供「仅清理」：脏工作区下不得 `worktree remove`，不得暗示可以强删或丢弃未提交改动

用户取消、拒绝回答、拒绝提交或未明确选择时：不得提交、不得合并、不得删除；报告尚未收尾后停止。

### 合并到主分支并清理（AI_TOOLS_WORKTREE_FINISH_MERGE_CLEANUP_V1）

用户明确选择合并并清理后才执行。除「提交后合并」中的提交外，所有 Git 写入必须带 `git -C "$MAIN_WORKTREE"`；提交必须 `git -C "$FINISH_WORKTREE"`。不得在切换后重新解析 `$FINISH_WORKTREE`。`worktree remove` 前必须断言 `$FINISH_WORKTREE` 不等于 `$MAIN_WORKTREE`。不得自动提交（除非用户明确选择「提交后合并」）。不得 stash、`git reset --hard`、`git worktree remove --force`、`git branch -D`，也不得 `rm -rf` 父目录或使用通配符批量删除。清理范围仅限冻结的 `$FINISH_WORKTREE` 与 `$WORKTREE_BRANCH`。

1. 若用户选择了「提交后合并」：先展示 `git -C "$FINISH_WORKTREE" status`，用户明确同意后才 `git -C "$FINISH_WORKTREE" add` 与 `commit`。用户拒绝则停止，保留 worktree。提交后（含 hook 改动）若 `git -C "$FINISH_WORKTREE" status --porcelain=v1` 仍非空：立即停止，不得进入后续合并或删除。
2. 无论是否选择过提交，只要 `$FINISH_WORKTREE` 不干净：停止，不得合并或删除。
3. `git -C "$MAIN_WORKTREE" status --porcelain=v1` 必须为空。主工作区不干净则停止，不得合并或删除本次 worktree。
4. 若 `$WORKTREE_BRANCH` 等于 `$TARGET_BRANCH`，或任一端为 `HEAD` / 空游离：停止，不得合并或删除。
5. 先把本会话工作区根目录切到 `$MAIN_WORKTREE`，优先使用原生切换（例如 `EnterWorktree`）。仅 shell `cd` 不算成功。切不过去：停止。
6. 执行：`git -C "$MAIN_WORKTREE" merge --no-edit "$WORKTREE_BRANCH"`。冲突或非零退出：停止，保留 worktree 与分支。
7. 断言 `$FINISH_WORKTREE` 仍是询问时冻结的绝对路径且不等于 `$MAIN_WORKTREE` 后，执行：`git -C "$MAIN_WORKTREE" worktree remove "$FINISH_REMOVE_PATH"`（不得 `--force`，不得对其它路径执行 remove）。失败则停止。
8. 仅当 `$WORKTREE_BRANCH` 是具名分支（不是 `HEAD`、空或游离）时，再执行：`git -C "$MAIN_WORKTREE" branch -d "$WORKTREE_BRANCH"`（不得 `-D`，不得批量删分支，不得对 `HEAD` 执行 `-d`）。失败则报告分支仍在。
9. 向用户报告：已合并到主分支（名称）、本次 worktree 已删除、本次临时分支是否已删除；并确认其它 worktree 未动。

### 仅清理 worktree

仅当用户明确选择「仅清理」且 `$FINISH_WORKTREE` 干净时执行。先切到 `$MAIN_WORKTREE`，再只执行 `git -C "$MAIN_WORKTREE" worktree remove "$FINISH_REMOVE_PATH"`。之后仅当 `$WORKTREE_BRANCH` 是具名分支且 `git -C "$MAIN_WORKTREE" branch -d "$WORKTREE_BRANCH"` 能安全删除时才删本次分支；`$WORKTREE_BRANCH` 为 `HEAD`、空或游离时不得执行 `branch -d`。否则报告分支仍在，不得用 `-D`，也不得删其它分支。

### 保留 worktree

不提交、不合并、不切换、不删除。报告 `$FINISH_WORKTREE`、`$WORKTREE_BRANCH`、主分支名，以及之后可在主工作区用 `git -C "$MAIN_WORKTREE" merge <分支>` 再 `git -C "$MAIN_WORKTREE" worktree remove` 的提示。
```

首次接入、追加或替换前，以及每次 `openspec update` 或 ai-tools 自定义层升级后，在目标项目根目录运行：

```bash
command -v rg >/dev/null || {
  echo 'ERROR: ripgrep (rg) is required'
  exit 1
}

for file in \
  .cursor/commands/opsx-{propose,apply,verify,sync,archive}.md \
  .cursor/skills/openspec-propose/SKILL.md \
  .cursor/skills/openspec-{apply-change,verify-change,sync-specs,archive-change}/SKILL.md
do
  if [ ! -f "$file" ]; then
    echo "NOFILE    $file"
    continue
  fi
  count="$( { rg -o --fixed-strings 'AI_TOOLS_WORKTREE_FINISH_V1' "$file" || true; } | wc -l | tr -d ' ')"
  case "$count" in
    0) echo "MISSING   $file" ;;
    1)
      required="AI_TOOLS_WORKTREE_FINISH_ASK_ALWAYS_V1 AI_TOOLS_WORKTREE_FINISH_SCOPE_V1 AI_TOOLS_WORKTREE_FINISH_MERGE_CLEANUP_V1"
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

`MISSING` 表示尚无收尾块，只向这 10 个文件追加当前 E 节完整文本。`STALE` 表示文件只有一个 `AI_TOOLS_WORKTREE_FINISH_V1` 标记，但缺少 `AI_TOOLS_WORKTREE_FINISH_ASK_ALWAYS_V1`、`AI_TOOLS_WORKTREE_FINISH_SCOPE_V1` 或 `AI_TOOLS_WORKTREE_FINISH_MERGE_CLEANUP_V1`（含缺少范围收窄、`git -C` 锚定或脏工作区提交询问的旧收尾块）；必须用当前 E 节完整注入文本替换旧收尾块，不得再次追加，也不得改写同文件中的 Verify 门禁块或 propose worktree 块。出现 `DUPLICATE` 时先清理重复收尾块，再按当前文本保留唯一一块。`NOFILE` 表示官方文件不存在，应先运行 `openspec init --tools cursor` 或 `openspec update`。内嵌标记不得把 `AI_TOOLS_WORKTREE_FINISH_V1` 的固定字符串计数抬成 `DUPLICATE`。

在临时目录确认检查脚本（不要改本仓库官方忽略路径）：

```bash
tmp="$(mktemp -d)"
mkdir -p "$tmp/.cursor/commands" "$tmp/.cursor/skills/openspec-propose"
cd "$tmp"

python3 - <<'PY'
def check(text: str) -> str:
    count = text.count('AI_TOOLS_WORKTREE_FINISH_V1')
    if count == 0:
        return 'MISSING'
    if count != 1:
        return f'DUPLICATE ({count})'
    for marker in [
        'AI_TOOLS_WORKTREE_FINISH_ASK_ALWAYS_V1',
        'AI_TOOLS_WORKTREE_FINISH_SCOPE_V1',
        'AI_TOOLS_WORKTREE_FINISH_MERGE_CLEANUP_V1',
    ]:
        if marker not in text:
            return f'STALE (missing {marker})'
    return 'OK'

ok = '''<!-- AI_TOOLS_WORKTREE_FINISH_V1 -->
## 隔离 worktree 收尾（AI_TOOLS_WORKTREE_FINISH_ASK_ALWAYS_V1）
### 收尾对象（AI_TOOLS_WORKTREE_FINISH_SCOPE_V1）
### 合并到主分支并清理（AI_TOOLS_WORKTREE_FINISH_MERGE_CLEANUP_V1）
'''
print(check(''))
print(check('<!-- AI_TOOLS_WORKTREE_FINISH_V1 -->\n旧块\n'))
print(check(ok))
print(ok.count('AI_TOOLS_WORKTREE_FINISH_V1'))
print(check(ok + '\n<!-- AI_TOOLS_WORKTREE_FINISH_V1 -->\n'))
PY
```

预期：

```text
MISSING
STALE (missing AI_TOOLS_WORKTREE_FINISH_ASK_ALWAYS_V1)
OK
1
DUPLICATE (2)
```

完整块中 `AI_TOOLS_WORKTREE_FINISH_V1` 的固定字符串计数必须为 1。另需确认：`.worktrees/` 下同时有多个实例时只 `worktree remove "$FINISH_REMOVE_PATH"`；`git worktree list` 路径经 `pwd -P` 后全等匹配，不得子串包含；提交后 porcelain 仍非空必须停止；`$WORKTREE_BRANCH` 为 `HEAD` 时不得 `branch -d`。

这是对官方生成物的项目级追加，不要用旧版完整文件覆盖新版官方模板。路径 A、B 均须执行本节的 A/B/C、D 与 E；路径 C 在重新生成官方层后也须执行本节的 A/B/C、D 与 E。仅复制 schema 不会自动获得 propose worktree 选择或隔离 worktree 收尾。

### 5.2 已有 active change 怎么办

| 情况 | 建议 |
|------|------|
| change 使用 `spec-driven`，且仍在规划/实现中 | 可继续用原 schema 做完并归档；新 change 再改用 `evidence-driven` |
| 希望中途切到 `evidence-driven` | 需补齐 `verification.md`，并确认 `.openspec.yaml` 的 `schema:`；有行为变化时再改 tasks/specs |
| 纯重构/文档、无规范层变化 | 可设 `skip_specs: true`，仍建议有 `verification` 计划 |

切换默认 schema **不会**自动改写历史 archived changes；只影响之后 `openspec new change` 的默认 schema（除非命令显式传 `--schema`）。

### 5.3 从 `spec-driven` 迁到 `evidence-driven` 的制品差异

```text
spec-driven:   proposal → specs/design → tasks → apply
evidence-driven: proposal → specs/design → tasks → verification → apply
```

官方 command/skills 以 CLI 生成物为基线，并按 5.1 节追加验证闭环与流转门禁。`verification` 的制品依赖通过 schema 的 `apply.requires` 与模板指导进入工作流；该依赖只保证制品存在。入口 Agent 先派发 apply 子 Agent；成功后再派发独立 verify 子 Agent。单独运行 `/opsx-verify` 时，入口 Agent 同样派发 verify 子 Agent。最终由 verification 中持久化的 Verify 门禁决定能否继续 sync 或 archive。

阶段内并行仅当运行时本会话可用 skills 列表含 `dispatching-parallel-agents` 时启用；列表中没有则与仅派发阶段子 Agent 的串行路径相同。磁盘或插件缓存中的 `SKILL.md` 不足以为可用。

propose 的 worktree 选择按 5.1 节 D 段注入，发生在官方 propose 主体之前，不改变后续制品依赖。隔离 worktree 收尾按 5.1 节 E 段注入到 propose / apply / verify / sync / archive 全部 10 个文件，发生在各命令官方主体之后，不改变 Verify 门禁。

## 6. 路径 C：从旧版 ai-tools 迁移

旧版特征通常包括：

- Git 跟踪了 `openspec-explore` … `openspec-sync-specs` 与对应 `opsx-*.md`；
- skill/command 内含「独立验证结论」「代码审查（归档硬门禁）」「Superpowers 对接」等本地段落；
- 可能还有本仓独有的 `openspec-update-change-from-code`（应保留）。

### 6.1 迁移原则

1. **官方层归还官方**：删除本地分叉的官方 skill/command，再用 `openspec update`（或 `init`）重新生成。
2. **自定义层只留明确约定的内容**：`evidence-driven`、5.1 节的 propose worktree 选择、隔离 worktree 收尾、验证闭环与流转门禁及工作区指纹脚本、中文规则、from-code。
3. **不要**把旧分叉文件「合并进」新官方模板；仅在官方生成物上追加带幂等标记的规则，其它旧门禁迁到项目自有 rule/skill。
4. **先备份再删**：至少保留分支或补丁，便于对照旧门禁文案。

### 6.2 推荐步骤

```bash
cd "$TARGET_PROJECT"
git checkout -b chore/migrate-to-ai-tools-official-first

# 0) 备份旧定制（可选但强烈建议）
mkdir -p /tmp/ai-tools-legacy-backup
cp -R .cursor/skills/openspec-apply-change /tmp/ai-tools-legacy-backup/ 2>/dev/null || true
cp .cursor/commands/opsx-apply.md /tmp/ai-tools-legacy-backup/ 2>/dev/null || true

# 1) 从版本控制中移除旧官方副本（路径按仓库实际调整）
git rm -r --ignore-unmatch \
  .cursor/skills/openspec-explore \
  .cursor/skills/openspec-propose \
  .cursor/skills/openspec-update-change \
  .cursor/skills/openspec-apply-change \
  .cursor/skills/openspec-verify-change \
  .cursor/skills/openspec-archive-change \
  .cursor/skills/openspec-sync-specs
git rm --ignore-unmatch \
  .cursor/commands/opsx-explore.md \
  .cursor/commands/opsx-propose.md \
  .cursor/commands/opsx-update.md \
  .cursor/commands/opsx-apply.md \
  .cursor/commands/opsx-verify.md \
  .cursor/commands/opsx-archive.md \
  .cursor/commands/opsx-sync.md

# 2) 升级 CLI 并重新生成官方层
npm install --global @fission-ai/openspec@latest
openspec --version
# 团队升级请改用精确版本，见 7.1 节
openspec update
# 若项目尚不完整，可用：openspec init --tools cursor

# 3) 刷新自定义 schema
mkdir -p openspec/schemas
rm -rf openspec/schemas/evidence-driven
cp -R \
  "$AI_TOOLS_DIR/openspec/schemas/evidence-driven" \
  openspec/schemas/

# 4) 确认 config
# schema: evidence-driven

# 5) 保留 / 重装旁路与中文规则（若仍需要）
mkdir -p .cursor/rules
cp \
  "$AI_TOOLS_DIR/.cursor/rules/openspec-chinese.mdc" \
  .cursor/rules/openspec-chinese.mdc
# from-code：若目录仍在可保留；否则
# npx skills add youpinyao/ai-tools --skill openspec-update-change-from-code

# 6) 校验
openspec schema validate evidence-driven
openspec list --json
```

重新生成官方层后，还必须按 5.1 节向 propose、apply、verify、sync、archive 的 command/skill 追加 propose worktree 选择、隔离 worktree 收尾以及验证闭环与流转门禁。

### 6.3 迁移后行为变化清单（给团队的预期管理）

| 旧版 ai-tools 常见行为 | 迁移后 |
|------------------------|--------|
| apply 结束后强制独立子 Agent verify，并直接修复验证阻塞 | 入口 Agent 先派发 apply 子 Agent，成功后再派发独立 verify 子 Agent；单独运行 `/opsx-verify` 时也由入口 Agent 派发 verify 子 Agent。阶段内是否并行取决于运行时会话 skills 列表是否含 `dispatching-parallel-agents`（按 5.1 节追加验证闭环、委派标记、并行开关与工作者身份标记） |
| sync / archive 前要求 verification 完成且无阻塞 | **保留**（sync/archive 入口分别强制检查） |
| archive 要求固定文案 `验证结论：通过` 且不可确认绕过 | 改为检查结构化 Verify 门禁块，且不可确认绕过 |
| Code Review 作为归档硬门禁 | 不再由本仓库保证 |
| 代码审查作为 verification 必做检查 | **保留**（未处理的 Critical/Important 会阻塞项目级 sync/archive 门禁） |
| Superpowers brainstorming / finishing 写死在 skill | 不再由本仓库保证 |
| propose 直接在当前工作区创建 change | 每次 propose 先询问隔离 worktree 或当前工作区；选择 worktree 时每次都新建独立 worktree（已处于 linked worktree 也不得复用；须切到新工作区根目录，切不过去则停止；原生可在仓库外，手工才锚定主工作区绝对路径），失败不得静默降级（按 5.1 节 D 段追加）。入口命令跑完后若仍在隔离 worktree，必须询问是否合并到主分支并清理（按 5.1 节 E 段追加） |
| `verification.md` 制品 | **保留**（schema 层） |
| 中文规则、from-code | **可保留** |

若业务还需 Code Review 等其它旧硬门禁，迁移完成后单独开 change，用项目自有 rule/skill 重新表达，避免再次深度分叉官方生成路径。

### 6.4 正在进行中的 change

1. 迁移前用旧流程尽量完成或归档关键 change，成本最低。
2. 若必须带着 active change 迁移：
   - 保留 change 目录与 `.openspec.yaml`；
   - 刷新 schema 后运行 `openspec status --change "<name>" --json` 与 `openspec validate "<name>" --type change --strict`；
   - 缺 `verification.md` 时按新模板补齐（规划阶段结果保持「待执行」，须含代码审查章节）；
   - 旧 verification 中「独立验证结论 / 代码审查硬门禁」章节可保留为项目约定；官方 archive 本身不一定检查它们，但 5.1 节追加的项目级门禁会阻止带有未处理 Critical/Important 的 change 流转。

## 7. 日常升级（接入之后）

### 7.1 升级 OpenSpec 官方层

普通使用者可用 `@latest` 快捷安装，但必须立刻核对版本：

```bash
cd "$TARGET_PROJECT"
npm install --global @fission-ai/openspec@latest
openspec --version
openspec update
openspec schema validate evidence-driven
```

团队执行升级时应记录并固定 `npm view` 解析出的精确版本，不要只依赖 `@latest` 的瞬时解析：

```bash
cd "$TARGET_PROJECT"
TARGET_VERSION="$(npm view @fission-ai/openspec version)"
npm install --global "@fission-ai/openspec@$TARGET_VERSION"
test "$(openspec --version)" = "$TARGET_VERSION"
openspec update
openspec schema validate evidence-driven
```

`openspec update` 可能刷新官方 skills/commands。升级完成后必须运行 5.1 节的三套检查并处理 `MISSING`、`STALE`、`DUPLICATE` 或 `NOFILE`：apply/verify/sync/archive 仅 `MISSING` 追加；其 `STALE` 表示旧 V1 块缺少当前委派标记、`AI_TOOLS_PARALLEL_DISPATCH_V1` 或对应工作者标记，须用当前 A/B 节完整文本替换旧块。propose 仅 `MISSING` 追加；其 `STALE` 表示旧块缺少 `AI_TOOLS_PROPOSE_WORKTREE_ASK_ALWAYS_V1`、`AI_TOOLS_PROPOSE_WORKTREE_INDEPENDENT_V1`、`AI_TOOLS_PROPOSE_WORKTREE_WORKSPACE_ROOT_V1`、`AI_TOOLS_PROPOSE_WORKTREE_NO_DOWNGRADE_V1` 或 `AI_TOOLS_PROPOSE_WORKTREE_SESSION_V1`（含仍只有 `AI_TOOLS_PROPOSE_WORKTREE_REUSE_V1`、或未冻结会话 worktree 的块），须用当前 D 节完整文本替换旧块。10 个文件的收尾块仅 `MISSING` 追加；其 `STALE` 表示旧块缺少 `AI_TOOLS_WORKTREE_FINISH_ASK_ALWAYS_V1`、`AI_TOOLS_WORKTREE_FINISH_SCOPE_V1` 或 `AI_TOOLS_WORKTREE_FINISH_MERGE_CLEANUP_V1`，须用当前 E 节完整文本替换旧收尾块。`DUPLICATE` 先清理；10 个文件的三套检查最终必须全部为 `OK`。

### 7.2 升级 ai-tools 自定义层

```bash
# 拉取最新 ai-tools 后
rm -rf "$TARGET_PROJECT/openspec/schemas/evidence-driven"
cp -R \
  "$AI_TOOLS_DIR/openspec/schemas/evidence-driven" \
  "$TARGET_PROJECT/openspec/schemas/"

# 按需更新中文规则、from-code skill
cp \
  "$AI_TOOLS_DIR/.cursor/rules/openspec-chinese.mdc" \
  "$TARGET_PROJECT/.cursor/rules/openspec-chinese.mdc"

cd "$TARGET_PROJECT"
openspec schema validate evidence-driven
```

**禁止**用本仓库完整 `openspec/config.yaml` 覆盖目标配置；只合并 `schema: evidence-driven`。

ai-tools 自定义层升级后也必须运行 5.1 节三套检查脚本，识别并替换 `STALE` 的旧 V1 apply/verify 块（含缺少 `AI_TOOLS_PARALLEL_DISPATCH_V1` 或工作者标记的情况）、`STALE` 的旧 propose worktree 块以及 `STALE` 的旧 worktree 收尾块；验收前 10 个文件的三套检查都应输出 `OK`。

### 7.3 本仓库（ai-tools）自身注意事项

- 不要在 `ai-tools` 仓库根目录对官方路径跑 `openspec init` / `openspec update` 并提交生成物。
- 官方模板对照应在临时目录完成，再手工同步到 `evidence-driven`。

### 7.4 工作流命令、JSON 与目录（OpenSpec 1.10.0）

以下命令与字段均来自 1.10.0 的 `openspec --help`、子命令 help、官方 schema 和临时 `openspec init --tools cursor` 生成物，不要猜测未列出的参数。

| 用途 | 命令 | 1.10.0 说明 |
|------|------|-------------|
| 新项目官方生成层 | `openspec init --tools cursor` | `--tools` 用于非交互指定工具；仍生成 7 组 skill + 7 个 command。官方 apply 在制品缺失时可能提示未随 init 生成的 `/opsx-continue`，不要纳入本仓库忽略清单或 5.1 幂等清单。 |
| 已初始化刷新 | `openspec update` | 更新 instruction 文件；`--force` 可在工具已是最新时仍刷新。 |
| schema 校验 | `openspec schema validate evidence-driven` | schema 子命令仍标为 experimental；`--json` 返回 `name` / `path` / `valid` / `issues`。 |
| 新建 change | `openspec new change "<name>" --schema evidence-driven` | `--schema` 覆盖默认 schema。 |
| 列出 change | `openspec list --json` | 顶层含 `changes`、`root`。`openspec change list` 已弃用。 |
| 制品状态 | `openspec status --change "<name>" --json` | 顶层含 `changeRoot`、`artifactPaths`、`actionContext`、`schemaName`、`planningHome`。 |
| 严格校验 | `openspec validate "<name>" --type change --strict --json` | 未填制品时会失败但返回可解析 JSON。 |
| apply 指令 | `openspec instructions apply --change "<name>" --json` | 顶层含 `state`、`missingArtifacts`、`contextFiles`。`evidence-driven` 在缺少 `verification` 时 `state` 可为 `blocked`。 |
| archive 指令 | `openspec instructions archive --change "<name>" --json` | 官方标明为 advisory，不得当作硬门禁。 |

以 `schemaName` / `--schema` 为准，不要用 `planningHome.defaultSchema`（该字段在 1.10.0 仍可能报 `spec-driven`）。

目录（用 JSON 里的 store-aware 路径，不要写死仓库相对路径）：

- 主规范：`<planningHome.root>/openspec/specs/<capability-path>/spec.md`
- active change：`openspec/changes/<name>/`
- 归档：`<planningHome.changesDir>/archive/`（仓库内通常是 `openspec/changes/archive/`）

官方 `/opsx-propose` / `/opsx-apply` / `/opsx-verify` / `/opsx-sync` / `/opsx-archive` 仍由上述 7 组生成物提供。官方 verify 只输出会话记分卡；官方 archive 对未完成制品或任务仅警告并允许确认继续。项目级 `AI_TOOLS_VERIFY_GATE_V1` 是额外门禁。

## 8. 验收清单

首次接入或任何升级后，必须在目标项目实际运行 5.1 节三套脚本并处理所有异常状态，直到
apply/verify/sync/archive 8 个文件以及 propose 2 个文件的门禁/选择检查全部输出 `OK`，且
这 10 个文件的收尾检查也全部输出 `OK`，然后确认：

- [ ] `openspec --version` 为团队约定并已记录的精确稳定版（升级时用 `@$TARGET_VERSION` 固定，不要只看 `@latest`）。
- [ ] 存在官方 `/opsx-propose`、`/opsx-apply` 等（Cursor 重启后可见）。
- [ ] `openspec/schemas/evidence-driven/schema.yaml` 存在。
- [ ] `openspec/config.yaml` 含 `schema: evidence-driven`，且项目原有 context/rules 未丢。
- [ ] `openspec schema validate evidence-driven` 通过。
- [ ] 旧分叉官方 skill/command 已从 Git 跟踪中移除（路径 C）。
- [ ] 运行 5.1 节三套脚本，8 个 verify 门禁文件与 2 个 propose 文件均输出 `OK`，10 个文件的收尾检查也均输出 `OK`，没有 `MISSING`、`STALE`、`DUPLICATE` 或 `NOFILE`；其中 apply command/skill 含 `AI_TOOLS_DELEGATED_APPLY_V1`、`AI_TOOLS_PARALLEL_DISPATCH_V1` 与 `AI_TOOLS_WORKER_APPLY_V1`，verify command/skill 含 `AI_TOOLS_DELEGATED_VERIFY_V1`、`AI_TOOLS_PARALLEL_DISPATCH_V1` 与 `AI_TOOLS_WORKER_VERIFY_V1`，propose command/skill 含 `AI_TOOLS_PROPOSE_WORKTREE_ASK_ALWAYS_V1`、`AI_TOOLS_PROPOSE_WORKTREE_INDEPENDENT_V1`、`AI_TOOLS_PROPOSE_WORKTREE_WORKSPACE_ROOT_V1`、`AI_TOOLS_PROPOSE_WORKTREE_NO_DOWNGRADE_V1` 与 `AI_TOOLS_PROPOSE_WORKTREE_SESSION_V1`，10 个文件均含 `AI_TOOLS_WORKTREE_FINISH_ASK_ALWAYS_V1`、`AI_TOOLS_WORKTREE_FINISH_SCOPE_V1` 与 `AI_TOOLS_WORKTREE_FINISH_MERGE_CLEANUP_V1`。
- [ ] verify 子 Agent 最多修复复验 3 轮；每次修改代码后都对修复后的完整 diff 重新执行代码审查、更新 verification 的审查范围与结论，且未处理的 Critical/Important 会阻塞通过。
- [ ] sync / archive command/skill 已追加入口门禁：仅 Verify 门禁为“通过、无阻塞”且验证指纹与当前工作区一致时才可继续。
- [ ] `.cursor/scripts/openspec-verification-fingerprint.py` 存在，verify 与 sync/archive 使用同一脚本计算指纹。
- [ ] 8 个 verify 门禁文件各自仅有一个 `AI_TOOLS_VERIFY_GATE_V1` 标记；2 个 propose 文件各自仅有一个 `AI_TOOLS_PROPOSE_WORKTREE_V1` 标记；10 个文件各自仅有一个 `AI_TOOLS_WORKTREE_FINISH_V1` 标记；旧块已按 `STALE` 规则替换而非重复追加。
- [ ] 仍需要时：中文规则、`openspec-update-change-from-code` 可用。
- [ ] 试跑：`/opsx-propose` 小 change，确认启动后先询问隔离 worktree 或当前工作区；若选择隔离 worktree，官方 propose 结束后再询问是否合并到主分支并清理本次 worktree；生成 `verification.md`，且 apply 前依赖满足。

冒烟命令示例：

```bash
cd "$TARGET_PROJECT"
openspec schema validate evidence-driven
openspec new change "smoke-ai-tools-integration" --schema evidence-driven
openspec status --change "smoke-ai-tools-integration" --json
# 1.10.0 顶层应含 changeRoot、artifactPaths、actionContext、schemaName、planningHome
openspec instructions apply --change "smoke-ai-tools-integration" --json
# 未填 verification 时 evidence-driven 的 apply 可为 blocked
openspec validate "smoke-ai-tools-integration" --type change --strict --json
# 验证完毕后可删除该 smoke change 目录，勿归档到生产规格
```

## 9. 常见问题

### 为什么 README 说「不要从 ai-tools 复制官方 templates」？

因为官方层应以 CLI 生成物为准。复制会导致版本漂移，下一次 `openspec update` 也会冲突。`ai-tools` 只保证自定义 schema 目录可复制。

### 接入后官方 verify 变「弱」了？

verify 主体仍跟随官方生成物。OpenSpec 1.10.0 官方 verify 只在会话中输出 Completeness / Correctness / Coherence 记分卡，不写 `verification.md`。增强规则要求无论由 apply 衔接还是单独运行 `/opsx-verify`，都由入口 Agent 派发独立 verify 子 Agent 执行。verify 子 Agent 仅对可安全、在当前 change 范围内且不需要用户决策的阻塞直接修复并重新验证（最多 3 轮）；其余情况停止并将阻塞返回入口 Agent。结构化结论写回 verification，sync/archive 会在各自入口强制检查该结论。若还需要不可绕过的 Code Review 等更严门禁，应另加项目规则或独立 skill。

### 每次 propose 都要选 worktree 吗？已经在 worktree 里呢？

要。安装 5.1 节 D 段后，每次 `/opsx-propose` 或 `openspec-propose` skill 都必须先问，即使工作区干净或已经处于 linked worktree。选择「在当前工作区继续」则原地创建 change。选择「使用隔离 worktree」时：每次都新建独立 worktree（新路径 + 新分支），并必须先把本会话工作区根目录切到新路径；仅 shell `cd` 不算切换成功，切不过去则停止，不得在旧目录写 change。已处于 linked worktree 也不得复用。原生 worktree 可以建在仓库外，只要不嵌套、不复用；手工 `git worktree` 才锚定主工作区父目录并用绝对路径。新分支默认基于当前 `HEAD`，因此工作区独立不等于 Git 历史独立。未提交改动不会自动进入新 worktree。创建失败不得静默改在当前目录继续。未安装该增强块时，官方 propose 仍直接在当前工作区执行。

### 隔离 worktree 跑完后会自动合并吗？

不会。安装 5.1 节 E 段后，入口 Agent 准备结束回复时，只对本次相关 worktree 询问：本会话 `$SESSION_WORKTREE`，或主工作区下 `.worktrees/` / `.worktree/` / `worktrees/`（及项目约定父目录）里的当前路径；路径必须对 `git worktree list --porcelain` 各条做 `pwd -P` 后全等比较。长期手工 worktree 和仓库外、且不是本会话创建的托管 worktree 不问。官方主体失败但本次 worktree 已在时也要问。干净时选项为「合并到主分支并清理」「仅清理」或「保留」；有未提交改动时改为「提交后合并并清理」或「保留」，不得在脏工作区强删。提交后若仍脏必须停止。合并、remove、删分支必须 `git -C "$MAIN_WORKTREE"`；提交才用 `git -C "$FINISH_WORKTREE"`；remove 使用匹配到的注册路径 `$FINISH_REMOVE_PATH`。主工作区不干净、分支游离或未明确选择时停止；游离 HEAD 只删 worktree，不得 `branch -d HEAD`。清理只删本次路径与对应具名分支，不得删兄弟实例或父目录。已接入项目若 D 块缺少 `AI_TOOLS_PROPOSE_WORKTREE_SESSION_V1` 须整块替换，否则仓库外会话 worktree 无法收尾。实施者、调查者与阶段子 Agent 不得询问。apply 入口须等完衔接的 verify 后才问。未安装该收尾块时，跑完后不会提示合并或清理。

### 安装增强规则后还要再装 Superpowers 吗？注入要不要再替换？

不必。`AI_TOOLS_PARALLEL_DISPATCH_V1` 只表示注入已包含阶段内并行规则，不表示 Superpowers 已安装。每次 apply / verify 运行时只看本会话可用 skills 列表是否含 `dispatching-parallel-agents`：没有则走官方串行默认。之后自行安装 Superpowers 且会话列表出现该 skill，无需再次替换注入，下一轮即可启用阶段内并行。卸掉后只要会话列表不再包含该 skill 即回到串行；插件缓存里残留的 `SKILL.md` 不算可用。只有注入文本过期（5.1 节脚本报 `STALE`）才需要用当前 A/B 节替换。并行工作者必须带 `AI_TOOLS_WORKER_APPLY_V1` / `AI_TOOLS_WORKER_VERIFY_V1`，否则会把自己当成入口再派阶段子 Agent。

### `openspec update` 会不会删掉 `evidence-driven`？

一般不会删除 `openspec/schemas/` 下的自定义 schema。但升级后仍应再跑 `openspec schema validate evidence-driven`，并确认 `config.yaml` 的 `schema:` 未被改回 `spec-driven`。

### 可以继续用 `spec-driven` 吗？

可以。不改 `config.yaml` 即保持官方默认。只有需要 `verification` 制品与 apply 前置依赖时，才切换到 `evidence-driven`。

### from-code 与官方 sync 有何区别？

| 命令 | 真源 | 写入范围 |
|------|------|----------|
| `/opsx-update-change-from-code` | 已实现代码 + 用户决策 | active change（及允许的相关文档），**不改** main specs |
| 官方 `/opsx-sync` | change 内 delta specs | main specs |

## 10. 相关文档

- 安装与仓库边界：[README.md](../README.md)
- 场景化工作流：[ai-sdd-workflow.md](./ai-sdd-workflow.md)
- Graphify 可选增强：[graphify-integration.md](./graphify-integration.md)
- 当前维护基线见 README 与本文。历史架构规格 `spec/spec-architecture-openspec-workflow-refactor.md` 已移出版本控制（`.gitignore` 含 `/spec`），本仓库不再跟踪等价文件。
- OpenSpec 上游：https://github.com/Fission-AI/OpenSpec
