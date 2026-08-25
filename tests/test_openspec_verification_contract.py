from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "openspec/schemas/evidence-driven/templates/verification.md"
SCHEMA = ROOT / "openspec/schemas/evidence-driven/schema.yaml"
INTEGRATION = ROOT / "docs/ai-tools-integration.md"


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
