"""HTTP 编排 module 单元测（信封断言，不依赖 MySQL）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from tests.http_scenarios import data_err, data_ok, envelope


@dataclass
class _FakeResponse:
    status_code: int
    body: dict[str, Any]
    text: str = ""

    def json(self) -> dict[str, Any]:
        return self.body


def test_envelope_requires_all_fields() -> None:
    with pytest.raises(AssertionError, match="traceId"):
        envelope(_FakeResponse(200, {"code": 0, "message": "ok", "data": {}}))


def test_data_ok_accepts_success_envelope() -> None:
    data = data_ok(
        _FakeResponse(
            200,
            {"code": 0, "message": "ok", "data": {"id": 1}, "traceId": "abc"},
        )
    )
    assert data == {"id": 1}


def test_data_err_accepts_failure_envelope() -> None:
    body = data_err(
        _FakeResponse(
            409,
            {"code": 40900, "message": "冲突", "data": None, "traceId": "xyz"},
        ),
        status=409,
        code=40900,
    )
    assert body["message"] == "冲突"
