from __future__ import annotations

from typing import Any


def ok(data: Any = None, message: str = "OK") -> dict[str, Any]:
    return {"success": True, "message": message, "data": data}


def err(
    message: str,
    error_code: str,
    errors: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "success": False,
        "message": message,
        "errorCode": error_code,
        "errors": errors or [],
    }
