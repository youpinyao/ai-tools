# 将 ai-tools 接入目标项目

本文面向**其它业务仓库**：说明如何从「仅有官方 OpenSpec」或「旧版 ai-tools（本地定制 skills/commands）」升级并接入当前 `ai-tools`。

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
| 官方生成层 | OpenSpec CLI 为基线，项目补充 propose worktree 选择、验证闭环与流转门禁 | explore / propose / update / apply / verify / archive / sync |
| 自定义层 | ai-tools | `evidence-driven` schema（含 `verification`）、propose worktree 选择、验证闭环与流转门禁、工作区指纹脚本、中文规则、from-code 旁路 |

**不要**再把本仓库里的官方 skill/command 副本拷进业务仓覆盖官方文件。应先由 `openspec init` / `openspec update` 生成官方层，再按本文向 propose、apply、verify、sync、archive 的 command/skill 追加项目规则。本仓库 `.gitignore` 已忽略那 7 组官方路径。

### 1.1 相对纯官方 OpenSpec，你多得到什么

- 默认 schema：`evidence-driven`（官方默认多为 `spec-driven`）。
- 额外制品：`verification.md`（验证计划 + 实现侧真实结果记录，含必做代码审查）。
- 制品依赖：`tasks → verification`，且 `apply` 依赖 `verification`；该 schema 依赖只表示制品已创建，流转门禁另以 verification 中的 Verify 门禁标记为准。
- 代码审查在 verification 中必做：apply 子 Agent 针对完整实现 diff 执行首次审查并记账；verify 子 Agent 每次安全修复代码后，必须针对修复后的完整 diff 重新执行审查并更新结论。未处理的 Critical/Important 会使 Verify 门禁失败，因此也是项目级 sync/archive 流转条件。
- 每次 `/opsx-propose` 或 `openspec-propose` skill 启动时，必须先询问使用隔离 worktree 还是当前工作区；该询问发生在创建 change 或写入任何制品之前。未安装增强规则时，该询问不成立。
- 入口 Agent 先派发 apply 子 Agent；成功后再派发独立 verify 子 Agent。单独运行 `/opsx-verify` 时，入口 Agent 同样派发 verify 子 Agent。apply / verify 阶段仍串行。阶段子 Agent 每次运行时仅当本会话可用 skills 列表中存在 `dispatching-parallel-agents` 时，才对独立域并行派发带工作者身份标记的实施者 / 调查者；列表中没有则按官方默认串行，不得因磁盘或插件缓存中能读到 `SKILL.md` 而启用并行。后续安装该 skill 无需再次替换注入。verify 子 Agent 仅直接修复可安全、在当前 change 范围内且无需用户决策的阻塞并重新验证（最多 3 轮）；遇正式规则列出的其它情况停止并返回入口 Agent。verification 完成且无阻塞项后，才可进入 sync 或 archive。
- 可选：简体中文强制规则、`/opsx-update-change-from-code`。

### 1.2 相对旧版 ai-tools，你不再从本仓库获得什么

旧版曾在仓库内跟踪并深度定制官方 skills/commands（含 Code Review 归档硬门禁、Superpowers finishing 等）。当前版本不再分发整套分叉模板，仅要求在官方生成物上追加 propose worktree 选择、验证闭环与流转门禁。

接入后：

- apply / verify / archive / sync 的主体行为仍以目标项目中**当前官方生成物**为准；项目追加规则负责入口编排（派发 apply/verify 子 Agent）、修复验证阻塞并强制检查流转门禁。
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

安装或更新 OpenSpec 官方 command/skills 后，必须确保 propose、apply、verify、sync、archive 都含当前规则。apply、verify、sync、archive 每个文件只保留一个 `AI_TOOLS_VERIFY_GATE_V1` 增强块；propose command/skill 每个文件只保留一个 `AI_TOOLS_PROPOSE_WORKTREE_V1` 增强块。两套标记不得混写。

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

```markdown
<!-- AI_TOOLS_VERIFY_GATE_V1 -->
## Apply 子 Agent 实施与强制验证

若当前会话已按本节派发过 apply 子 Agent，本节视为已执行，不得因 command 与 skill 同处一个上下文而重复派发。入口 Agent 仍负责等待 apply 子 Agent、在其成功后派发并等待 verify 子 Agent，以及检查 Verify 门禁和工作区指纹，但不得执行官方 apply 主体。

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
```

#### B. Verify：修复、复验并持久化结论

向以下两个文件追加或替换为以下内容（`STALE` 时替换旧块）：

- `.cursor/commands/opsx-verify.md`
- `.cursor/skills/openspec-verify-change/SKILL.md`

```markdown
<!-- AI_TOOLS_VERIFY_GATE_V1 -->
## Verify 入口编排与验证阻塞修复闭环

若当前会话已派发过 verify 子 Agent（无论由本节还是 Apply 节触发），本节视为已执行，不得因 command 与 skill 同处一个上下文而重复派发。入口 Agent 只等待该子 Agent 并读取、汇报最终门禁，不得执行官方 verify 主体。

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
```

#### C. Sync / Archive：入口处强制检查

向以下四个文件追加或替换为以下内容（`STALE` 时替换旧块）：

- `.cursor/commands/opsx-sync.md`
- `.cursor/skills/openspec-sync-specs/SKILL.md`
- `.cursor/commands/opsx-archive.md`
- `.cursor/skills/openspec-archive-change/SKILL.md`

```markdown
<!-- AI_TOOLS_VERIFY_GATE_V1 -->
## Verification 流转门禁

执行任何 sync 或 archive 操作前，必须读取当前 change 的 `verification.md`，并检查唯一的 `AI_TOOLS_VERIFICATION_RESULT_V1` 门禁块。运行 `python3 .cursor/scripts/openspec-verification-fingerprint.py "<当前 change 的 verification.md 路径>"` 重新计算当前工作区指纹；只有门禁块同时包含 `状态：通过`、`阻塞项：无`，且记录的验证指纹与命令输出完全一致时才可继续。

门禁块缺失、状态不是“通过”、阻塞项不是“无”、验证指纹不匹配，或存在多个门禁块时，立即停止；不得通过用户确认绕过。验证后发生的任何代码或制品变化都会使旧门禁失效，应先重新执行 verify，修复阻塞并刷新门禁结果。
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

command 与 skill 使用同一规则正文；仅当官方文件标题层级会与本节冲突时，才把本节 `##` / `###` 降一级，不得改语义。

```markdown
<!-- AI_TOOLS_PROPOSE_WORKTREE_V1 -->
## Propose 起始工作区选择（AI_TOOLS_PROPOSE_WORKTREE_ASK_ALWAYS_V1）

在执行任何官方 propose 主体步骤前，必须先完成工作区选择。不得创建 change、不得分配 change 名称、不得写入 `openspec/changes/` 下任何制品，也不得运行 `openspec new change`。

无论工作区是否干净、是否已经处于 linked worktree，每次 `/opsx-propose` 或 `openspec-propose` skill 调用都必须询问，不得根据状态跳过，不得替用户选择。

向用户说明并提供两个选项：

- `使用隔离 worktree`：基于当前 `HEAD` 准备隔离工作区后再继续官方 propose。当前工作区的未提交改动不会自动出现在新 worktree。
- `在当前工作区继续`：保留当前目录和分支，继续官方 propose。

用户取消、拒绝回答或未明确选择时立即停止，不得继续官方 propose。

### 选择当前工作区

保留当前目录和分支，进入官方 propose。不得创建 worktree，不得切换分支。

### 选择隔离 worktree（AI_TOOLS_PROPOSE_WORKTREE_REUSE_V1）

1. 先检测当前 Git 布局，且必须排除 submodule 误判。依次取：
   `GIT_DIR=$(cd "$(git rev-parse --git-dir)" && pwd -P)`；
   `GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" && pwd -P)`；
   `SUPERPROJECT=$(git rev-parse --show-superproject-working-tree 2>/dev/null || true)`。
2. 若 `SUPERPROJECT` 非空：当前是 submodule，按普通仓库处理，不得当作 linked worktree。
3. 若 `GIT_DIR != GIT_COMMON` 且 `SUPERPROJECT` 为空：已处于 linked worktree。复用当前 worktree，报告路径与当前分支（或 detached HEAD），不得再创建嵌套 worktree，然后进入下方「准备完成后」。
4. 否则（普通 checkout，或 submodule）：优先使用运行环境已有的原生 worktree 能力（例如 `EnterWorktree`、`WorktreeCreate`、`/worktree`）。仅当没有原生能力时才使用 `git worktree`。
5. 手工 `git worktree` 时：
   - 目录优先顺序：项目明确约定 > 已有 `.worktrees/` > 已有 `worktrees/` > 默认 `.worktrees/`。两者都存在时用 `.worktrees/`。
   - 项目内目录必须先运行 `git check-ignore -q <目录>`；未忽略则立即停止并报告，不得在未忽略目录创建 worktree，不得擅自修改 `.gitignore`。
   - 使用尚未占用的临时工作分支和路径，例如 `openspec/propose-<YYYYMMDD-HHMMSS>`。最终 change 名称仍由官方 propose 流程确定，不得预先用 change 名称命名分支。
   - 基于当前 `HEAD` 创建：`git worktree add -b "<branch>" "<path>" HEAD`。不得把未提交改动自动搬运到新 worktree。
   - 不得使用 `git reset --hard`、强制删除分支、`git worktree remove --force` 或其它破坏性清理。
6. 进入目标 worktree 后，执行项目可识别的基础 setup：存在 `package.json` 则安装依赖；存在 `Cargo.toml` 则构建；存在 `requirements.txt` / `pyproject.toml` / `go.mod` 则按对应工具安装。没有这些文件则跳过该项。
7. 再执行项目可识别的基线检查：仓库已有明确测试命令时才运行。没有可识别测试命令则跳过。setup 或基线检查失败时暂停并报告原因；在用户明确同意继续前，不得进入官方 propose。

### 失败处理（AI_TOOLS_PROPOSE_WORKTREE_NO_DOWNGRADE_V1）

用户取消、worktree 创建失败、目录未被忽略、sandbox 拒绝、setup 失败或基线检查失败且用户未明确同意继续时，立即停止并报告原因；不得静默退回当前工作区继续 propose。所有阻塞必须发生在 OpenSpec change 和制品创建之前。

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
      required="AI_TOOLS_PROPOSE_WORKTREE_ASK_ALWAYS_V1 AI_TOOLS_PROPOSE_WORKTREE_REUSE_V1 AI_TOOLS_PROPOSE_WORKTREE_NO_DOWNGRADE_V1"
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

`MISSING` 表示尚无增强块，只向这两个文件追加当前 D 节完整文本。`STALE` 表示文件只有一个 `AI_TOOLS_PROPOSE_WORKTREE_V1` 标记，但缺少 `AI_TOOLS_PROPOSE_WORKTREE_ASK_ALWAYS_V1`、`AI_TOOLS_PROPOSE_WORKTREE_REUSE_V1` 或 `AI_TOOLS_PROPOSE_WORKTREE_NO_DOWNGRADE_V1`；必须用当前 D 节完整注入文本替换旧块，不得再次追加。出现 `DUPLICATE` 时先清理重复块，再按当前文本保留唯一一块。`NOFILE` 表示官方 propose 文件不存在，应先运行 `openspec init --tools cursor` 或 `openspec update`。不要把 propose 块写入 apply/verify/sync/archive 文件，也不要把 `AI_TOOLS_VERIFY_GATE_V1` 写入 propose 文件。

这是对官方生成物的项目级追加，不要用旧版完整文件覆盖新版官方模板。路径 A、B 均须执行本节的 A/B/C 与 D；路径 C 在重新生成官方层后也须执行本节的 A/B/C 与 D。仅复制 schema 不会自动获得 propose worktree 选择。

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

propose 的 worktree 选择按 5.1 节 D 段注入，发生在官方 propose 主体之前，不改变后续制品依赖。

## 6. 路径 C：从旧版 ai-tools 迁移

旧版特征通常包括：

- Git 跟踪了 `openspec-explore` … `openspec-sync-specs` 与对应 `opsx-*.md`；
- skill/command 内含「独立验证结论」「代码审查（归档硬门禁）」「Superpowers 对接」等本地段落；
- 可能还有本仓独有的 `openspec-update-change-from-code`（应保留）。

### 6.1 迁移原则

1. **官方层归还官方**：删除本地分叉的官方 skill/command，再用 `openspec update`（或 `init`）重新生成。
2. **自定义层只留明确约定的内容**：`evidence-driven`、5.1 节的 propose worktree 选择、验证闭环与流转门禁及工作区指纹脚本、中文规则、from-code。
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

重新生成官方层后，还必须按 5.1 节向 propose、apply、verify、sync、archive 的 command/skill 追加 propose worktree 选择以及验证闭环与流转门禁。

### 6.3 迁移后行为变化清单（给团队的预期管理）

| 旧版 ai-tools 常见行为 | 迁移后 |
|------------------------|--------|
| apply 结束后强制独立子 Agent verify，并直接修复验证阻塞 | 入口 Agent 先派发 apply 子 Agent，成功后再派发独立 verify 子 Agent；单独运行 `/opsx-verify` 时也由入口 Agent 派发 verify 子 Agent。阶段内是否并行取决于运行时会话 skills 列表是否含 `dispatching-parallel-agents`（按 5.1 节追加验证闭环、委派标记、并行开关与工作者身份标记） |
| sync / archive 前要求 verification 完成且无阻塞 | **保留**（sync/archive 入口分别强制检查） |
| archive 要求固定文案 `验证结论：通过` 且不可确认绕过 | 改为检查结构化 Verify 门禁块，且不可确认绕过 |
| Code Review 作为归档硬门禁 | 不再由本仓库保证 |
| 代码审查作为 verification 必做检查 | **保留**（未处理的 Critical/Important 会阻塞项目级 sync/archive 门禁） |
| Superpowers brainstorming / finishing 写死在 skill | 不再由本仓库保证 |
| propose 直接在当前工作区创建 change | 每次 propose 先询问隔离 worktree 或当前工作区；选择 worktree 时普通 checkout 先进入新 worktree，已处于 linked worktree 则复用，失败不得静默降级（按 5.1 节 D 段追加） |
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

```bash
cd "$TARGET_PROJECT"
npm install --global @fission-ai/openspec@latest
openspec update
openspec schema validate evidence-driven
```

`openspec update` 可能刷新官方 skills/commands。升级完成后必须运行 5.1 节的两套检查并处理 `MISSING`、`STALE`、`DUPLICATE` 或 `NOFILE`：apply/verify/sync/archive 仅 `MISSING` 追加；其 `STALE` 表示旧 V1 块缺少当前委派标记、`AI_TOOLS_PARALLEL_DISPATCH_V1` 或对应工作者标记，须用当前 A/B 节完整文本替换旧块。propose 仅 `MISSING` 追加；其 `STALE` 表示旧块缺少 `AI_TOOLS_PROPOSE_WORKTREE_ASK_ALWAYS_V1`、`AI_TOOLS_PROPOSE_WORKTREE_REUSE_V1` 或 `AI_TOOLS_PROPOSE_WORKTREE_NO_DOWNGRADE_V1`，须用当前 D 节完整文本替换旧块。`DUPLICATE` 先清理；10 个文件最终必须全部为 `OK`。

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

ai-tools 自定义层升级后也必须运行 5.1 节两套检查脚本，识别并替换 `STALE` 的旧 V1 apply/verify 块（含缺少 `AI_TOOLS_PARALLEL_DISPATCH_V1` 或工作者标记的情况）以及 `STALE` 的旧 propose worktree 块；验收前 10 个文件都应输出 `OK`。

### 7.3 本仓库（ai-tools）自身注意事项

- 不要在 `ai-tools` 仓库根目录对官方路径跑 `openspec init` / `openspec update` 并提交生成物。
- 官方模板对照应在临时目录完成，再手工同步到 `evidence-driven`。

## 8. 验收清单

首次接入或任何升级后，必须在目标项目实际运行 5.1 节两套脚本并处理所有异常状态，直到
apply/verify/sync/archive 8 个文件以及 propose 2 个文件全部输出 `OK`，然后确认：

- [ ] `openspec --version` 为团队约定的最新稳定版。
- [ ] 存在官方 `/opsx-propose`、`/opsx-apply` 等（Cursor 重启后可见）。
- [ ] `openspec/schemas/evidence-driven/schema.yaml` 存在。
- [ ] `openspec/config.yaml` 含 `schema: evidence-driven`，且项目原有 context/rules 未丢。
- [ ] `openspec schema validate evidence-driven` 通过。
- [ ] 旧分叉官方 skill/command 已从 Git 跟踪中移除（路径 C）。
- [ ] 运行 5.1 节两套脚本，8 个 verify 门禁文件与 2 个 propose 文件均输出 `OK`，没有 `MISSING`、`STALE`、`DUPLICATE` 或 `NOFILE`；其中 apply command/skill 含 `AI_TOOLS_DELEGATED_APPLY_V1`、`AI_TOOLS_PARALLEL_DISPATCH_V1` 与 `AI_TOOLS_WORKER_APPLY_V1`，verify command/skill 含 `AI_TOOLS_DELEGATED_VERIFY_V1`、`AI_TOOLS_PARALLEL_DISPATCH_V1` 与 `AI_TOOLS_WORKER_VERIFY_V1`，propose command/skill 含 `AI_TOOLS_PROPOSE_WORKTREE_ASK_ALWAYS_V1`、`AI_TOOLS_PROPOSE_WORKTREE_REUSE_V1` 与 `AI_TOOLS_PROPOSE_WORKTREE_NO_DOWNGRADE_V1`。
- [ ] verify 子 Agent 最多修复复验 3 轮；每次修改代码后都对修复后的完整 diff 重新执行代码审查、更新 verification 的审查范围与结论，且未处理的 Critical/Important 会阻塞通过。
- [ ] sync / archive command/skill 已追加入口门禁：仅 Verify 门禁为“通过、无阻塞”且验证指纹与当前工作区一致时才可继续。
- [ ] `.cursor/scripts/openspec-verification-fingerprint.py` 存在，verify 与 sync/archive 使用同一脚本计算指纹。
- [ ] 8 个 verify 门禁文件各自仅有一个 `AI_TOOLS_VERIFY_GATE_V1` 标记；2 个 propose 文件各自仅有一个 `AI_TOOLS_PROPOSE_WORKTREE_V1` 标记；旧块已按 `STALE` 规则替换而非重复追加。
- [ ] 仍需要时：中文规则、`openspec-update-change-from-code` 可用。
- [ ] 试跑：`/opsx-propose` 小 change，确认启动后先询问隔离 worktree 或当前工作区，生成 `verification.md`，且 apply 前依赖满足。

冒烟命令示例：

```bash
cd "$TARGET_PROJECT"
openspec schema validate evidence-driven
openspec new change "smoke-ai-tools-integration" --schema evidence-driven
openspec status --change "smoke-ai-tools-integration"
# 验证完毕后可删除该 smoke change 目录，勿归档到生产规格
```

## 9. 常见问题

### 为什么 README 说「不要从 ai-tools 复制官方 templates」？

因为官方层应以 CLI 生成物为准。复制会导致版本漂移，下一次 `openspec update` 也会冲突。`ai-tools` 只保证自定义 schema 目录可复制。

### 接入后官方 verify 变「弱」了？

verify 主体仍跟随官方生成物；增强规则要求无论由 apply 衔接还是单独运行 `/opsx-verify`，都由入口 Agent 派发独立 verify 子 Agent 执行。verify 子 Agent 仅对可安全、在当前 change 范围内且不需要用户决策的阻塞直接修复并重新验证（最多 3 轮）；其余情况停止并将阻塞返回入口 Agent。结构化结论写回 verification，sync/archive 会在各自入口强制检查该结论。若还需要不可绕过的 Code Review 等更严门禁，应另加项目规则或独立 skill。

### 每次 propose 都要选 worktree 吗？已经在 worktree 里呢？

要。安装 5.1 节 D 段后，每次 `/opsx-propose` 或 `openspec-propose` skill 都必须先问，即使工作区干净或已经处于 linked worktree。选择「在当前工作区继续」则原地创建 change。选择「使用隔离 worktree」时：普通 checkout 先创建并进入新 worktree；已处于 linked worktree 则复用当前目录，不嵌套创建。未提交改动不会自动进入新 worktree。创建失败不得静默改在当前目录继续。未安装该增强块时，官方 propose 仍直接在当前工作区执行。

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
- 架构规格（官方优先）：[../spec/spec-architecture-openspec-workflow-refactor.md](../spec/spec-architecture-openspec-workflow-refactor.md)
- OpenSpec 上游：https://github.com/Fission-AI/OpenSpec
