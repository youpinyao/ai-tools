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
