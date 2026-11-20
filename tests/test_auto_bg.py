"""auto-bg rails. No live gateway, no real profile, no LLM."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import auto_bg  # noqa: E402


class Src:
    def __init__(self, **kw):
        self.platform = SimpleNamespace(value="signal")
        self.chat_type = "dm"
        self.profile = "chief-of-staff"
        self.user_id = "fake-user"
        self.chat_id = "fake-chat"
        for k, v in kw.items():
            setattr(self, k, v)


class Ev:
    def __init__(self, text="please file this", **kw):
        self.text = text
        self.message_id = kw.pop("message_id", "mid-1")
        self.message_type = SimpleNamespace(value=kw.pop("kind", "text"))
        self.media_urls = kw.pop("media_urls", [])
        self.source = kw.pop("source", Src())


class Gw:
    def __init__(self, busy=True, update=False, boom=None):
        self.busy = busy
        self.update = update
        self.boom = boom

    def _session_key_for_source(self, source):
        if self.boom == "key":
            raise RuntimeError("key")
        return "session-key"

    def _is_session_running(self, key):
        if self.boom == "busy":
            raise RuntimeError("busy")
        return self.busy

    def _peek_session_state(self, key):
        if self.boom == "update":
            raise RuntimeError("update")
        return SimpleNamespace(persistent=SimpleNamespace(update_prompt_pending=self.update))


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTO_BG_HOME", str(tmp_path))
    allow = tmp_path / "state" / "auto-bg"
    allow.mkdir(parents=True)
    (allow / "allow.json").write_text(json.dumps(["fake-user", "fake-chat"]), encoding="utf-8")
    auto_bg.reset_state()
    yield tmp_path
    auto_bg.reset_state()


def test_rewrite_when_busy(home):
    out = auto_bg.pre_gateway_dispatch(Ev(), Gw())
    assert out == {"action": "rewrite", "text": "/bg please file this"}


def test_idle(home):
    assert auto_bg.pre_gateway_dispatch(Ev(), Gw(busy=False)) is None


@pytest.mark.parametrize("text", ["/bg x", "/busy", "/approve", "/stop", "/deny", "/new"])
def test_slash_skipped(home, text):
    assert auto_bg.pre_gateway_dispatch(Ev(text), Gw()) is None


def test_pending_approval(home, monkeypatch):
    monkeypatch.setattr("tools.approval.has_blocking_approval", lambda key: True)
    assert auto_bg.pre_gateway_dispatch(Ev(), Gw()) is None


def test_pending_clarify(home, monkeypatch):
    monkeypatch.setattr("tools.approval.has_blocking_approval", lambda key: False)
    monkeypatch.setattr("tools.slash_confirm.get_pending", lambda key: None)
    monkeypatch.setattr(
        "tools.clarify_gateway.get_pending_for_session", lambda key, include_choice_prompts=True: object()
    )
    assert auto_bg.pre_gateway_dispatch(Ev(), Gw()) is None


def test_pending_slash_confirm(home, monkeypatch):
    monkeypatch.setattr("tools.approval.has_blocking_approval", lambda key: False)
    monkeypatch.setattr("tools.slash_confirm.get_pending", lambda key: {"ok": 1})
    assert auto_bg.pre_gateway_dispatch(Ev(), Gw()) is None


def test_update_prompt(home, monkeypatch):
    monkeypatch.setattr("tools.approval.has_blocking_approval", lambda key: False)
    monkeypatch.setattr("tools.slash_confirm.get_pending", lambda key: None)
    monkeypatch.setattr(
        "tools.clarify_gateway.get_pending_for_session", lambda key, include_choice_prompts=True: None
    )
    assert auto_bg.pre_gateway_dispatch(Ev(), Gw(update=True)) is None


def test_probe_raise(home, monkeypatch):
    def boom(key):
        raise RuntimeError("nope")
    monkeypatch.setattr("tools.approval.has_blocking_approval", boom)
    assert auto_bg.pre_gateway_dispatch(Ev(), Gw()) is None


def test_not_allowlisted(home):
    ev = Ev(source=Src(user_id="other", chat_id="other"))
    assert auto_bg.pre_gateway_dispatch(ev, Gw()) is None


def test_wrong_profile(home):
    assert auto_bg.pre_gateway_dispatch(Ev(source=Src(profile="ops-vps")), Gw()) is None


def test_group(home):
    assert auto_bg.pre_gateway_dispatch(Ev(source=Src(chat_type="group")), Gw()) is None


def test_attachment_and_empty(home):
    assert auto_bg.pre_gateway_dispatch(Ev(media_urls=["/tmp/a"]), Gw()) is None
    assert auto_bg.pre_gateway_dispatch(Ev(kind="voice"), Gw()) is None
    assert auto_bg.pre_gateway_dispatch(Ev("  "), Gw()) is None


def test_kill_switch(home):
    flag = home / "state" / "auto-bg" / "DISABLED"
    flag.write_text("off\n", encoding="utf-8")
    assert auto_bg.pre_gateway_dispatch(Ev(), Gw()) is None
    flag.unlink()
    assert auto_bg.pre_gateway_dispatch(Ev(message_id="after"), Gw())["action"] == "rewrite"


def test_missing_and_empty_allow(home):
    path = home / "state" / "auto-bg" / "allow.json"
    path.unlink()
    auto_bg.reset_state()
    assert auto_bg.pre_gateway_dispatch(Ev(), Gw()) is None
    path.write_text("[]", encoding="utf-8")
    auto_bg.reset_state()
    assert auto_bg.pre_gateway_dispatch(Ev(), Gw()) is None


def test_dedupe(home):
    assert auto_bg.pre_gateway_dispatch(Ev(), Gw())["action"] == "rewrite"
    assert auto_bg.pre_gateway_dispatch(Ev(), Gw()) is None


def test_rate_guard(home, monkeypatch):
    monkeypatch.setattr(auto_bg, "_SEEN", [])
    for i in range(4):
        assert auto_bg.pre_gateway_dispatch(Ev(message_id=f"r{i}"), Gw())["action"] == "rewrite"
    assert auto_bg.pre_gateway_dispatch(Ev(message_id="r4"), Gw()) is None


def test_loop_guard(home):
    assert auto_bg.pre_gateway_dispatch(Ev("/bg already"), Gw()) is None


def test_logs_redacted(home, caplog):
    caplog.set_level("INFO")
    auto_bg.pre_gateway_dispatch(Ev(text="secret phrase"), Gw())
    joined = caplog.text
    assert "secret phrase" not in joined
    assert "fake-user" not in joined
    assert "fake-chat" not in joined
    assert "auto-bg rewrite chat=<redacted>" in joined


def test_weird_event_never_raises(home):
    assert auto_bg.pre_gateway_dispatch(None, None) is None
    assert auto_bg.pre_gateway_dispatch(SimpleNamespace(), Gw()) is None


def test_manager_follows_home_override(tmp_path, monkeypatch):
    """Offline proof: ainvoke_hook uses the manager for the active home override."""
    from hermes_constants import reset_hermes_home_override, set_hermes_home_override
    from hermes_cli import plugins

    launch = tmp_path / "launch"
    routed = tmp_path / "chief"
    launch.mkdir()
    routed.mkdir()
    seen = []

    def cb_launch(**kwargs):
        seen.append("launch")
        return {"action": "allow"}

    def cb_routed(**kwargs):
        seen.append("routed")
        return {"action": "rewrite", "text": "/bg hi"}

    token = set_hermes_home_override(str(launch))
    try:
        mgr = plugins.get_plugin_manager()
        mgr._hooks.setdefault("pre_gateway_dispatch", []).append(cb_launch)
        mgr._discovered = True
    finally:
        reset_hermes_home_override(token)
    token = set_hermes_home_override(str(routed))
    try:
        mgr = plugins.get_plugin_manager()
        mgr._hooks.setdefault("pre_gateway_dispatch", []).append(cb_routed)
        mgr._discovered = True
        import asyncio
        result = asyncio.run(
            plugins.ainvoke_hook("pre_gateway_dispatch", event=None, gateway=None)
        )
        assert seen == ["routed"]
        assert result[0]["text"] == "/bg hi"
    finally:
        reset_hermes_home_override(token)


def test_real_dispatch_hook_rewrites(home):
    """Drive GatewayRunner._hm_pre_gateway_dispatch_hook in a fresh interpreter.

    Importing gateway.run inside this pytest process aborts it. A fresh
    interpreter imports it cleanly, which is how the real method is called.
    """
    import os
    import subprocess
    import sys
    script = home / "drive_dispatch.py"
    script.write_text(
        "import sys\n"
        "sys.path[:0] = [\n"
        "    '/home/debian/auto-bg-t2072u',\n"
        "    '/home/debian/hermes/hermes-agent',\n"
        "    '/home/debian/hermes/hermes-agent/venv/lib/python3.12/site-packages',\n"
        "]\n"
        "import asyncio, os\n"
        "from types import SimpleNamespace\n"
        "from hermes_constants import set_hermes_home_override\n"
        "from hermes_cli import plugins\n"
        "from gateway.platforms.event import MessageEvent, MessageType\n"
        "from gateway.run import GatewayRunner\n"
        "from gateway.session import SessionSource\n"
        "from gateway.config import Platform\n"
        "import auto_bg\n"
        "home = os.environ['AUTO_BG_HOME']\n"
        "set_hermes_home_override(home)\n"
        "manager = plugins.get_plugin_manager()\n"
        "manager._discovered = True\n"
        "class Ctx:\n"
        "    def register_hook(self, name, fn, **_kw):\n"
        "        manager._hooks.setdefault(name, []).append(fn)\n"
        "auto_bg.register(Ctx())\n"
        "import tools.approval, tools.slash_confirm, tools.clarify_gateway\n"
        "tools.approval.has_blocking_approval = lambda key: False\n"
        "tools.slash_confirm.get_pending = lambda key: None\n"
        "tools.clarify_gateway.get_pending_for_session = lambda key, include_choice_prompts=True: None\n"
        "runner = object.__new__(GatewayRunner)\n"
        "runner.session_store = None\n"
        "runner._session_key_for_source = lambda source: 'session-key'\n"
        "runner._is_session_running = lambda key: True\n"
        "runner._peek_session_state = lambda key: SimpleNamespace(persistent=SimpleNamespace(update_prompt_pending=False))\n"
        "source = SessionSource(platform=Platform.SIGNAL, chat_id='fake-chat', chat_type='dm', user_id='fake-user', profile='chief-of-staff')\n"
        "event = MessageEvent(text='hello there', message_type=MessageType.TEXT, message_id='integ-1', source=source)\n"
        "out = asyncio.run(runner._hm_pre_gateway_dispatch_hook(event, source))\n"
        "print(out.text)\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["AUTO_BG_HOME"] = str(home)
    env["PYTHONPATH"] = os.pathsep.join([
        str(ROOT),
        "/home/debian/hermes/hermes-agent",
        "/home/debian/hermes/hermes-agent/venv/lib/python3.12/site-packages",
        env.get("PYTHONPATH", ""),
    ])
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr[-800:]
    assert proc.stdout.strip().splitlines()[-1] == "/bg hello there"
