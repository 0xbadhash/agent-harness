"""Pure decision. Never launches, never logs sender ids."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

from busy_parallel import MARKER
from busy_parallel import state as st


@dataclass
class Decision:
    launch: bool
    reason: str
    job_id: str = ""


def _job_id(message_id: str) -> str:
    digest = hashlib.sha256(message_id.encode("utf-8")).hexdigest()[:8]
    return f"busy-par-{digest}"


def decide(event: dict, cfg: dict, home) -> Decision:
    if os.environ.get("BUSY_PARALLEL_WORKER") == "1":
        return Decision(False, "loop-guard-process")
    if not st.enabled(home):
        return Decision(False, "switch-off")
    if event.get("internal") or event.get("worker"):
        return Decision(False, "loop-guard")
    text = event.get("text") if isinstance(event.get("text"), str) else ""
    if MARKER in text or "busy-par-" in text:
        return Decision(False, "loop-guard")
    if not (event.get("busy") or event.get("session_busy")):
        return Decision(False, "not-busy")
    kind = (event.get("message_type") or "text").lower()
    if kind != "text" or event.get("media"):
        return Decision(False, "non-text")
    if not text.strip():
        return Decision(False, "non-text")
    source = event.get("source") if isinstance(event.get("source"), dict) else {}
    if (source.get("chat_type") or "dm") != "dm":
        return Decision(False, "not-dm")
    if (event.get("platform") or "").lower() != "signal":
        return Decision(False, "not-signal")
    senders = set(cfg.get("allow_senders") or [])
    chats = set(cfg.get("allow_chats") or [])
    if source.get("user_id") not in senders and source.get("chat_id") not in chats:
        return Decision(False, "allowlist-reject")
    message_id = str(event.get("message_id") or "")
    if not message_id:
        return Decision(False, "no-message-id")
    if st.seen(home, message_id):
        return Decision(False, "dedupe")
    cap = int(cfg.get("concurrency_cap") or 2)
    if len(st.inflight(home)) >= cap:
        return Decision(False, "concurrency-cap")
    rate = int(cfg.get("per_minute_cap") or 4)
    if st.recent_launches(home) >= rate:
        return Decision(False, "rate-cap")
    return Decision(True, "allowlist-accept", _job_id(message_id))
