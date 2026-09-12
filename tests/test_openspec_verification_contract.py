from pathlib import Path
import json
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
INTEGRATION = ROOT / ".agents/skills/integrating-ai-tools/reference.md"
MIGRATION = ROOT / ".agents/skills/migrating-codex-cursor/SKILL.md"
CURRENT_DOCS = [
    ROOT / "README.md",
    ROOT / "docs/ai-sdd-workflow.md",
    ROOT / ".agents/skills/integrating-ai-tools/reference.md",
    ROOT / ".agents/skills/upgrading-openspec/reference.md",
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


APPLY_GATE_MARKERS = (
    "AI_TOOLS_STATE_GATE_V1",
    "AI_TOOLS_DIRECT_APPLY_V1",
)
VERIFY_GATE_MARKERS = (
    "AI_TOOLS_STATE_GATE_V1",
    "AI_TOOLS_DIRECT_VERIFY_V1",
)
FLOW_GATE_MARKERS = ("AI_TOOLS_STATE_GATE_V1", "AI_TOOLS_VERIFY_FLOW_GATE_V1")


class VerificationContractTest(unittest.TestCase):
    def test_cursor_migration_forbids_commands_and_keeps_one_skill_source(self) -> None:
        text = MIGRATION.read_text()
        self.assertIn("Cursor 不保留 command", text)
        self.assertIn("删除 `.cursor/commands/`", text)
        self.assertIn("不得用 Cursor command 作为薄适配入口", text)
        self.assertIn("只保留 `.agents/skills/<name>/` 中的一份 skill", text)
        self.assertIn("`.cursor/commands/` 不存在或为空", text)

    def test_cross_agent_custom_artifacts_have_single_sources(self) -> None:
        canonical = (
            ROOT / ".agents/skills/openspec-update-change-from-code/SKILL.md",
            ROOT / "AGENTS.md",
            ROOT / "openspec/config.yaml",
        )
        for path in canonical:
            with self.subTest(path=path):
                self.assertTrue(path.is_file())

        legacy = (
            ROOT / ".cursor/skills/openspec-update-change-from-code/SKILL.md",
            ROOT / ".cursor/commands/opsx-update-change-from-code.md",
            ROOT / ".cursor/rules/openspec-chinese.mdc",
            ROOT / ".cursor/scripts/openspec-verification-fingerprint.py",
            ROOT / "scripts/openspec-verification-fingerprint.py",
        )
        for path in legacy:
            with self.subTest(path=path):
                self.assertFalse(path.exists())

        agents = (ROOT / "AGENTS.md").read_text()
        self.assertEqual(
            agents.count("AI_TOOLS_OPENSPEC_CONVERSATION_CHINESE_V1_START"),
            1,
        )
        self.assertEqual(
            agents.count("AI_TOOLS_OPENSPEC_CONVERSATION_CHINESE_V1_END"),
            1,
        )
        self.assertIn("对话、澄清、进度汇报和总结", agents)
        self.assertIn("Commit / PR", agents)

        config = (ROOT / "openspec/config.yaml").read_text()
        self.assertEqual(config.count("AI_TOOLS_OPENSPEC_CHINESE_V1_START"), 1)
        self.assertEqual(config.count("AI_TOOLS_OPENSPEC_CHINESE_V1_END"), 1)
        self.assertIn("语言：中文（简体）", config)
        self.assertNotIn("对话", config)
        self.assertNotIn("Commit / PR", config)

        current = "\n".join(path.read_text() for path in CURRENT_DOCS)
        self.assertIn(".agents/skills/openspec-update-change-from-code", current)
        self.assertIn("AI_TOOLS_OPENSPEC_CHINESE_V1_START", current)
        self.assertIn(
            "AI_TOOLS_OPENSPEC_CONVERSATION_CHINESE_V1_START",
            current,
        )
        self.assertNotIn("Cursor 另有斜杠命令", current)
        self.assertNotIn('cp "$AI_TOOLS_DIR/AGENTS.md"', current)

    def test_openspec_config_context_is_injected_into_artifact_instructions(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            shutil.copytree(
                ROOT / "openspec/schemas/evidence-driven",
                target / "openspec/schemas/evidence-driven",
            )
            shutil.copy2(
                ROOT / "openspec/config.yaml",
                target / "openspec/config.yaml",
            )
            subprocess.run(
                [
                    "openspec",
                    "new",
                    "change",
                    "context-contract-smoke",
                    "--schema",
                    "evidence-driven",
                ],
                cwd=target,
                check=True,
                capture_output=True,
                text=True,
            )
            result = subprocess.run(
                [
                    "openspec",
                    "instructions",
                    "proposal",
                    "--change",
                    "context-contract-smoke",
                    "--json",
                ],
                cwd=target,
                check=True,
                capture_output=True,
                text=True,
            )

        payload = json.loads(result.stdout)
        context = payload["context"]
        self.assertIn("AI_TOOLS_OPENSPEC_CHINESE_V1_START", context)
        self.assertIn("制品正文使用简体中文", context)

    def test_openspec_uses_agents_skills_as_the_only_cross_ide_source(self) -> None:
        current = "\n".join(path.read_text() for path in CURRENT_DOCS)
        self.assertIn("openspec init --tools codex", current)
        self.assertNotIn("openspec init --tools cursor,codex", current)
        self.assertNotIn(".cursor/commands/opsx-{propose,apply,verify,sync,archive}", current)
        self.assertNotIn(".cursor/skills/openspec-{apply-change", current)

        integration = integration_text()
        self.assertIn(
            'rm -rf "$TARGET_PROJECT/.cursor/commands/opsx-"*',
            integration,
        )
        self.assertIn(
            'rm -rf "$TARGET_PROJECT/.cursor/skills/openspec-"*',
            integration,
        )
        self.assertRegex(
            integration,
            re.compile(r"\.agents/skills/.{0,100}唯一", re.DOTALL),
        )

    def test_current_docs_define_state_gate_responsibilities(self) -> None:
        for path in CURRENT_DOCS:
            text = path.read_text()
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertIn("AI_TOOLS_VERIFY_GATE_V2", text)

    def test_current_docs_define_direct_serial_execution_semantics(
        self,
    ) -> None:
        for path in CURRENT_DOCS:
            text = path.read_text()
            relative_path = path.relative_to(ROOT).as_posix()
            for phrase in (
                "当前 Agent",
                "串行",
            ):
                with self.subTest(path=relative_path, phrase=phrase):
                    self.assertIn(phrase, text)

        current = "\n".join(path.read_text() for path in CURRENT_DOCS)
        self.assertNotIn("子 Agent", current)
        self.assertNotIn("dispatching-parallel-agents", current)
        self.assertIn("$openspec-apply-change", current)
        self.assertNotRegex(current, r"\$openspec-apply(?!-change)")

    def test_current_docs_reject_legacy_workspace_semantics(self) -> None:
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

    def test_current_docs_do_not_install_openspec_worktree_enhancements(self) -> None:
        for path in CURRENT_DOCS:
            text = path.read_text()
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertNotRegex(
                    text,
                    re.compile(
                        r"(?m)^<!-- AI_TOOLS_(?:PROPOSE_WORKTREE|WORKTREE_FINISH)"
                    ),
                )

    def test_upgrade_plan_deterministically_removes_legacy_worktree_blocks(
        self,
    ) -> None:
        text = (ROOT / ".agents/skills/upgrading-openspec/reference.md").read_text()
        for required in (
            "AI_TOOLS_PROPOSE_WORKTREE_V1",
            "AI_TOOLS_WORKTREE_FINISH_V1",
            "AI_TOOLS_VERIFY_GATE_NO_FINISH_ASK_V1",
            "旧 worktree 增强",
            "不再提供",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)

        start = "# AI_TOOLS_REMOVE_LEGACY_WORKTREE_SKILLS_V1_START"
        end = "# AI_TOOLS_REMOVE_LEGACY_WORKTREE_SKILLS_V1_END"
        self.assertIn(start, text)
        self.assertIn(end, text)
        cleanup = section(text, start + "\n", end)
        official = (
            "openspec-propose",
            "openspec-apply-change",
            "openspec-verify-change",
            "openspec-sync-specs",
            "openspec-archive-change",
        )
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            skills = target / ".agents/skills"
            for name in official:
                path = skills / name
                path.mkdir(parents=True)
                (path / "SKILL.md").write_text("legacy worktree block")
            from_code = skills / "openspec-update-change-from-code"
            from_code.mkdir()
            sentinel = from_code / "SKILL.md"
            sentinel.write_text("keep from-code")

            result = subprocess.run(
                ["bash", "-eu", "-c", cleanup],
                env={**os.environ, "TARGET_PROJECT": str(target)},
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            for name in official:
                with self.subTest(name=name):
                    self.assertFalse((skills / name).exists())
            self.assertEqual(sentinel.read_text(), "keep from-code")

    def test_exact_version_upgrade_also_cleans_legacy_worktree_blocks(self) -> None:
        text = integration_text()
        exact_upgrade = section(
            text,
            "团队执行升级时应记录并固定 `npm view`",
            "### 7.2 升级 ai-tools 自定义层",
        )
        self.assertIn(
            'rm -rf -- "$TARGET_PROJECT/.agents/skills/$skill_name"',
            exact_upgrade,
        )
        self.assertIn("openspec-update-change-from-code", exact_upgrade)

    def test_integration_docs_distinguish_builtin_review_from_extra_approval(
        self,
    ) -> None:
        text = integration_text()
        self.assertIn("当前 verification 已内置完整 diff 代码审查", text)
        self.assertIn("未处理的 Critical/Important", text)
        self.assertIn("独立审批人", text)


    def test_upgrade_plan_v1_detector_matches_real_marker_sample(self) -> None:
        text = (ROOT / ".agents/skills/upgrading-openspec/reference.md").read_text()
        match = re.search(
            r"^LEGACY_VERIFICATION_PATTERN='([^']+)'$",
            text,
            re.MULTILINE,
        )
        self.assertIsNotNone(match)
        assert match is not None
        pattern = match.group(1)
        self.assertIn("SCOPE_V[12]", pattern)
        with tempfile.TemporaryDirectory() as directory:
            sample = Path(directory) / "verification.md"
            marker = "AI_TOOLS_VERIFICATION_RESULT_" + "V1_START"
            sample.write_text("<!-- {} -->\n".format(marker))
            result = subprocess.run(
                ["rg", "-q", pattern, str(sample)],
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_upgrade_plan_v2_migration_block_executes_fail_fast(self) -> None:
        text = (ROOT / ".agents/skills/upgrading-openspec/reference.md").read_text()
        migration = fenced_bash(
            text,
            "替换后直接运行以下断言：",
            "预期：目标项目自有配置未被整文件覆盖",
        )
        self.assertTrue(migration.startswith("set -euo pipefail\n"))

        gate_paths = (
            ".agents/skills/openspec-apply-change/SKILL.md",
            ".agents/skills/openspec-verify-change/SKILL.md",
            ".agents/skills/openspec-sync-specs/SKILL.md",
            ".agents/skills/openspec-archive-change/SKILL.md",
        )
        markers_by_path = {
            gate_paths[0]: "AI_TOOLS_DIRECT_APPLY_V1",
            gate_paths[1]: "AI_TOOLS_DIRECT_VERIFY_V1",
            gate_paths[2]: "AI_TOOLS_VERIFY_FLOW_GATE_V1",
            gate_paths[3]: "AI_TOOLS_VERIFY_FLOW_GATE_V1",
        }

        def valid_gate(relative: str) -> str:
            return (
                "<!-- AI_TOOLS_VERIFY_GATE_V2 -->\n"
                "current AI_TOOLS_STATE_GATE_V1\n"
                f"current {markers_by_path[relative]}\n"
                "<!-- AI_TOOLS_VERIFY_GATE_V2_END -->\n"
            )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target"
            run_dir = root / "run"
            run_dir.mkdir()

            def reset_target() -> None:
                if target.exists():
                    shutil.rmtree(target)
                for relative in gate_paths:
                    path = target / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(valid_gate(relative))

            def invoke(*, optimize: bool = False) -> subprocess.CompletedProcess:
                environment = os.environ.copy()
                environment.update({
                    "REPRESENTATIVE_TARGET_PROJECT": str(target),
                    "RUN_DIR": str(run_dir),
                })
                if optimize:
                    environment["PYTHONOPTIMIZE"] = "1"
                return subprocess.run(
                    ["bash", "-c", migration],
                    cwd=ROOT,
                    env=environment,
                    check=False,
                    capture_output=True,
                    text=True,
                )

            reset_target()
            for relative in (
                "scripts/openspec-verification-fingerprint.py",
                ".cursor/scripts/openspec-verification-fingerprint.py",
            ):
                path = target / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("legacy")
            self.assertEqual(invoke().returncode, 0)
            self.assertFalse(
                (target / "scripts/openspec-verification-fingerprint.py").exists()
            )
            self.assertFalse(
                (target / ".cursor/scripts/openspec-verification-fingerprint.py").exists()
            )

            reset_target()
            legacy = "<!-- AI_TOOLS_VERIFY_GATE_" + "V1 -->\n"
            (target / gate_paths[0]).write_text(valid_gate(gate_paths[0]) + legacy)
            self.assertNotEqual(invoke().returncode, 0)
            self.assertNotEqual(invoke(optimize=True).returncode, 0)

            reset_target()
            (target / gate_paths[0]).write_text(
                valid_gate(gate_paths[0]) + valid_gate(gate_paths[0])
            )
            self.assertNotEqual(invoke().returncode, 0)

            reset_target()
            (target / gate_paths[0]).unlink()
            self.assertNotEqual(invoke().returncode, 0)

            reset_target()
            (target / gate_paths[0]).write_text("official body only\n")
            self.assertNotEqual(invoke().returncode, 0)

            reset_target()
            (target / gate_paths[0]).write_text(
                valid_gate(gate_paths[0]).replace(
                    "current AI_TOOLS_STATE_GATE_V1",
                    "python3 scripts/openspec-verification-fingerprint.py",
                )
            )
            legacy_gate = invoke()
            self.assertNotEqual(legacy_gate.returncode, 0)
            self.assertIn("legacy fingerprint gate", legacy_gate.stderr)

            reset_target()
            (target / gate_paths[0]).write_text(
                valid_gate(gate_paths[0]).replace(
                    "current AI_TOOLS_DIRECT_APPLY_V1\n",
                    "",
                )
            )
            missing_direct = invoke()
            self.assertNotEqual(missing_direct.returncode, 0)
            self.assertIn("missing required marker", missing_direct.stderr)

            reset_target()
            verification = target / "openspec/changes/legacy/verification.md"
            verification.parent.mkdir(parents=True)
            marker = "AI_TOOLS_VERIFICATION_RESULT_" + "V1_START"
            verification.write_text("<!-- {} -->\n".format(marker))
            active = invoke()
            self.assertNotEqual(active.returncode, 0)
            self.assertNotIn("unbound variable", active.stderr)
            self.assertIn("含旧验证结构", active.stdout)
            report = run_dir / "legacy-verification-changes.txt"
            self.assertIn(str(verification.relative_to(target)), report.read_text())
            self.assertIn(str(verification.relative_to(target)), active.stdout)

            reset_target()
            verification.parent.mkdir(parents=True)
            verification.write_text(
                "<!-- AI_TOOLS_VERIFICATION_SCOPE_V2_START -->\n"
            )
            active = invoke()
            self.assertNotEqual(active.returncode, 0)
            self.assertIn(str(verification.relative_to(target)), report.read_text())


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
        self.assertNotIn("AI_TOOLS_VERIFICATION_SCOPE", text)
        self.assertNotIn("AI_TOOLS_VERIFICATION_RESULT_V1", text)
        self.assertNotIn("## 自动化验证", text)
        self.assertNotIn("## 实际执行结果", text)

    def test_schema_describes_compact_authoritative_state(self) -> None:
        text = SCHEMA.read_text()
        self.assertIn("引用 requirement、scenario 或 task ID", text)
        self.assertIn("更新原检查行", text)
        self.assertIn("确认本次验证范围", text)
        self.assertNotIn("权威状态仅在“实际执行结果”", text)

    def test_integration_uses_v2_state_gate(self) -> None:
        text = integration_text()
        self.assertIn("AI_TOOLS_VERIFY_GATE_V2", text)
        self.assertIn("AI_TOOLS_VERIFICATION_RESULT_V2_START", text)
        self.assertIn("状态为“通过”", text)
        self.assertIn("阻塞项为“无”", text)
        self.assertNotIn("AI_TOOLS_VERIFY_GATE_V1", text)
        self.assertNotIn("AI_TOOLS_VERIFICATION_RESULT_V1_START", text)

    def test_integration_defines_verification_behavior(self) -> None:
        text = integration_text()
        for required in (
            "确认验证范围",
            "无法区分当前 change 与既有无关改动时",
            "更新统一表中的原行",
            "退出码、摘要和报告路径",
        ):
            self.assertIn(required, text)

    def test_integration_defines_v2_migration_and_flow_rules(self) -> None:
        text = integration_text()
        for required in (
            "V1-only active change",
            "先执行一次 verify",
            "sync / archive 不比较验证完成后的代码或证据变化",
            "出现 V1 或缺少状态门禁标记时标为 `STALE`",
            "以当前 V2 完整块替换",
            "不得再次追加",
        ):
            self.assertIn(required, text)

    def test_integration_has_one_result_block(self) -> None:
        text = integration_text()
        for marker in (
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

    def test_apply_and_verify_blocks_require_direct_serial_execution(self) -> None:
        text = integration_text()
        blocks = re.findall(
            r"(?ms)^<!-- AI_TOOLS_VERIFY_GATE_V2 -->\n"
            r".*?"
            r"^<!-- AI_TOOLS_VERIFY_GATE_V2_END -->$",
            text,
        )
        self.assertEqual(len(blocks), 3)
        apply_block, verify_block, _ = blocks
        self.assertIn("AI_TOOLS_DIRECT_APPLY_V1", apply_block)
        self.assertIn("当前 Agent", apply_block)
        self.assertIn("串行", apply_block)
        self.assertIn("AI_TOOLS_DIRECT_VERIFY_V1", verify_block)
        self.assertIn("当前 Agent", verify_block)
        self.assertIn("串行", verify_block)

        forbidden = (
            "子 Agent",
            "dispatching-parallel-agents",
            "AI_TOOLS_DELEGATED_",
            "AI_TOOLS_WORKER_",
            "AI_TOOLS_PARALLEL_",
            "AI_TOOLS_DISPATCH_FALLBACK_V1",
        )
        for kind, block in (("apply", apply_block), ("verify", verify_block)):
            for marker in forbidden:
                with self.subTest(kind=kind, marker=marker):
                    self.assertNotIn(marker, block)

    def test_gate_checker_validates_required_markers_inside_each_block(self) -> None:
        samples = {
            "apply": APPLY_GATE_MARKERS,
            "verify": VERIFY_GATE_MARKERS,
            "flow": FLOW_GATE_MARKERS,
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

    def test_gate_checker_rejects_removed_dispatch_markers(self) -> None:
        removed_markers = (
            "AI_TOOLS_DELEGATED_APPLY_V1",
            "AI_TOOLS_WORKER_VERIFY_V1",
            "AI_TOOLS_PARALLEL_HANDOFF_V1_START",
            "AI_TOOLS_DISPATCH_FALLBACK_V1",
        )
        for kind, markers in (
            ("apply", APPLY_GATE_MARKERS),
            ("verify", VERIFY_GATE_MARKERS),
        ):
            for removed in removed_markers:
                with self.subTest(kind=kind, removed=removed):
                    status = classify_gate(
                        kind,
                        gate_block(*markers, body=removed),
                    )
                    self.assertTrue(status.startswith("STALE"), status)

    def test_gate_checker_rejects_legacy_fingerprint_v2_blocks(self) -> None:
        legacy_body = (
            "python3 scripts/openspec-verification-fingerprint.py\n"
            "AI_TOOLS_VERIFICATION_SCOPE_V2_START\n"
            "scope_digest content_digest 范围摘要： 内容指纹：\n"
        )
        samples = {
            "apply": APPLY_GATE_MARKERS,
            "verify": VERIFY_GATE_MARKERS,
            "flow": FLOW_GATE_MARKERS,
        }
        for kind, markers in samples.items():
            with self.subTest(kind=kind):
                legacy_markers = tuple(
                    marker for marker in markers
                    if marker != "AI_TOOLS_STATE_GATE_V1"
                )
                status = classify_gate(
                    kind,
                    gate_block(*legacy_markers, body=legacy_body),
                )
                self.assertTrue(status.startswith("STALE"), status)

    def test_gate_checker_classifies_invalid_gate_shapes(self) -> None:
        required = APPLY_GATE_MARKERS
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
