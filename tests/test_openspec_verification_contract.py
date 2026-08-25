from pathlib import Path
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "openspec/schemas/evidence-driven/templates/verification.md"
SCHEMA = ROOT / "openspec/schemas/evidence-driven/schema.yaml"
INTEGRATION = ROOT / "docs/ai-tools-integration.md"
CURRENT_DOCS = [
    ROOT / "README.md",
    ROOT / "docs/ai-sdd-workflow.md",
    ROOT / "docs/ai-tools-integration.md",
    ROOT / "docs/openspec-upgrade-plan.md",
]


def integration_text() -> str:
    return INTEGRATION.read_text()


def gate_checker_source() -> str:
    match = re.search(
        r"(?ms)^# AI_TOOLS_VERIFY_GATE_CHECKER_V2_START\n"
        r"(.*?)"
        r"^# AI_TOOLS_VERIFY_GATE_CHECKER_V2_END$",
        integration_text(),
    )
    if match is None:
        raise AssertionError("integration document must embed the V2 gate checker")
    return match.group(1)


def classify_gate(kind: str, text: str) -> str:
    with tempfile.TemporaryDirectory() as directory:
        sample = Path(directory) / "sample.md"
        sample.write_text(text)
        result = subprocess.run(
            [sys.executable, "-c", gate_checker_source(), kind, str(sample)],
            check=True,
            capture_output=True,
            text=True,
        )
    return result.stdout.strip()


def gate_block(*markers: str, body: str = "") -> str:
    lines = [
        "<!-- AI_TOOLS_VERIFY_GATE_V2 -->",
        *markers,
        body,
        "<!-- AI_TOOLS_VERIFY_GATE_V2_END -->",
    ]
    return "\n".join(line for line in lines if line) + "\n"


def section(text: str, start: str, end: str) -> str:
    return text.split(start, 1)[1].split(end, 1)[0]


def fenced_bash(text: str, start: str, end: str) -> str:
    body = section(text, start, end)
    match = re.search(r"(?ms)^```bash\n(.*?)^```$", body)
    if match is None:
        raise AssertionError("expected one bash block")
    return match.group(1)


class VerificationContractTest(unittest.TestCase):
    def test_current_docs_each_define_scoped_v2_responsibilities(self) -> None:
        required_by_doc = {
            "README.md": (
                r"AI_TOOLS_VERIFY_GATE_V2",
                r"V2 范围指纹",
                r"范围内变化.{0,40}阻断",
                r"范围外变化.{0,40}告警",
                r"sync.{0,80}main spec.{0,40}不强制重复实现验证",
            ),
            "ai-sdd-workflow.md": (
                r"AI_TOOLS_VERIFY_GATE_V2",
                r"范围摘要与内容\s*指纹",
                r"范围内变化.{0,40}阻断",
                r"范围外变化.{0,40}告警",
                r"sync.{0,100}main spec.{0,60}不.{0,20}重复实现验证",
            ),
            "ai-tools-integration.md": (
                r"AI_TOOLS_VERIFY_GATE_V2",
                r"V2 范围指纹",
                r"范围内变化.{0,40}阻断",
                r"范围外变化.{0,40}告警",
                r"正常 sync.{0,100}main spec.{0,60}不强制复验",
            ),
            "openspec-upgrade-plan.md": (
                r"AI_TOOLS_VERIFY_GATE_V2",
                r"V2 范围指纹",
                r"范围内阻断",
                r"范围外告警",
                r"sync.{0,100}main spec.{0,60}不强制重复实现验证",
            ),
        }
        for path in CURRENT_DOCS:
            text = path.read_text()
            for pattern in required_by_doc[path.name]:
                with self.subTest(path=path.name, pattern=pattern):
                    self.assertRegex(text, re.compile(pattern, re.DOTALL))

    def test_current_docs_reject_legacy_workspace_and_finish_prompt_semantics(
        self,
    ) -> None:
        for path in CURRENT_DOCS:
            text = path.read_text()
            if path == INTEGRATION:
                text = re.sub(
                    r"(?ms)^# AI_TOOLS_VERIFY_GATE_CHECKER_V2_START$.*?"
                    r"^# AI_TOOLS_VERIFY_GATE_CHECKER_V2_END$",
                    "",
                    text,
                )
            compact = re.sub(r"""[`'"\s+]""", "", text)
            with self.subTest(path=path.name, contract="legacy gate"):
                self.assertNotIn("AI_TOOLS_VERIFY_GATE_V1", compact)
            legacy_workspace = re.compile(
                r"(?:统一|确定性|记录的|整个|完整|全)(?:的)?工作区(?:内容)?指纹"
            )
            for match in legacy_workspace.finditer(compact):
                context = compact[max(0, match.start() - 40):match.start()]
                with self.subTest(path=path.name, phrase=match.group(0)):
                    self.assertRegex(
                        context,
                        re.compile(r"(?:不回退|不再|不得|禁止|删除|移除|旧).{0,40}$"),
                    )

        workflow = (ROOT / "docs/ai-sdd-workflow.md").read_text()
        self.assertIn("本轮用户明确要求", workflow)
        self.assertIn("默认保留", workflow)
        self.assertNotRegex(
            workflow,
            re.compile(
                r"WorktreeFinish[^\n]*\|[^|\n]*询问[^|\n]*(?:合并|清理)",
            ),
        )
        self.assertNotRegex(
            workflow,
            re.compile(r"(?<!不得)(?<!不应)主动询问.{0,40}(?:合并|清理|收尾)"),
        )

    def test_upgrade_plan_has_executable_v1_migration_and_scoped_smoke(
        self,
    ) -> None:
        text = (ROOT / "docs/openspec-upgrade-plan.md").read_text()
        required_commands = (
            'SCOPED_SMOKE="$(mktemp -d',
            "trap 'rm -rf \"$SCOPED_SMOKE\"' EXIT",
            'git -C "$SCOPED_SMOKE" init',
            'git -C "$SCOPED_SMOKE" add',
            "commit -qm 'baseline'",
            'BASELINE="$(git -C "$SCOPED_SMOKE" rev-parse HEAD)"',
            "AI_TOOLS_VERIFICATION_SCOPE_V2_START",
            "AI_TOOLS_VERIFICATION_RESULT_V2_START",
            'python3 "$FINGERPRINT_SCRIPT" "$VERIFICATION"',
            'test "$outside_scope_digest" = "$scope_digest"',
            'test "$outside_content_digest" = "$content_digest"',
            'test -n "$inside_content_digest"',
            'test "$inside_content_digest" != "$content_digest"',
            'test "$outside_exit" -eq 0',
            'test "$inside_exit" -ne 0',
            "V1-only active change",
        )
        for command in required_commands:
            with self.subTest(command=command):
                self.assertIn(command, text)
        self.assertRegex(text, re.compile(r"V2 完整块.{0,40}替换"))
        self.assertRegex(text, re.compile(r"(?:禁止|不得).{0,20}追加"))

    def test_upgrade_plan_v1_detector_matches_real_marker_sample(self) -> None:
        text = (ROOT / "docs/openspec-upgrade-plan.md").read_text()
        match = re.search(r"^V1_ACTIVE_PATTERN='([^']+)'$", text, re.MULTILINE)
        self.assertIsNotNone(match)
        assert match is not None
        pattern = match.group(1)
        self.assertNotIn("[[]1[]]", pattern)
        with tempfile.TemporaryDirectory() as directory:
            sample = Path(directory) / "verification.md"
            marker = "AI_TOOLS_VERIFICATION_SCOPE_" + "V1_START"
            sample.write_text("<!-- {} -->\n".format(marker))
            result = subprocess.run(
                ["rg", "-q", pattern, str(sample)],
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_upgrade_plan_smoke_executes_and_restores_fail_fast(self) -> None:
        text = (ROOT / "docs/openspec-upgrade-plan.md").read_text()
        smoke = fenced_bash(
            text,
            "然后执行以下可重复的范围指纹冒烟",
            "预期：初始化、baseline commit",
        )
        self.assertTrue(smoke.startswith("set -euo pipefail\n"))
        required_input = smoke.index(': "${REPRESENTATIVE_TARGET_PROJECT:?')
        absolute_check = smoke.index('case "$REPRESENTATIVE_TARGET_PROJECT" in')
        definition = smoke.index('TARGET_PROJECT="$REPRESENTATIVE_TARGET_PROJECT"')
        script_check = smoke.index('test -f "$FINGERPRINT_SCRIPT"')
        first_use = smoke.index('SCOPED_SMOKE="$(mktemp -d')
        self.assertLess(required_input, absolute_check)
        self.assertLess(absolute_check, definition)
        self.assertLess(definition, script_check)
        self.assertLess(script_check, first_use)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target"
            script = target / ".cursor/scripts/openspec-verification-fingerprint.py"
            script.parent.mkdir(parents=True)
            shutil.copy2(
                ROOT / ".cursor/scripts/openspec-verification-fingerprint.py",
                script,
            )
            environment = os.environ.copy()
            environment.update({
                "AI_TOOLS_DIR": str(ROOT),
                "REPRESENTATIVE_TARGET_PROJECT": str(target),
            })
            success = subprocess.run(
                ["bash", "-c", smoke],
                cwd=ROOT,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(success.returncode, 0, success.stderr)

            missing_script = root / "missing-script-target"
            missing_script.mkdir()
            invalid_environment = dict(environment)
            invalid_environment["REPRESENTATIVE_TARGET_PROJECT"] = str(
                missing_script
            )
            failure = subprocess.run(
                ["bash", "-c", smoke],
                cwd=ROOT,
                env=invalid_environment,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(failure.returncode, 0)

            relative_environment = dict(environment)
            relative_environment["REPRESENTATIVE_TARGET_PROJECT"] = "relative"
            relative = subprocess.run(
                ["bash", "-c", smoke],
                cwd=ROOT,
                env=relative_environment,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(relative.returncode, 0)

            poisoned = smoke.replace(
                '\nrm -rf "$SCOPED_SMOKE"\ntrap - EXIT',
                '\nfalse\nrm -rf "$SCOPED_SMOKE"\ntrap - EXIT',
            )
            restored = subprocess.run(
                ["bash", "-c", poisoned],
                cwd=ROOT,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(restored.returncode, 0)

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

    def test_integration_uses_v2_gate_and_copies_script(self) -> None:
        text = integration_text()
        self.assertIn("AI_TOOLS_VERIFY_GATE_V2", text)
        self.assertIn("AI_TOOLS_VERIFICATION_SCOPE_V2_START", text)
        self.assertIn("AI_TOOLS_VERIFICATION_RESULT_V2_START", text)
        complete_install = (
            r'mkdir -p "\$TARGET_PROJECT/\.cursor/scripts"\n'
            r'cp "\$AI_TOOLS_DIR/\.cursor/scripts/'
            r'openspec-verification-fingerprint\.py" \\\n'
            r'  "\$TARGET_PROJECT/\.cursor/scripts/'
            r'openspec-verification-fingerprint\.py".*?'
            r"ast\.parse.*?\n"
            r'  "\$TARGET_PROJECT/\.cursor/scripts/'
            r'openspec-verification-fingerprint\.py"'
        )
        install_sections = {
            "首次接入": section(
                text,
                "#### V2 范围指纹脚本",
                "#### A. Apply",
            ),
            "日常升级": section(
                text,
                "### 7.2 升级 ai-tools 自定义层",
                "### 7.3 本仓库",
            ),
        }
        for name, install in install_sections.items():
            with self.subTest(name=name):
                self.assertRegex(install, re.compile(complete_install, re.DOTALL))
                self.assertIn("不会生成 __pycache__", install)
        self.assertIn("必须同次升级", install_sections["首次接入"])
        self.assertNotIn("AI_TOOLS_VERIFY_GATE_V1", text)
        self.assertNotIn("AI_TOOLS_VERIFICATION_RESULT_V1_START", text)

    def test_integration_defines_scoped_v2_gate_behavior(self) -> None:
        text = integration_text()
        for required in (
            "基线提交",
            "包含路径",
            "排除路径",
            "状态、阻塞项、范围摘要、内容指纹",
            "范围内变化",
            "范围外变化",
            "告警",
            "扩展范围并复验",
            "无法区分当前 change 与既有无关改动时",
            "不回退全工作区指纹",
            "更新统一表中的原行",
            "退出码、摘要和报告路径",
        ):
            self.assertIn(required, text)

    def test_integration_defines_v2_migration_and_flow_rules(self) -> None:
        text = integration_text()
        for required in (
            "V1-only active change",
            "先执行一次 verify",
            "未纳入范围的 main spec",
            "只产生范围外告警",
            "archive 前不重复实现验证",
            "出现 V1 时标为 `STALE`",
            "以 V2 完整块替换",
            "不得再次追加",
        ):
            self.assertIn(required, text)

    def test_integration_has_balanced_unique_scope_and_result_blocks(self) -> None:
        text = integration_text()
        for marker in (
            "AI_TOOLS_VERIFICATION_SCOPE_V2_START",
            "AI_TOOLS_VERIFICATION_SCOPE_V2_END",
            "AI_TOOLS_VERIFICATION_RESULT_V2_START",
            "AI_TOOLS_VERIFICATION_RESULT_V2_END",
        ):
            occurrences = re.findall(
                rf"(?m)^[ \t]*<!-- {marker} -->[ \t]*$",
                text,
            )
            self.assertEqual(len(occurrences), 1, marker)

    def test_documented_gate_blocks_are_complete_and_self_contained(self) -> None:
        text = integration_text()
        blocks = re.findall(
            r"(?ms)^<!-- AI_TOOLS_VERIFY_GATE_V2 -->\n"
            r".*?"
            r"^<!-- AI_TOOLS_VERIFY_GATE_V2_END -->$",
            text,
        )
        self.assertEqual(len(blocks), 3)
        self.assertEqual(classify_gate("apply", blocks[0]), "OK")
        self.assertEqual(classify_gate("verify", blocks[1]), "OK")
        self.assertEqual(classify_gate("flow", blocks[2]), "OK")

    def test_gate_checker_validates_required_markers_inside_each_block(self) -> None:
        samples = {
            "apply": (
                "AI_TOOLS_DELEGATED_APPLY_V1",
                "AI_TOOLS_PARALLEL_DISPATCH_V1",
                "AI_TOOLS_WORKER_APPLY_V1",
                "AI_TOOLS_VERIFY_GATE_NO_FINISH_ASK_V1",
            ),
            "verify": (
                "AI_TOOLS_DELEGATED_VERIFY_V1",
                "AI_TOOLS_PARALLEL_DISPATCH_V1",
                "AI_TOOLS_WORKER_VERIFY_V1",
                "AI_TOOLS_VERIFY_GATE_NO_FINISH_ASK_V1",
            ),
            "flow": ("AI_TOOLS_VERIFY_GATE_NO_FINISH_ASK_V1",),
        }
        for kind, markers in samples.items():
            with self.subTest(kind=kind):
                self.assertEqual(classify_gate(kind, gate_block(*markers)), "OK")
            for missing in markers:
                with self.subTest(kind=kind, missing=missing):
                    present = tuple(marker for marker in markers if marker != missing)
                    incomplete = gate_block(*present) + missing + "\n"
                    self.assertTrue(
                        classify_gate(kind, incomplete).startswith("STALE"),
                    )

    def test_gate_checker_classifies_invalid_gate_shapes(self) -> None:
        required = (
            "AI_TOOLS_DELEGATED_APPLY_V1",
            "AI_TOOLS_PARALLEL_DISPATCH_V1",
            "AI_TOOLS_WORKER_APPLY_V1",
            "AI_TOOLS_VERIFY_GATE_NO_FINISH_ASK_V1",
        )
        valid = gate_block(*required)
        old_gate = "<!-- AI_TOOLS_VERIFY_GATE_" + "V1 -->\n"
        cases = {
            "MISSING": "",
            "MISSING-inline-marker": (
                "prefix <!-- AI_TOOLS_VERIFY_GATE_V2 --> suffix\n"
            ),
            "STALE-v1-only": old_gate,
            "STALE-mixed": valid + old_gate,
            "STALE-missing-end": valid.replace(
                "<!-- AI_TOOLS_VERIFY_GATE_V2_END -->\n",
                "",
            ),
            "STALE-isolated-end": "<!-- AI_TOOLS_VERIFY_GATE_V2_END -->\n",
            "STALE-conflict": gate_block(
                *required,
                body="入口结束时必须询问 worktree 收尾。",
            ),
            "STALE-conflict-expanded": gate_block(
                *required,
                body="准备结束回复时必须询问本次隔离 worktree 如何处理。",
            ),
            "DUPLICATE": valid + valid,
            "DUPLICATE-two-starts": valid.replace(
                "<!-- AI_TOOLS_VERIFY_GATE_V2 -->\n",
                "<!-- AI_TOOLS_VERIFY_GATE_V2 -->\n"
                "<!-- AI_TOOLS_VERIFY_GATE_V2 -->\n",
            ),
            "DUPLICATE-two-ends": valid.replace(
                "<!-- AI_TOOLS_VERIFY_GATE_V2_END -->\n",
                "<!-- AI_TOOLS_VERIFY_GATE_V2_END -->\n"
                "<!-- AI_TOOLS_VERIFY_GATE_V2_END -->\n",
            ),
        }
        for expected, sample in cases.items():
            with self.subTest(expected=expected):
                actual = classify_gate("apply", sample)
                self.assertTrue(actual.startswith(expected.split("-", 1)[0]), actual)
