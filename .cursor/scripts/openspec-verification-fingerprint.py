#!/usr/bin/env python3
import hashlib
import os
import re
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Dict, List, Optional, Set, Tuple


SCOPE_PATTERN = re.compile(
    rb"(?ms)^[ \t]*<!-- AI_TOOLS_VERIFICATION_SCOPE_V2_START -->[ \t]*\r?\n"
    rb"(.*?)"
    rb"^[ \t]*<!-- AI_TOOLS_VERIFICATION_SCOPE_V2_END -->[ \t]*\r?\n?"
)
RESULT_PATTERN = re.compile(
    rb"(?ms)^[ \t]*<!-- AI_TOOLS_VERIFICATION_RESULT_V2_START -->[ \t]*\r?\n"
    rb".*?"
    rb"^[ \t]*<!-- AI_TOOLS_VERIFICATION_RESULT_V2_END -->[ \t]*\r?\n?"
)


@dataclass(frozen=True)
class ScopeRule:
    path: str
    is_prefix: bool


@dataclass(frozen=True)
class Scope:
    baseline: str
    include: Tuple[ScopeRule, ...]
    exclude: Tuple[ScopeRule, ...]


def normalize_rule(raw: str) -> ScopeRule:
    is_prefix = raw.endswith("/")
    value = raw[:-1] if is_prefix else raw
    pure = PurePosixPath(value)
    parts = value.split("/")
    if (
        not value
        or value == "."
        or pure.is_absolute()
        or "\\" in value
        or any(part in ("", ".", "..") for part in parts)
    ):
        raise ValueError("scope path must be a safe repository-relative POSIX path")
    normalized = pure.as_posix() + ("/" if is_prefix else "")
    return ScopeRule(normalized, is_prefix)


def parse_scope(document: bytes, verification_relative: str) -> Scope:
    matches = SCOPE_PATTERN.findall(document)
    if len(matches) != 1:
        raise ValueError("expected exactly one V2 scope block")
    try:
        lines = matches[0].decode("utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise ValueError("V2 scope block must be UTF-8") from error

    baseline: Optional[str] = None
    values: Dict[str, List[str]] = {"include": [], "exclude": []}
    current: Optional[str] = None
    seen: Set[str] = set()
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("- "):
            if current not in ("include", "exclude"):
                raise ValueError("scope list item must follow include or exclude")
            values[current].append(line[2:].strip())
            continue
        match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*):(?:[ \t]*(.*))?", line)
        if match is None or match.group(1) not in ("baseline", "include", "exclude"):
            raise ValueError("scope block accepts only baseline, include, and exclude")
        key, value = match.groups()
        if key in seen:
            raise ValueError("scope fields must appear exactly once")
        seen.add(key)
        current = None
        if key == "baseline":
            if not value:
                raise ValueError("baseline must not be empty")
            baseline = value
        else:
            if value:
                raise ValueError("{} must be a list".format(key))
            current = key

    if seen != {"baseline", "include", "exclude"}:
        raise ValueError("scope requires baseline, include, and exclude")
    if not values["include"]:
        raise ValueError("include must contain at least one path")
    if "none" in values["include"]:
        raise ValueError("none is only valid as the sole exclude item")
    if "none" in values["exclude"]:
        if values["exclude"] != ["none"]:
            raise ValueError("none is only valid as the sole exclude item")
        values["exclude"] = []

    include = tuple(normalize_rule(item) for item in values["include"])
    exclude = tuple(normalize_rule(item) for item in values["exclude"])
    verification_path = PurePosixPath(verification_relative)
    change_prefix = verification_path.parent.as_posix().rstrip("/") + "/"
    if not any(_rule_matches(rule, change_prefix) for rule in include):
        raise ValueError("verification change directory must be included")
    if (
        not any(_rule_matches(rule, verification_relative) for rule in include)
        or any(_rule_matches(rule, verification_relative) for rule in exclude)
    ):
        raise ValueError("verification file must remain in scope after excludes")

    assert baseline is not None
    try:
        subprocess.run(
            ["git", "cat-file", "-e", "{}^{{commit}}".format(baseline)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        full_baseline = subprocess.run(
            ["git", "rev-parse", "{}^{{commit}}".format(baseline)],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout.strip()
    except subprocess.CalledProcessError as error:
        raise ValueError("baseline must resolve to a commit") from error
    return Scope(full_baseline, include, exclude)


def add_frame(digest: "hashlib._Hash", label: bytes, data: bytes) -> None:
    digest.update(len(label).to_bytes(8, "big"))
    digest.update(label)
    digest.update(len(data).to_bytes(8, "big"))
    digest.update(data)


def compute_scope_digest(scope: Scope) -> str:
    digest = hashlib.sha256()
    add_frame(digest, b"ALGORITHM", b"AI_TOOLS_SCOPED_FINGERPRINT_V2")
    add_frame(digest, b"BASELINE", scope.baseline.encode("ascii"))
    for rule in scope.include:
        add_frame(digest, b"INCLUDE", rule.path.encode("utf-8"))
    for rule in scope.exclude:
        add_frame(digest, b"EXCLUDE", rule.path.encode("utf-8"))
    return digest.hexdigest()


def _git_paths(root: Path, *args: str) -> Set[str]:
    output = subprocess.run(
        ["git", "-C", os.fspath(root)] + list(args),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout
    return {os.fsdecode(path) for path in output.split(b"\0") if path}


def _rule_matches(rule: ScopeRule, path: str) -> bool:
    if rule.is_prefix:
        return path == rule.path[:-1] or path.startswith(rule.path)
    return path == rule.path


def _is_scoped(scope: Scope, path: str) -> bool:
    return (
        any(_rule_matches(rule, path) for rule in scope.include)
        and not any(_rule_matches(rule, path) for rule in scope.exclude)
    )


def _index_entry(root: Path, relative: str) -> Tuple[str, str]:
    output = subprocess.run(
        ["git", "-C", os.fspath(root), "ls-files", "-s", "-z", "--", relative],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout
    if not output:
        return "", ""
    metadata = output.split(b"\t", 1)[0].decode("ascii").split()
    return metadata[0], metadata[1]


def _entry_data(root: Path, relative: str, verification_relative: str) -> Tuple[bytes, bytes, bytes]:
    path = root / relative
    if not path.exists() and not path.is_symlink():
        return b"MISSING", b"0", b"<MISSING>"
    if not path.is_symlink():
        try:
            path.resolve().relative_to(root.resolve())
        except ValueError as error:
            raise ValueError(
                "scope path resolves outside the repository: {}".format(relative)
            ) from error

    index_mode, index_oid = _index_entry(root, relative)
    if index_mode == "160000":
        head = subprocess.run(
            ["git", "-C", os.fspath(path), "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "-C", os.fspath(path), "status", "--porcelain"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout
        if dirty or head.decode("ascii") != index_oid:
            raise ValueError("scoped submodule is dirty: {}".format(relative))
        return b"SUBMODULE", b"0", head

    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode):
        return b"SYMLINK", b"0", os.fsencode(os.readlink(os.fspath(path)))
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError("unsupported scoped file type: {}".format(relative))
    content = path.read_bytes()
    if relative == verification_relative:
        matches = RESULT_PATTERN.findall(content)
        if len(matches) != 1:
            raise ValueError("expected exactly one V2 result block")
        content = RESULT_PATTERN.sub(b"", content, count=1)
    executable = b"1" if metadata.st_mode & stat.S_IXUSR else b"0"
    return b"FILE", executable, content


def compute_content_digest(root: Path, scope: Scope, verification_relative: str) -> str:
    paths = _git_paths(root, "ls-files", "-z")
    paths.update(_git_paths(root, "ls-files", "--others", "--exclude-standard", "-z"))
    selected = {path for path in paths if _is_scoped(scope, path)}
    for rule in scope.include:
        if not rule.is_prefix and _is_scoped(scope, rule.path):
            selected.add(rule.path)

    digest = hashlib.sha256()
    add_frame(digest, b"ALGORITHM", b"AI_TOOLS_SCOPED_FINGERPRINT_V2")
    for relative in sorted(selected, key=os.fsencode):
        entry_type, executable, content = _entry_data(root, relative, verification_relative)
        add_frame(digest, b"PATH", os.fsencode(relative))
        add_frame(digest, b"TYPE", entry_type)
        add_frame(digest, b"EXECUTABLE", executable)
        add_frame(digest, b"CONTENT", content)
    return digest.hexdigest()


def list_outside_changes(root: Path, scope: Scope) -> Tuple[str, ...]:
    changed = _git_paths(root, "diff", "--name-only", "-z", scope.baseline, "--")
    changed.update(_git_paths(root, "ls-files", "--others", "--exclude-standard", "-z"))
    return tuple(sorted((path for path in changed if not _is_scoped(scope, path)), key=os.fsencode))


def _repository_root() -> Path:
    output = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()
    return Path(output).resolve()


def main() -> int:
    try:
        if len(sys.argv) != 2:
            raise ValueError("usage: openspec-verification-fingerprint.py <verification.md>")
        root = _repository_root()
        verification = Path(sys.argv[1]).resolve()
        try:
            verification_relative = verification.relative_to(root).as_posix()
        except ValueError as error:
            raise ValueError("verification path must be inside the repository") from error
        document = verification.read_bytes()
        scope = parse_scope(document, verification_relative)
        scope_digest = compute_scope_digest(scope)
        content_digest = compute_content_digest(root, scope, verification_relative)
        outside = list_outside_changes(root, scope)
        print("scope_digest={}".format(scope_digest))
        print("content_digest={}".format(content_digest))
        print("outside_changes={}".format(len(outside)))
        for path in outside:
            print("outside_path={}".format(path))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print("error: {}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
