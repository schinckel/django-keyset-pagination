from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]

from packaging.requirements import Requirement

from keyset_pagination.mixin import PaginateMixin


def test_paginate_mixin_imports_on_modern_django():
    assert PaginateMixin is not None


def test_pyproject_declares_tested_django_range():
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    with pyproject.open("rb") as f:
        data = tomllib.load(f)
    deps = data["project"]["dependencies"]
    all_reqs = [Requirement(dep) for dep in deps]
    django_reqs = [req for req in all_reqs if req.name.lower() == "django"]
    assert django_reqs, "No Django dependency found in project.dependencies"
    specifiers = {(s.operator, s.version) for s in django_reqs[0].specifier}
    assert (">=", "4.2") in specifiers, f"Django lower bound >=4.2 not found in {specifiers}"
    assert ("<", "6.1") in specifiers, f"Django upper bound <6.1 not found in {specifiers}"
