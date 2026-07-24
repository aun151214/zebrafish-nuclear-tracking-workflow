from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


FORBIDDEN_DIRECTORY_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "audit",
    "legacy_reference",
}

FORBIDDEN_DIRECTORY_SUFFIXES = {
    ".egg-info",
}

FORBIDDEN_ROOT_DIRECTORIES = {
    "data",
    "raw_data",
    "output",
    "outputs",
    "result",
    "results",
    "logs",
    "tmp",
    "cache",
}

FORBIDDEN_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".tif",
    ".tiff",
    ".h5",
    ".hdf5",
    ".mat",
    ".mastodon",
    ".gif",
    ".mp4",
    ".zip",
    ".tar",
    ".tgz",
}

FORBIDDEN_ROOT_FILES = {
    "APPLY_INSTRUCTIONS.txt",
    "secrets.env",
    "local_config.yaml",
}

FORBIDDEN_ROOT_GLOBS = (
    "APPLY_STAGE*_INSTRUCTIONS.txt",
)

# The fragments are deliberately separated so this checker does not flag its
# own source file while still reconstructing the full local path patterns at
# runtime.
ABSOLUTE_LOCAL_PATTERNS = (
    "/data/" "aun",
    "/scratch/" "aun",
    "/mnt/" "svnas1_oates",
    "/home/" "aun",
    "sv-" "nas1",
    "rcp." "epfl.ch",
)

# These markers are also assembled from fragments so the scanner does not
# report its own detection rules as private keys.
PRIVATE_KEY_MARKERS = (
    "-----BEGIN " + "RSA PRIVATE KEY-----",
    "-----BEGIN " + "OPENSSH PRIVATE KEY-----",
    "-----BEGIN " + "EC PRIVATE KEY-----",
)

LIKELY_SECRET_ASSIGNMENT = re.compile(
    r"""(?ix)
    \b(password|passwd|secret|api[_-]?key|access[_-]?token|private[_-]?key)
    \s*[:=]\s*
    ["'][^"'\n]{4,}["']
    """
)

TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".toml",
    ".json",
    ".cff",
    ".ini",
    ".cfg",
    ".sh",
}

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024


@dataclass(frozen=True)
class CleanlinessIssue:
    category: str
    path: str
    detail: str


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def scan_repository(root: str | Path) -> list[CleanlinessIssue]:
    root_path = Path(root).resolve()
    if not root_path.is_dir():
        raise NotADirectoryError(root_path)

    issues: list[CleanlinessIssue] = []

    for directory_name in sorted(FORBIDDEN_ROOT_DIRECTORIES):
        candidate = root_path / directory_name
        if candidate.exists():
            issues.append(
                CleanlinessIssue(
                    category="generated-root-directory",
                    path=directory_name,
                    detail="Generated or local data directory is present.",
                )
            )

    for filename in sorted(FORBIDDEN_ROOT_FILES):
        candidate = root_path / filename
        if candidate.exists():
            issues.append(
                CleanlinessIssue(
                    category="forbidden-root-file",
                    path=filename,
                    detail="Private or staging-only root file is present.",
                )
            )

    for pattern in FORBIDDEN_ROOT_GLOBS:
        for candidate in sorted(root_path.glob(pattern)):
            issues.append(
                CleanlinessIssue(
                    category="staging-instruction",
                    path=_relative(candidate, root_path),
                    detail=(
                        "Stage-application instructions must stay outside "
                        "the clean repository."
                    ),
                )
            )

    for path in sorted(root_path.rglob("*")):
        relative = _relative(path, root_path)

        if ".git" in path.parts:
            continue

        if path.is_dir():
            if path.name in FORBIDDEN_DIRECTORY_NAMES:
                issues.append(
                    CleanlinessIssue(
                        category="forbidden-directory",
                        path=relative,
                        detail=(
                            f"Directory name {path.name!r} is not "
                            "release-clean."
                        ),
                    )
                )
            elif any(
                path.name.endswith(suffix)
                for suffix in FORBIDDEN_DIRECTORY_SUFFIXES
            ):
                issues.append(
                    CleanlinessIssue(
                        category="generated-package-metadata",
                        path=relative,
                        detail=(
                            "Generated package metadata must not be included "
                            "in the release archive."
                        ),
                    )
                )
            continue

        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            issues.append(
                CleanlinessIssue(
                    category="forbidden-binary-or-archive",
                    path=relative,
                    detail=f"Forbidden suffix: {path.suffix.lower()}",
                )
            )

        try:
            size = path.stat().st_size
        except OSError as error:
            issues.append(
                CleanlinessIssue(
                    category="unreadable-file",
                    path=relative,
                    detail=str(error),
                )
            )
            continue

        if size > MAX_FILE_SIZE_BYTES:
            issues.append(
                CleanlinessIssue(
                    category="large-file",
                    path=relative,
                    detail=(
                        f"{size} bytes exceeds "
                        f"{MAX_FILE_SIZE_BYTES} bytes."
                    ),
                )
            )

        if path.suffix.lower() not in TEXT_SUFFIXES and path.name != ".gitignore":
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        for pattern in ABSOLUTE_LOCAL_PATTERNS:
            if pattern in text:
                issues.append(
                    CleanlinessIssue(
                        category="local-absolute-path",
                        path=relative,
                        detail=(
                            "Contains local path or host pattern: "
                            f"{pattern}"
                        ),
                    )
                )

        for marker in PRIVATE_KEY_MARKERS:
            if marker in text:
                issues.append(
                    CleanlinessIssue(
                        category="private-key",
                        path=relative,
                        detail=(
                            "Contains private-key marker: "
                            f"{marker}"
                        ),
                    )
                )

        if LIKELY_SECRET_ASSIGNMENT.search(text):
            issues.append(
                CleanlinessIssue(
                    category="likely-secret",
                    path=relative,
                    detail="Contains a likely credential assignment.",
                )
            )

    return issues
