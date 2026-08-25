# OpenSpec 范围指纹与紧凑验证账本实施计划

> **面向 Agent 执行者：** 必须使用 `superpowers:subagent-driven-development`（推荐）
> 或 `superpowers:executing-plans` 逐项实施本计划。所有步骤使用复选框跟踪。

**目标：** 将全工作区 V1 指纹替换为 change 范围内的 V2 指纹，并把
`verification.md` 收敛为低重复、可审计的紧凑验证账本。

**架构：** 仓库维护一个 Python 标准库实现的 V2 指纹脚本和对应集成测试；目标项目从
本仓库复制脚本。`verification.md` 内的范围块定义信任边界，结果块保存范围摘要与内容
指纹；verify 负责生成，sync/archive 负责确定性复核。范围外变化只告警，不阻断。

**技术栈：** Python 3.8+ 标准库、Git CLI、OpenSpec 1.10.0 schema、Markdown、Cursor
commands/skills 注入文本。

## 全局约束

- 设计基线：
  `docs/superpowers/specs/2026-08-25-openspec-scoped-verification-design.md`。
- OpenSpec 相关产物、文档和汇报使用简体中文；代码标识符和 CLI 参数可使用英文。
- 不增加 Python 第三方依赖；目标项目最低要求保持 Python 3.8+。
- `proposal`、`specs`、`design`、`tasks` 继续继承 OpenSpec 1.10.0 官方语义。
- 代码审查仍为 verification 必做项；未处理 Critical / Important 继续阻断。
- V2 范围外变化只告警；范围块、范围内内容或代码审查结论失效时继续硬阻断。
- 模板主体不超过 30 行；机器维护的范围块与结果块不计入该预算。
- 不保留 V1/V2 双重权威状态；V2 写入时删除 V1 结果块。
- 不自动创建 commit。只有用户在执行阶段明确授权提交时，才执行各任务末尾的提交步骤。

## 文件结构

- 新建 `.cursor/scripts/openspec-verification-fingerprint.py`
  - 本仓库维护的 V2 指纹唯一源码；目标项目通过复制安装。
- 新建 `tests/test_openspec_verification_fingerprint.py`
  - 使用临时 Git 仓库验证范围解析、摘要稳定性、范围内阻断和范围外告警。
- 修改 `openspec/schemas/evidence-driven/templates/verification.md`
  - 紧凑验证账本模板。
- 修改 `openspec/schemas/evidence-driven/schema.yaml`
  - 与紧凑账本一致的 verification/apply 指令。
- 修改 `docs/ai-tools-integration.md`
  - 安装 V2 脚本，替换 apply/verify/sync/archive 门禁注入和迁移检查。
- 修改 `docs/ai-sdd-workflow.md`
  - 描述范围门禁数据流和 sync 后 archive 行为。
- 修改 `README.md`
  - 更新能力摘要和接入步骤。
- 修改 `docs/openspec-upgrade-plan.md`
  - 更新静态契约、目标项目冒烟与升级验收。
- 保留 `docs/superpowers/specs/2026-08-25-openspec-scoped-verification-design.md`
  - 已确认的设计依据。

---

### Task 1：实现 V2 范围指纹工具

**文件：**
- 新建：`.cursor/scripts/openspec-verification-fingerprint.py`
- 新建：`tests/test_openspec_verification_fingerprint.py`

**接口：**
- 输入：`python3 .cursor/scripts/openspec-verification-fingerprint.py <verification.md>`
- 输出：

  ```text
  scope_digest=<64 位小写 SHA-256>
  content_digest=<64 位小写 SHA-256>
  outside_changes=<十进制数量>
  outside_path=<仓库相对路径>
  ```

- `outside_path` 可出现零次或多次，按字节序排序；范围外变化不改变退出码。
- 格式错误、路径越界、baseline 无效或范围内 submodule 脏时退出非零并输出明确错误。
- 供后续任务使用的函数：

  ```python
  @dataclass(frozen=True)
  class ScopeRule:
      path: str
      is_prefix: bool

  @dataclass(frozen=True)
  class Scope:
      baseline: str
      include: tuple[ScopeRule, ...]
      exclude: tuple[ScopeRule, ...]

  def parse_scope(document: bytes, verification_relative: str) -> Scope: ...
  def compute_scope_digest(scope: Scope) -> str: ...
  def compute_content_digest(root: Path, scope: Scope, verification_relative: str) -> str: ...
  def list_outside_changes(root: Path, scope: Scope) -> tuple[str, ...]: ...
  ```

- Python 3.8 不支持内建泛型和 `dataclass` 的部分新版语法，实际源码使用
  `Tuple[ScopeRule, ...]`、`List[str]` 等 `typing` 写法。

- [ ] **步骤 1：建立临时仓库测试夹具和范围解析失败测试**

在测试文件中创建可重复使用的夹具：

```python
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".cursor/scripts/openspec-verification-fingerprint.py"


def run(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        cwd=cwd,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class FingerprintTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        run("git", "init", "-q", cwd=self.repo)
        run("git", "config", "user.name", "Test User", cwd=self.repo)
        run("git", "config", "user.email", "test@example.com", cwd=self.repo)
        (self.repo / "src").mkdir()
        (self.repo / "src/app.py").write_text("VALUE = 1\n")
        (self.repo / "notes.md").write_text("initial\n")
        run("git", "add", ".", cwd=self.repo)
        run("git", "commit", "-qm", "baseline", cwd=self.repo)
        self.baseline = run("git", "rev-parse", "HEAD", cwd=self.repo).stdout.strip()
        self.change = self.repo / "openspec/changes/scoped"
        self.change.mkdir(parents=True)
        self.verification = self.change / "verification.md"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_verification(self, include: str = "src/") -> None:
        self.verification.write_text(
            "## 范围\n"
            "<!-- AI_TOOLS_VERIFICATION_SCOPE_V2_START -->\n"
            f"baseline: {self.baseline}\n"
            "include:\n"
            f"- {include}\n"
            "- openspec/changes/scoped/\n"
            "exclude:\n"
            "- none\n"
            "<!-- AI_TOOLS_VERIFICATION_SCOPE_V2_END -->\n"
            "<!-- AI_TOOLS_VERIFICATION_RESULT_V2_START -->\n"
            "- 状态：通过\n"
            "- 阻塞项：无\n"
            "- 范围摘要：PENDING\n"
            "- 内容指纹：PENDING\n"
            "<!-- AI_TOOLS_VERIFICATION_RESULT_V2_END -->\n"
        )

    def invoke(self, check: bool = True) -> subprocess.CompletedProcess:
        return run(
            sys.executable,
            os.fspath(SCRIPT),
            os.fspath(self.verification),
            cwd=self.repo,
            check=check,
        )

    def test_rejects_missing_scope_block(self) -> None:
        self.verification.write_text("## 范围\n")
        result = self.invoke(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exactly one V2 scope block", result.stderr)
```

- [ ] **步骤 2：运行解析测试，确认因脚本不存在而失败**

运行：

```bash
python3 -m unittest tests.test_openspec_verification_fingerprint.FingerprintTest.test_rejects_missing_scope_block -v
```

预期：FAIL，错误表明
`.cursor/scripts/openspec-verification-fingerprint.py` 不存在或无法执行。

- [ ] **步骤 3：实现范围块解析和路径规范化**

脚本必须：

1. 使用正则要求恰好一个 `AI_TOOLS_VERIFICATION_SCOPE_V2` 块。
2. 只接受 `baseline`、`include`、`exclude` 三个字段。
3. 将 `none` 仅解释为无排除项。
4. 拒绝绝对路径、空路径、`.`、`..` 路径段、反斜杠和仓库外路径。
5. 保留末尾 `/` 表示目录前缀，其他路径表示精确文件。
6. 要求 verification 所在 change 目录前缀被 include 命中。
7. 使用 `git cat-file -e "<baseline>^{commit}"` 验证 baseline，并规范化为完整 SHA。

核心解析入口：

```python
SCOPE_PATTERN = re.compile(
    rb"(?ms)^[ \t]*<!-- AI_TOOLS_VERIFICATION_SCOPE_V2_START -->[ \t]*\r?\n"
    rb"(.*?)"
    rb"^[ \t]*<!-- AI_TOOLS_VERIFICATION_SCOPE_V2_END -->[ \t]*\r?\n?"
)


def normalize_rule(raw: str) -> ScopeRule:
    is_prefix = raw.endswith("/")
    value = raw[:-1] if is_prefix else raw
    pure = PurePosixPath(value)
    if (
        not value
        or value == "."
        or pure.is_absolute()
        or "\\" in value
        or any(part in ("", ".", "..") for part in pure.parts)
    ):
        raise ValueError("scope path must be a safe repository-relative POSIX path")
    normalized = pure.as_posix() + ("/" if is_prefix else "")
    return ScopeRule(normalized, is_prefix)
```

- [ ] **步骤 4：补充摘要和范围行为测试**

将 `parse_output` 放在模块级，并把以下测试方法加入步骤 1 创建的
`FingerprintTest` 类：

```python
def parse_output(text: str) -> dict:
    result = {}
    for line in text.splitlines():
        key, value = line.split("=", 1)
        result.setdefault(key, []).append(value)
    return result


    def test_result_block_does_not_change_content_digest(self) -> None:
        self.write_verification()
        first = parse_output(self.invoke().stdout)
        text = self.verification.read_text().replace("PENDING", "0" * 64)
        self.verification.write_text(text)
        second = parse_output(self.invoke().stdout)
        self.assertEqual(first["content_digest"], second["content_digest"])

    def test_scoped_change_changes_content_digest(self) -> None:
        self.write_verification()
        first = parse_output(self.invoke().stdout)
        (self.repo / "src/app.py").write_text("VALUE = 2\n")
        second = parse_output(self.invoke().stdout)
        self.assertNotEqual(first["content_digest"], second["content_digest"])

    def test_outside_change_warns_without_changing_digest(self) -> None:
        self.write_verification()
        first = parse_output(self.invoke().stdout)
        (self.repo / "notes.md").write_text("unrelated\n")
        second = parse_output(self.invoke().stdout)
        self.assertEqual(first["content_digest"], second["content_digest"])
        self.assertEqual(second["outside_changes"], ["1"])
        self.assertEqual(second["outside_path"], ["notes.md"])

    def test_new_untracked_file_under_prefix_changes_digest(self) -> None:
        self.write_verification()
        first = parse_output(self.invoke().stdout)
        (self.repo / "src/new.py").write_text("NEW = True\n")
        second = parse_output(self.invoke().stdout)
        self.assertNotEqual(first["content_digest"], second["content_digest"])
```

另补充：

- 修改范围块会改变 `scope_digest`。
- 删除精确文件会改变 `content_digest`。
- `exclude` 排除的路径只产生范围外告警。
- V1-only 文档被拒绝。
- 路径含 `..` 或绝对路径时被拒绝。
- ignored untracked 文件不参与摘要也不产生范围外告警。
- verification 证据正文变化会改变内容指纹。

- [ ] **步骤 5：实现内容指纹和范围外变化枚举**

实现要求：

- 参与枚举的文件集合为 `git ls-files -z` 与
  `git ls-files --others --exclude-standard -z` 的并集。
- 目录前缀每次重新匹配完整集合；精确路径即使不存在也加入 `<MISSING>`。
- 每个条目使用长度前缀 framing，纳入路径、类型、可执行位和内容。
- symlink 纳入链接目标；submodule 纳入 gitlink commit，范围内 submodule 脏时失败。
- verification 文件在计算前只删除唯一 V2 结果块；范围块和其它正文继续参与摘要。
- 范围外变化集合为 `git diff --name-only -z <baseline> --` 加未忽略 untracked 文件，
  再排除范围命中的路径。

核心 framing：

```python
def add_frame(digest: "hashlib._Hash", label: bytes, data: bytes) -> None:
    digest.update(len(label).to_bytes(8, "big"))
    digest.update(label)
    digest.update(len(data).to_bytes(8, "big"))
    digest.update(data)
```

摘要必须从固定算法标识开始：

```python
add_frame(digest, b"ALGORITHM", b"AI_TOOLS_SCOPED_FINGERPRINT_V2")
```

- [ ] **步骤 6：运行完整指纹测试**

运行：

```bash
python3 -m unittest tests.test_openspec_verification_fingerprint -v
```

预期：全部测试 PASS，退出码 0。

- [ ] **步骤 7：如获提交授权，提交指纹工具**

```bash
git add .cursor/scripts/openspec-verification-fingerprint.py \
  tests/test_openspec_verification_fingerprint.py
git commit -m "feat(openspec): 使用 change 范围计算验证指纹"
```

---

### Task 2：收敛 verification 模板与 schema 指令

**文件：**
- 修改：`openspec/schemas/evidence-driven/templates/verification.md`
- 修改：`openspec/schemas/evidence-driven/schema.yaml:201-226`
- 测试：`tests/test_openspec_verification_contract.py`

**接口：**
- 模板只提供“范围、检查、代码审查、风险与回滚”四个一级章节。
- V2 范围块由 propose/verify 填充，V2 结果块由 verify 维护。
- 检查表列固定为“覆盖项、命令或步骤、状态、证据”。

- [ ] **步骤 1：写模板静态契约失败测试**

创建测试：

```python
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "openspec/schemas/evidence-driven/templates/verification.md"
SCHEMA = ROOT / "openspec/schemas/evidence-driven/schema.yaml"


class VerificationContractTest(unittest.TestCase):
    def test_template_is_compact_and_uses_v2_blocks(self) -> None:
        text = TEMPLATE.read_text()
        headings = [line for line in text.splitlines() if line.startswith("## ")]
        self.assertEqual(headings, [
            "## 范围",
            "## 检查",
            "## 代码审查",
            "## 风险与回滚",
        ])
        self.assertLessEqual(len(text.splitlines()), 30)
        self.assertIn("AI_TOOLS_VERIFICATION_SCOPE_V2_START", text)
        self.assertNotIn("AI_TOOLS_VERIFICATION_RESULT_V1", text)
        self.assertNotIn("## 自动化验证", text)
        self.assertNotIn("## 实际执行结果", text)

    def test_schema_describes_compact_authoritative_state(self) -> None:
        text = SCHEMA.read_text()
        self.assertIn("引用 requirement、scenario 或 task ID", text)
        self.assertIn("更新原检查行", text)
        self.assertIn("范围外变化只告警", text)
        self.assertNotIn("权威状态仅在“实际执行结果”", text)
```

- [ ] **步骤 2：运行契约测试确认失败**

运行：

```bash
python3 -m unittest tests.test_openspec_verification_contract -v
```

预期：FAIL，报告旧模板章节、行数或旧 schema 文案不符合契约。

- [ ] **步骤 3：将模板替换为紧凑结构**

模板主体使用以下内容，不复制长篇策略说明：

```markdown
## 范围

- 基线：<!-- 完整 commit SHA -->
- 包含：<!-- 仓库相对路径或目录前缀 -->
- 排除：无

<!-- AI_TOOLS_VERIFICATION_SCOPE_V2_START -->
baseline: PENDING
include:
- PENDING
exclude:
- none
<!-- AI_TOOLS_VERIFICATION_SCOPE_V2_END -->

## 检查

| 覆盖项 | 命令或步骤 | 状态 | 证据 |
|---|---|---|---|
| <!-- requirement/scenario/task ID --> | <!-- 已确认的真实命令或步骤 --> | 待执行 | |

## 代码审查

- 范围：待执行
- 结论：待执行
- 发现：无

## 风险与回滚

- 剩余风险：无
- 回滚：不适用
```

如果严格按行数计算超过 30 行，优先删除空行和非必要注释，不删除四个章节、表头或范围块。

- [ ] **步骤 4：同步 schema verification/apply 指令**

将 instruction 收敛为以下语义：

- 规划阶段只建立范围候选和检查计划，状态保持“待执行”。
- 覆盖项引用 requirement/scenario/task ID，不复述正文。
- 命令必须来自仓库真实配置。
- 同一检查复验时更新原行，只保存退出码、摘要和证据路径。
- verify 读取完整 diff 并确认 include/exclude；范围外变化只告警。
- 代码审查结论在“代码审查”章节唯一维护。
- 未处理 Critical / Important、失败项或范围歧义继续阻断。

删除对已移除“实际执行结果”章节的引用。apply instruction 只要求更新统一检查表和代码审查
章节，不在 apply 阶段写通过门禁。

- [ ] **步骤 5：运行模板契约和 schema 校验**

运行：

```bash
python3 -m unittest tests.test_openspec_verification_contract -v
openspec schema validate evidence-driven
```

预期：测试全部 PASS；CLI 输出
`Schema 'evidence-driven' is valid`，两个命令退出码均为 0。

- [ ] **步骤 6：如获提交授权，提交模板收敛**

```bash
git add openspec/schemas/evidence-driven/templates/verification.md \
  openspec/schemas/evidence-driven/schema.yaml \
  tests/test_openspec_verification_contract.py
git commit -m "refactor(openspec): 收敛验证账本结构"
```

---

### Task 3：将目标项目门禁升级到 V2

**文件：**
- 修改：`docs/ai-tools-integration.md:185-451`
- 测试：`tests/test_openspec_verification_contract.py`

**接口：**
- 目标项目安装：

  ```bash
  mkdir -p "$TARGET_PROJECT/.cursor/scripts"
  cp "$AI_TOOLS_DIR/.cursor/scripts/openspec-verification-fingerprint.py" \
    "$TARGET_PROJECT/.cursor/scripts/openspec-verification-fingerprint.py"
  ```

- 注入块版本升级为 `AI_TOOLS_VERIFY_GATE_V2`。
- V2 结果字段为“状态、阻塞项、范围摘要、内容指纹”。

- [ ] **步骤 1：扩展静态契约测试并确认失败**

在 `VerificationContractTest` 增加：

```python
INTEGRATION = ROOT / "docs/ai-tools-integration.md"


    def test_integration_uses_v2_gate_and_copies_script(self) -> None:
        text = INTEGRATION.read_text()
        self.assertIn("AI_TOOLS_VERIFY_GATE_V2", text)
        self.assertIn("AI_TOOLS_VERIFICATION_SCOPE_V2_START", text)
        self.assertIn("AI_TOOLS_VERIFICATION_RESULT_V2_START", text)
        self.assertIn(
            'cp "$AI_TOOLS_DIR/.cursor/scripts/openspec-verification-fingerprint.py"',
            text,
        )
        self.assertNotIn("AI_TOOLS_VERIFY_GATE_V1", text)
        self.assertNotIn("AI_TOOLS_VERIFICATION_RESULT_V1_START", text)
```

运行：

```bash
python3 -m unittest \
  tests.test_openspec_verification_contract.VerificationContractTest.test_integration_uses_v2_gate_and_copies_script \
  -v
```

预期：FAIL，指出文档仍使用 V1。

- [ ] **步骤 2：用复制安装替代内嵌 V1 脚本**

删除 `docs/ai-tools-integration.md` 中旧脚本源码，改为：

1. 从 `AI_TOOLS_DIR` 复制 V2 脚本。
2. 运行 `python3 ... --help` 或无副作用解析检查。
3. 说明脚本只覆盖范围声明，范围外变化输出告警。
4. 说明脚本版本与注入块必须同次升级。

- [ ] **步骤 3：更新 Apply 注入**

保留现有入口/apply/verify 子 Agent 编排和防递归语义，仅替换门禁部分：

- 标记改为 `AI_TOOLS_VERIFY_GATE_V2`。
- 入口读取唯一 V2 范围块与结果块。
- apply 子 Agent 不计算摘要；仍负责首次完整 diff 代码审查。
- verify 返回后，入口运行 V2 脚本并比较两个摘要。
- 只有范围内失效、阻塞或 verify 失败才阻止完成；范围外路径作为告警汇报。

- [ ] **步骤 4：更新 Verify 注入**

验证闭环改为：

1. 根据 baseline 与完整 diff 生成候选 include/exclude。
2. 无法区分当前 change 与既有无关改动时停止并询问，不回退全工作区指纹。
3. 每个检查只更新统一表中的原行，不追加每轮历史。
4. 结果证据只保留退出码、摘要和报告路径。
5. 最终写唯一 V2 范围块和结果块；先使用 `PENDING`，运行脚本后回填两个摘要。
6. 删除旧 V1 结果块。
7. 范围外变化写入汇报，不将状态改为阻塞；若判断属于 change，则扩展范围并复验。

- [ ] **步骤 5：更新 Sync/Archive 注入与迁移规则**

入口规则要求：

- 恰好一个 V2 范围块和结果块。
- 状态通过、阻塞项为无、两个摘要与当前输出一致。
- V1-only active change 必须先执行一次 verify，不自动转换。
- 正常 sync 更新未纳入范围的 main spec 时只产生范围外告警；archive 前不重复实现验证。
- 官方 spec validate 失败仍按官方主体处理。

同步更新幂等检查：

- 每个目标文件只允许一个 `AI_TOOLS_VERIFY_GATE_V2`。
- 出现 V1 时标为 `STALE`，以 V2 完整块替换，不追加第二块。
- apply/verify/sync/archive 的现有 worker、delegated、parallel 和 no-finish-ask 标记继续校验。

- [ ] **步骤 6：运行文档契约测试**

运行：

```bash
python3 -m unittest tests.test_openspec_verification_contract -v
```

预期：全部 PASS。

- [ ] **步骤 7：如获提交授权，提交 V2 接入规则**

```bash
git add docs/ai-tools-integration.md tests/test_openspec_verification_contract.py
git commit -m "docs(openspec): 将验证流转门禁升级为范围指纹"
```

---

### Task 4：同步维护文档与升级契约

**文件：**
- 修改：`README.md:35-39,130-150,204-231`
- 修改：`docs/ai-sdd-workflow.md:106-140,242-259`
- 修改：`docs/openspec-upgrade-plan.md:168-247,319-352,389-449,451-552`
- 修改：`tests/test_openspec_verification_contract.py`

**接口：**
- 所有当前维护文档统一使用“V2 范围指纹”“范围外告警”“范围内阻断”。
- 历史 `docs/superpowers/plans/` 与 `docs/superpowers/specs/` 不批量改写旧 V1 事实。

- [ ] **步骤 1：增加当前维护文档一致性失败测试**

将 `CURRENT_DOCS` 放在模块级，并把测试方法加入已有的
`VerificationContractTest` 类：

```python
CURRENT_DOCS = [
    ROOT / "README.md",
    ROOT / "docs/ai-sdd-workflow.md",
    ROOT / "docs/ai-tools-integration.md",
    ROOT / "docs/openspec-upgrade-plan.md",
]


    def test_current_docs_use_scoped_v2_language(self) -> None:
        combined = "\n".join(path.read_text() for path in CURRENT_DOCS)
        self.assertIn("AI_TOOLS_VERIFY_GATE_V2", combined)
        self.assertIn("范围外", combined)
        self.assertNotIn("AI_TOOLS_VERIFY_GATE_V1", combined)
        self.assertNotIn("统一工作区指纹", combined)
```

运行：

```bash
python3 -m unittest \
  tests.test_openspec_verification_contract.VerificationContractTest.test_current_docs_use_scoped_v2_language \
  -v
```

预期：FAIL，列出仍含 V1 或“统一工作区指纹”的当前维护文档。

- [ ] **步骤 2：更新 README**

明确：

- Python 3.8+ 用于范围指纹，不再声称覆盖整个工作区。
- 接入时从本仓库复制脚本。
- `verification.md` 为紧凑账本。
- 范围内变化使门禁失效；范围外变化只告警。
- 正常 sync 后不因 main spec 更新强制重复实现验证。
- 项目级 V2 门禁仍不是 OpenSpec 官方行为。

- [ ] **步骤 3：更新场景工作流**

调整闭环描述：

- verify 先确认 baseline 与范围，再执行检查。
- 每轮复验更新原检查行，不追加完整历史。
- sync/archive 复核范围摘要与内容指纹。
- 范围外变化显示告警；属于 change 时必须扩展范围并复验。
- sync 生成的 main spec 若未在声明范围内，不使 implementation verification 失效。

- [ ] **步骤 4：更新可重复升级计划**

升级计划增加：

- 对比 V2 脚本接口和测试。
- 检查紧凑模板四个章节及 30 行预算。
- 检查目标项目 V1 → V2 替换而非重复追加。
- 在临时 Git 项目执行范围内/范围外冒烟测试。
- 当前维护文档不得残留 V1；历史设计/计划允许保留。
- 目标项目 active V1 change 必须重新 verify。

删除旧静态契约中对“实际执行结果”章节和全工作区指纹的要求。

- [ ] **步骤 5：运行当前文档一致性测试**

运行：

```bash
python3 -m unittest tests.test_openspec_verification_contract -v
```

预期：全部 PASS。

- [ ] **步骤 6：如获提交授权，提交文档同步**

```bash
git add README.md docs/ai-sdd-workflow.md docs/openspec-upgrade-plan.md \
  tests/test_openspec_verification_contract.py
git commit -m "docs(openspec): 说明范围验证与紧凑账本"
```

---

### Task 5：执行端到端冒烟与最终审查

**文件：**
- 验证：`.cursor/scripts/openspec-verification-fingerprint.py`
- 验证：`tests/test_openspec_verification_fingerprint.py`
- 验证：`tests/test_openspec_verification_contract.py`
- 验证：`openspec/schemas/evidence-driven/`
- 验证：`README.md`
- 验证：`docs/`

**接口：**
- 本任务不引入新接口，只验证前四项任务的组合行为。

- [ ] **步骤 1：运行全部 Python 测试**

```bash
python3 -m unittest discover -s tests -v
```

预期：全部测试 PASS，失败数为 0。

- [ ] **步骤 2：校验 schema 和模板预算**

```bash
openspec schema validate evidence-driven
test "$(wc -l < openspec/schemas/evidence-driven/templates/verification.md | tr -d ' ')" -le 30
```

预期：schema 有效，模板总行数不超过 30，退出码均为 0。

- [ ] **步骤 3：运行隔离临时项目冒烟**

创建仓库外临时目录，在其中：

1. `git init` 并提交 baseline。
2. 创建范围内 `src/`、范围外 `notes.md` 和 change `verification.md`。
3. 运行 V2 脚本记录两个摘要。
4. 修改 `notes.md`，确认内容指纹不变且 `outside_changes=1`。
5. 修改 `src/`，确认内容指纹变化。
6. 在 `src/` 新增 untracked 文件，确认内容指纹变化。
7. 修改结果块，确认内容指纹不变。
8. 修改验证证据正文，确认内容指纹变化。

优先直接复用任务 1 的 unittest，不另写一次性业务逻辑；本步骤只用于人工阅读 CLI 输出。

- [ ] **步骤 4：验证当前维护文档无 V1 残留**

```bash
if rg -n 'AI_TOOLS_VERIFY_GATE_V1|AI_TOOLS_VERIFICATION_RESULT_V1|统一工作区指纹' \
  README.md docs/ai-sdd-workflow.md docs/ai-tools-integration.md \
  docs/openspec-upgrade-plan.md openspec/; then
  echo "错误：当前维护文件仍含 V1 语义" >&2
  exit 1
fi
```

预期：`rg` 无匹配，条件体不执行，命令退出码 0。

- [ ] **步骤 5：审查完整差异**

运行：

```bash
git diff --check
git status --short
git diff -- .cursor/scripts tests openspec README.md docs
```

审查要求：

- 没有修改历史 V1 设计/计划以伪造历史。
- 没有改动官方生成的 OpenSpec command/skill 副本。
- V2 标记在当前维护文档中唯一。
- 没有未解释的全仓库硬阻断。
- 模板没有重复计划/结果章节。
- 测试覆盖范围内变化、范围外变化、目录新增文件、结果块排除和非法路径。
- 未处理 Critical / Important 为零。

- [ ] **步骤 6：如获提交授权，提交最终设计与计划**

仅在前序任务提交未包含这些文档，且用户已明确授权时执行：

```bash
git add docs/superpowers/specs/2026-08-25-openspec-scoped-verification-design.md \
  docs/superpowers/plans/2026-08-25-openspec-scoped-verification.md
git commit -m "docs(openspec): 记录范围验证设计与实施计划"
```

## 完成标准

- V2 指纹脚本由本仓库维护，并通过 Python 3.8+ 标准库集成测试。
- 范围内 tracked/staged/unstaged/untracked 变化使内容指纹失效。
- 目录前缀下新增、删除、重命名文件被检测。
- 范围外变化只告警，不改变内容指纹。
- `verification.md` 只有四个一级章节且不超过 30 行。
- 统一检查表不复制 requirement 正文或完整命令输出。
- schema 不再引用已删除的“实际执行结果”章节。
- apply/verify/sync/archive 注入统一使用 V2 范围块和结果块。
- V1 active change 的一次性复验迁移规则明确。
- 正常 sync 产生的范围外 main spec 更新不要求重复实现验证。
- 当前维护文档无 V1 语义残留，历史文档保持原始事实。
- `openspec schema validate evidence-driven`、全部 unittest 与 `git diff --check` 通过。
