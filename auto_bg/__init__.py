"""Rewrite a busy chief-of-staff Signal DM to /bg. Read-only. Never raises."""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

log = logging.getLogger("auto_bg")

_SEEN: list[str] = []
_HITS: list[float] = []
_ALLOW = {"mtime": None, "ids": frozenset()}
_LOADED = False


def reset_state() -> None:
    """Test helper. Not used by the gateway."""
    _SEEN.clear()
    _HITS.clear()
    _ALLOW["mtime"] = None
    _ALLOW["ids"] = frozenset()


def _root() -> Path:
    return Path(os.environ.get("AUTO_BG_HOME", "/home/debian/hermes"))


def _allow_ids() -> frozenset:
    path = _root() / "state" / "auto-bg" / "allow.json"
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return frozenset()
    if _ALLOW["mtime"] == mtime:
        return _ALLOW["ids"]
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        ids = frozenset(str(x) for x in raw) if isinstance(raw, list) else frozenset()
    except (OSError, ValueError, TypeError):
        ids = frozenset()
    _ALLOW["mtime"] = mtime
    _ALLOW["ids"] = ids
    return ids


def _killed() -> bool:
    return (_root() / "state" / "auto-bg" / "DISABLED").exists()


def _platform(source) -> str:
    plat = getattr(source, "platform", None)
    return str(getattr(plat, "value", plat) or "").lower()


def _pending(gateway, key: str) -> bool:
    """True means do not rewrite. A probe that fails is treated as pending."""
    probes = []
    try:
        from tools.approval import has_blocking_approval
        probes.append(lambda: has_blocking_approval(key))
    except Exception:
        log.debug("auto-bg probe import failed")
        return True
    try:
        from tools.slash_confirm import get_pending as slash_pending
        probes.append(lambda: slash_pending(key) is not None)
    except Exception:
        log.debug("auto-bg probe import failed")
        return True
    try:
        from tools.clarify_gateway import get_pending_for_session
        probes.append(lambda: get_pending_for_session(key, include_choice_prompts=True) is not None)
    except Exception:
        log.debug("auto-bg probe import failed")
        return True
    probes.append(_update_pending(gateway, key))
    for probe in probes:
        try:
            if probe():
                return True
        except Exception:
            log.debug("auto-bg probe failed")
            return True
    return False


def _update_pending(gateway, key: str):
    def _check() -> bool:
        state = gateway._peek_session_state(key)
        return bool(state.persistent.update_prompt_pending)
    return _check


def _remember(message_id: str) -> None:
    if message_id in _SEEN:
        return
    _SEEN.append(message_id)
    del _SEEN[:-512]


def _rate_ok() -> bool:
    now = time.monotonic()
    fresh = [t for t in _HITS if now - t < 60]
    _HITS[:] = fresh
    if len(fresh) >= 4:
        return False
    _HITS.append(now)
    return True


def pre_gateway_dispatch(event=None, gateway=None, session_store=None, **kwargs):
    try:
        return _decide(event, gateway)
    except Exception:
        log.debug("auto-bg callback failed")
        return None


def _decide(event, gateway):
    if _killed():
        return None
    source = getattr(event, "source", None)
    if source is None or gateway is None:
        return None
    if _platform(source) != "signal":
        return None
    if getattr(source, "chat_type", None) != "dm":
        return None
    if getattr(source, "profile", None) != "chief-of-staff":
        return None
    text = getattr(event, "text", None)
    if not isinstance(text, str) or not text.strip():
        return None
    stripped = text.strip()
    if stripped.startswith("/"):
        return None
    kind = getattr(getattr(event, "message_type", None), "value", None)
    if kind not in (None, "text"):
        return None
    if getattr(event, "media_urls", None):
        return None
    ids = _allow_ids()
    if not ids:
        return None
    if getattr(source, "user_id", None) not in ids and getattr(source, "chat_id", None) not in ids:
        return None
    message_id = getattr(event, "message_id", None)
    if message_id and message_id in _SEEN:
        return None
    try:
        key = gateway._session_key_for_source(source)
        if not gateway._is_session_running(key):
            return None
    except Exception:
        log.debug("auto-bg busy probe failed")
        return None
    if _pending(gateway, key):
        return None
    if not _rate_ok():
        return None
    if message_id:
        _remember(str(message_id))
    log.info("auto-bg rewrite chat=<redacted>")
    return {"action": "rewrite", "text": "/bg " + stripped}


def register(ctx) -> None:
    global _LOADED
    ctx.register_hook("pre_gateway_dispatch", pre_gateway_dispatch)
    if not _LOADED:
        _LOADED = True
        log.info("auto-bg loaded")
