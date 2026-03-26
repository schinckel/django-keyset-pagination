from pathlib import Path

from keyset_pagination.mixin import PaginateMixin


def test_paginate_mixin_imports_on_modern_django():
    assert PaginateMixin is not None


def test_pyproject_declares_tested_django_range():
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    contents = pyproject.read_text(encoding="utf-8")
    assert 'dependencies = ["Django>=4.2,<6.1"]' in contents
