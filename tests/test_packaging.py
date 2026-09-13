"""Reproducible packaging and CI security contracts."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ci_build_tool_is_security_patched():
    versions = {}
    for raw in (ROOT / "requirements-test.lock").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if "==" not in line or line.startswith("#"):
            continue
        name, version = line.split("==", 1)
        versions[name.casefold()] = version

    assert tuple(map(int, versions["setuptools"].split("."))) >= (83, 0, 0)
