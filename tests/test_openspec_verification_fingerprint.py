import os
from pathlib import Path
import shutil
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


def parse_output(text: str) -> dict:
    result = {}
    for line in text.splitlines():
        key, value = line.split("=", 1)
        result.setdefault(key, []).append(value)
    return result


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

    def test_scope_block_change_changes_scope_digest(self) -> None:
        self.write_verification()
        first = parse_output(self.invoke().stdout)
        self.write_verification(include="notes.md")
        second = parse_output(self.invoke().stdout)
        self.assertNotEqual(first["scope_digest"], second["scope_digest"])

    def test_deleted_exact_file_changes_content_digest(self) -> None:
        self.write_verification(include="src/app.py")
        first = parse_output(self.invoke().stdout)
        (self.repo / "src/app.py").unlink()
        second = parse_output(self.invoke().stdout)
        self.assertNotEqual(first["content_digest"], second["content_digest"])

    def test_excluded_path_only_produces_outside_warning(self) -> None:
        self.write_verification()
        text = self.verification.read_text().replace("- none", "- src/generated.py")
        self.verification.write_text(text)
        first = parse_output(self.invoke().stdout)
        (self.repo / "src/generated.py").write_text("generated\n")
        second = parse_output(self.invoke().stdout)
        self.assertEqual(first["content_digest"], second["content_digest"])
        self.assertEqual(second["outside_path"], ["src/generated.py"])

    def test_rejects_v1_only_document(self) -> None:
        self.verification.write_text(
            "<!-- AI_TOOLS_VERIFICATION_SCOPE_V1_START -->\n"
            "<!-- AI_TOOLS_VERIFICATION_SCOPE_V1_END -->\n"
        )
        result = self.invoke(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exactly one V2 scope block", result.stderr)

    def test_rejects_parent_path_segment(self) -> None:
        self.write_verification(include="../src/")
        result = self.invoke(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("safe repository-relative POSIX path", result.stderr)

    def test_rejects_absolute_path(self) -> None:
        self.write_verification(include="/src/")
        result = self.invoke(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("safe repository-relative POSIX path", result.stderr)

    def test_rejects_path_through_symlink_outside_repository(self) -> None:
        outside = self.repo.parent / (self.repo.name + "-outside")
        outside.mkdir()
        try:
            (outside / "secret.txt").write_text("secret\n")
            (self.repo / "escape").symlink_to(outside, target_is_directory=True)
            self.write_verification(include="escape/secret.txt")
            result = self.invoke(check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("scope path resolves outside the repository", result.stderr)
        finally:
            shutil.rmtree(outside)

    def test_ignored_untracked_file_is_ignored(self) -> None:
        self.write_verification()
        (self.repo / ".gitignore").write_text("src/ignored.py\n")
        run("git", "add", ".gitignore", cwd=self.repo)
        run("git", "commit", "-qm", "ignore generated file", cwd=self.repo)
        self.baseline = run("git", "rev-parse", "HEAD", cwd=self.repo).stdout.strip()
        self.write_verification()
        first = parse_output(self.invoke().stdout)
        (self.repo / "src/ignored.py").write_text("ignored\n")
        second = parse_output(self.invoke().stdout)
        self.assertEqual(first["content_digest"], second["content_digest"])
        self.assertEqual(second["outside_changes"], ["0"])

    def test_verification_evidence_change_changes_content_digest(self) -> None:
        self.write_verification()
        first = parse_output(self.invoke().stdout)
        text = self.verification.read_text() + "\n## 验证证据\n- 已人工复核输出\n"
        self.verification.write_text(text)
        second = parse_output(self.invoke().stdout)
        self.assertNotEqual(first["content_digest"], second["content_digest"])

    def test_rejects_invalid_baseline(self) -> None:
        self.baseline = "not-a-commit"
        self.write_verification()
        result = self.invoke(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("baseline must resolve to a commit", result.stderr)

    def test_rejects_unknown_scope_field(self) -> None:
        self.write_verification()
        text = self.verification.read_text().replace("include:\n", "unexpected: value\ninclude:\n")
        self.verification.write_text(text)
        result = self.invoke(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("only baseline, include, and exclude", result.stderr)

    def test_requires_change_directory_in_include(self) -> None:
        self.write_verification()
        text = self.verification.read_text().replace("- openspec/changes/scoped/\n", "")
        self.verification.write_text(text)
        result = self.invoke(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("verification change directory must be included", result.stderr)

    def test_symlink_target_changes_content_digest(self) -> None:
        (self.repo / "src/link").symlink_to("app.py")
        self.write_verification()
        first = parse_output(self.invoke().stdout)
        (self.repo / "src/link").unlink()
        (self.repo / "src/link").symlink_to("../notes.md")
        second = parse_output(self.invoke().stdout)
        self.assertNotEqual(first["content_digest"], second["content_digest"])

    def test_executable_bit_changes_content_digest(self) -> None:
        self.write_verification()
        first = parse_output(self.invoke().stdout)
        (self.repo / "src/app.py").chmod(0o755)
        second = parse_output(self.invoke().stdout)
        self.assertNotEqual(first["content_digest"], second["content_digest"])

    def test_rejects_dirty_scoped_submodule(self) -> None:
        child = self.repo.parent / (self.repo.name + "-child")
        child.mkdir()
        try:
            run("git", "init", "-q", cwd=child)
            run("git", "config", "user.name", "Test User", cwd=child)
            run("git", "config", "user.email", "test@example.com", cwd=child)
            (child / "module.py").write_text("VALUE = 1\n")
            run("git", "add", ".", cwd=child)
            run("git", "commit", "-qm", "module baseline", cwd=child)
            run(
                "git",
                "-c",
                "protocol.file.allow=always",
                "submodule",
                "add",
                "-q",
                os.fspath(child),
                "modules/child",
                cwd=self.repo,
            )
            run("git", "commit", "-qam", "add submodule", cwd=self.repo)
            self.baseline = run("git", "rev-parse", "HEAD", cwd=self.repo).stdout.strip()
            self.write_verification(include="modules/child")
            (self.repo / "modules/child/module.py").write_text("VALUE = 2\n")
            result = self.invoke(check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("scoped submodule is dirty", result.stderr)
        finally:
            shutil.rmtree(child)
