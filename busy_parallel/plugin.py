"""Plugin entry. Not installed. Dry-run returns None so the chief keeps the message."""

from __future__ import annotations

import os
from pathlib import Path

from busy_parallel.runner import handle


def on_post_gateway_admission(**kwargs):
    home = Path(os.environ.get("HERMES_HOME", "/tmp/busy-parallel-unset"))
    event = {
        "platform": kwargs.get("platform") or "",
        "message_id": kwargs.get("message_id") or "",
        "text": kwargs.get("text") or "",
        "message_type": kwargs.get("message_type") or "text",
        "media": kwargs.get("media"),
        "busy": bool(kwargs.get("busy") or kwargs.get("session_busy")),
        "session_busy": bool(kwargs.get("session_busy") or kwargs.get("busy")),
        "internal": bool(kwargs.get("internal")),
        "worker": bool(kwargs.get("worker")),
        "source": kwargs.get("source") if isinstance(kwargs.get("source"), dict) else {},
    }
    result = handle(event, home)
    if result.get("handled"):
        return {"action": "handled"}
    return None


def register(ctx) -> None:
    ctx.register_hook("post_gateway_admission", on_post_gateway_admission)
