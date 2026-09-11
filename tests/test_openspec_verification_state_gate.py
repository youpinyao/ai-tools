from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CURRENT_CONTRACT = (
    ROOT / "README.md",
    ROOT / "docs/ai-sdd-workflow.md",
    ROOT / ".agents/skills/integrating-ai-tools/SKILL.md",
    ROOT / ".agents/skills/integrating-ai-tools/reference.md",
    ROOT / ".agents/skills/upgrading-openspec/reference.md",
)


class VerificationStateGateTest(unittest.TestCase):
    def test_distribution_uses_state_gate_without_fingerprint_tooling(self) -> None:
        self.assertFalse(
            (ROOT / "scripts/openspec-verification-fingerprint.py").exists()
        )
        integration = (CURRENT_CONTRACT[3]).read_text()
        self.assertIn("状态为“通过”", integration)
        self.assertIn("阻塞项为“无”", integration)

    def test_upgrade_removes_legacy_script_and_reverifies_legacy_results(self) -> None:
        integration = (CURRENT_CONTRACT[3]).read_text()
        upgrade = (CURRENT_CONTRACT[4]).read_text()

        self.assertIn("rm -f -- \\", integration)
        self.assertIn(
            '"$TARGET_PROJECT/scripts/openspec-verification-fingerprint.py"',
            integration,
        )
        self.assertIn(
            '"$TARGET_PROJECT/.cursor/scripts/'
            'openspec-verification-fingerprint.py"',
            integration,
        )
        self.assertIn(
            "AI_TOOLS_VERIFICATION_SCOPE_V[12]_(START|END)",
            upgrade,
        )
        self.assertIn("范围摘要：|内容指纹：", upgrade)
        self.assertNotIn("范围内/范围外冒烟测试", upgrade)
        self.assertIn("对所有 `STALE` 文件", upgrade)
        self.assertIn("缺少 `AI_TOOLS_STATE_GATE_V1` 的旧 V2 指纹块", upgrade)


if __name__ == "__main__":
    unittest.main()
