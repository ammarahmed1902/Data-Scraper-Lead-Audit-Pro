"""Tests for API error unwrapping."""

from app.core.db_errors import error_detail_from_exception, root_cause


def test_root_cause_unwraps_exception_group():
    inner = ValueError("real problem")
    group = ExceptionGroup("task group failed", [inner])
    assert root_cause(group) is inner


def test_error_detail_from_exception_group():
    inner = ValueError("schema mismatch")
    group = ExceptionGroup("unhandled errors in a TaskGroup", [inner])
    assert error_detail_from_exception(group) == "schema mismatch"
