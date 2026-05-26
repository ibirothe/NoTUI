from __future__ import annotations

import pytest

from notui.exceptions import ValidationError
from notui.services import validate_category, validate_content, validate_title


def test_validate_title_trims_and_rejects_empty() -> None:
    assert validate_title("  hello  ") == "hello"
    with pytest.raises(ValidationError):
        validate_title("   ")


def test_validate_title_rejects_newline_and_too_long() -> None:
    with pytest.raises(ValidationError):
        validate_title("hello\nworld")
    with pytest.raises(ValidationError):
        validate_title("x" * 201)


def test_validate_content_limit() -> None:
    assert validate_content("") == ""
    with pytest.raises(ValidationError):
        validate_content("x" * 100_001)


def test_validate_category_trims_and_allows_empty() -> None:
    assert validate_category("  work  ") == "work"
    assert validate_category("   ") is None
    assert validate_category(None) is None


def test_validate_category_rejects_newline_and_too_long() -> None:
    with pytest.raises(ValidationError):
        validate_category("work\nhome")
    with pytest.raises(ValidationError):
        validate_category("x" * 81)
