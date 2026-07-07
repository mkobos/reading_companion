"""Shared HTTP error helpers.

All bodies use the spec/contracts/api.openapi.yaml `Error` shape
({"message": str}) via the custom exception handler registered in
app.main. 404s are identical for "doesn't exist" and "malformed ID" so
responses reveal nothing that would let a client distinguish the two
(spec/features/security.feature, "Workspaces are unreachable without their
URL").
"""

from fastapi import HTTPException


def not_found_error() -> HTTPException:
    return HTTPException(status_code=404, detail="Not found")


def bad_request_error(message: str) -> HTTPException:
    return HTTPException(status_code=400, detail=message)


def conflict_error(message: str) -> HTTPException:
    return HTTPException(status_code=409, detail=message)


def rate_limited_error(retry_after_seconds: int) -> HTTPException:
    return HTTPException(
        status_code=429,
        detail="Rate limit exceeded",
        headers={"Retry-After": str(retry_after_seconds)},
    )


def agent_failure_error() -> HTTPException:
    """502 per api.openapi.yaml's AgentFailure response: nothing is
    persisted and the request can be retried."""
    return HTTPException(status_code=502, detail="Agent turn failed; nothing was saved. Retry.")
