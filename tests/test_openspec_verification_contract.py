from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "openspec/schemas/evidence-driven/templates/verification.md"
SCHEMA = ROOT / "openspec/schemas/evidence-driven/schema.yaml"
INTEGRATION = ROOT / "docs/ai-tools-integration.md"


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

    def test_integration_defines_scoped_v2_gate_behavior(self) -> None:
        text = INTEGRATION.read_text()
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
        text = INTEGRATION.read_text()
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
