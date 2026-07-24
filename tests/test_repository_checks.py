from pathlib import Path

from zebrafish_tracking.repository_checks import scan_repository


def test_clean_repository_candidate_passes(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "module.py").write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text(
        "# Clean repository\n",
        encoding="utf-8",
    )

    assert scan_repository(tmp_path) == []


def test_repository_check_detects_cache_local_path_and_data(tmp_path: Path):
    cache = tmp_path / "__pycache__"
    cache.mkdir()
    (cache / "module.pyc").write_bytes(b"compiled")

    data = tmp_path / "data"
    data.mkdir()
    (data / "movie.tif").write_bytes(b"image")

    # Assemble the regression fixture at runtime so the repository scanner
    # tests the forbidden path without finding that literal in this source.
    local_path = "/data/" + "aun/private/run"
    (tmp_path / "script.py").write_text(
        f'PATH = "{local_path}"\n',
        encoding="utf-8",
    )

    issues = scan_repository(tmp_path)
    categories = {issue.category for issue in issues}

    assert "forbidden-directory" in categories
    assert "generated-root-directory" in categories
    assert "forbidden-binary-or-archive" in categories
    assert "local-absolute-path" in categories


def test_repository_check_detects_generated_egg_info(tmp_path: Path):
    metadata = tmp_path / "src" / "example_package.egg-info"
    metadata.mkdir(parents=True)
    (metadata / "PKG-INFO").write_text(
        "Name: example-package\n",
        encoding="utf-8",
    )

    issues = scan_repository(tmp_path)

    assert any(
        issue.category == "generated-package-metadata"
        and issue.path == "src/example_package.egg-info"
        for issue in issues
    )


def test_checker_source_does_not_self_match_private_key_markers():
    import zebrafish_tracking.repository_checks as checks

    source = Path(checks.__file__).read_text(encoding="utf-8")
    assert not any(
        marker in source
        for marker in checks.PRIVATE_KEY_MARKERS
    )
