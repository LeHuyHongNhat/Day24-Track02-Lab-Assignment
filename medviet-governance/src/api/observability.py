import json
import time
import uuid
from collections import Counter
from pathlib import Path
from threading import Lock
from typing import Optional, Tuple

from fastapi import Request

from src.access.rbac import MOCK_USERS

AUDIT_LOG_PATH = Path("reports/api_access.log")

_STATE_LOCK = Lock()
_REQUESTS_TOTAL = Counter()
_REQUESTS_BY_STATUS = Counter()
_REQUESTS_BY_ROUTE = Counter()
_UNAUTHORIZED_RAW_TOTAL = 0


def reset_observability_state() -> None:
    """Reset in-memory counters for tests."""
    global _UNAUTHORIZED_RAW_TOTAL
    with _STATE_LOCK:
        _REQUESTS_TOTAL.clear()
        _REQUESTS_BY_STATUS.clear()
        _REQUESTS_BY_ROUTE.clear()
        _UNAUTHORIZED_RAW_TOTAL = 0


def resolve_route_metadata(path: str, method: str) -> Tuple[Optional[str], Optional[str]]:
    """Map request path/method to logical resource/action labels."""
    normalized_path = path.rstrip("/") or "/"
    if normalized_path == "/api/patients/raw" and method == "GET":
        return "patient_data", "read"
    if normalized_path == "/api/patients/anonymized" and method == "GET":
        return "training_data", "read"
    if normalized_path == "/api/metrics/aggregated" and method == "GET":
        return "aggregated_metrics", "read"
    if normalized_path.startswith("/api/patients/") and method == "DELETE":
        return "patient_data", "delete"
    return None, None


def resolve_user_identity(authorization: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Resolve username/role from a bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        return None, None

    token = authorization.split(" ", 1)[1]
    user = MOCK_USERS.get(token)
    if not user:
        return None, None

    return user.get("username"), user.get("role")


def record_audit_event(
    *,
    request_id: str,
    method: str,
    path: str,
    user: Optional[str],
    role: Optional[str],
    resource: Optional[str],
    action: Optional[str],
    status_code: int,
    duration_ms: float,
) -> dict:
    """Append one structured audit event and update in-memory metrics."""
    event = {
        "request_id": request_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "method": method,
        "path": path,
        "user": user,
        "role": role,
        "resource": resource,
        "action": action,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
    }

    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _STATE_LOCK:
        with AUDIT_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

        route_key = f"{method} {path}"
        _REQUESTS_TOTAL[route_key] += 1
        _REQUESTS_BY_STATUS[str(status_code)] += 1
        _REQUESTS_BY_ROUTE[route_key] += 1

        global _UNAUTHORIZED_RAW_TOTAL
        if path == "/api/patients/raw" and status_code == 403:
            _UNAUTHORIZED_RAW_TOTAL += 1

    return event


def render_prometheus_metrics() -> str:
    """Render a small Prometheus exposition payload."""
    lines = [
        "# HELP medviet_http_requests_total Total HTTP requests handled.",
        "# TYPE medviet_http_requests_total counter",
    ]
    with _STATE_LOCK:
        for route_key, count in sorted(_REQUESTS_TOTAL.items()):
            method, path = route_key.split(" ", 1)
            lines.append(
                f'medviet_http_requests_total{{method="{method}",path="{path}"}} {count}'
            )

        lines.extend(
            [
                "# HELP medviet_http_responses_total HTTP responses by status code.",
                "# TYPE medviet_http_responses_total counter",
            ]
        )
        for status_code, count in sorted(_REQUESTS_BY_STATUS.items()):
            lines.append(
                f'medviet_http_responses_total{{status_code="{status_code}"}} {count}'
            )

        lines.extend(
            [
                "# HELP medviet_unauthorized_raw_access_total Unauthorized raw patient access attempts.",
                "# TYPE medviet_unauthorized_raw_access_total counter",
                f"medviet_unauthorized_raw_access_total {_UNAUTHORIZED_RAW_TOTAL}",
            ]
        )

    return "\n".join(lines) + "\n"


async def audit_middleware(request: Request, call_next):
    """FastAPI middleware that writes structured audit logs."""
    started = time.perf_counter()
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    user, role = resolve_user_identity(request.headers.get("authorization"))
    resource, action = resolve_route_metadata(request.url.path, request.method)

    status_code = 500
    response = None
    error = None

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception as exc:
        error = exc
        raise
    finally:
        duration_ms = (time.perf_counter() - started) * 1000.0
        if response is not None:
            status_code = response.status_code
        record_audit_event(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            user=user,
            role=role,
            resource=resource,
            action=action,
            status_code=status_code,
            duration_ms=duration_ms,
        )

        if error is not None:
            # Re-raise is handled by the except block above.
            pass


def install_observability(app) -> None:
    """Register audit middleware on the FastAPI app."""
    app.middleware("http")(audit_middleware)
