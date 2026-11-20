# ENABLE RUNBOOK — auto-bg — t2072u

ENABLE ONLY WHEN NO HERMES JOB RUNS (CEO t2072u).

The plugin rewrites a plain Signal DM to `/bg <text>` while chief-of-staff is busy. `/bg` does not see earlier chat, only that text. The running turn does not see the rewrite. The background session still belongs to chief-of-staff and answers in the same chat.

Install on the chief-of-staff profile only. Source trace: the Signal adapter's message handler enters `_async_profile_runtime_scope` before `_handle_message`, and the plugin manager is keyed by that home. The offline test `test_manager_follows_home_override` checks the manager switch.

## Copy

```bash
sudo -u debian mkdir -p /home/debian/hermes/profiles/chief-of-staff/plugins/auto-bg
cp -a /home/debian/auto-bg-t2072u/auto_bg/plugin.yaml /home/debian/auto-bg-t2072u/auto_bg/__init__.py \
  /home/debian/hermes/profiles/chief-of-staff/plugins/auto-bg/
cp -a /home/debian/hermes/profiles/chief-of-staff/config.yaml \
  /home/debian/hermes/profiles/chief-of-staff/config.yaml.bak-t2072u
```

Add `auto-bg` to `plugins.enabled` in that config (today the list is `[hindsight]`). Do not edit the launch-home config.

## Allowlist

Read the CEO DM id from the profile Signal home channel and write it as a one-element JSON list. Do not print it.

```bash
python3 - << 'PY'
import json
from pathlib import Path
import yaml
cfg = yaml.safe_load(Path("/home/debian/hermes/profiles/chief-of-staff/config.yaml").read_text())
chat = cfg["platforms"]["signal"]["home_channel"]["chat_id"]
dest = Path("/home/debian/hermes/state/auto-bg")
dest.mkdir(parents=True, exist_ok=True)
(dest / "allow.json").write_text(json.dumps([chat]) + "\n")
print("allow.json written", dest / "allow.json", "entries", 1)
PY
```

Do not create ENABLE. Loading the plugin is on. Fast off with no restart: `touch /home/debian/hermes/state/auto-bg/DISABLED`.

## Restart

One restart. Do not restart signal-cli.

`systemctl --user restart hermes-gateway-7e5c0db0.service`

Plugins load at process start (`PluginManager.discover_and_load`). DISABLED is read on each message and does not need a restart.

## Verify

`systemctl --user is-active hermes-gateway-7e5c0db0.service` is active. `ActiveEnterTimestamp` and `MainPID` differ from before the restart. `journalctl --user -u hermes-gateway-7e5c0db0.service -n 200` contains `auto-bg loaded`. Signal still connects (the unit log shows the Signal adapter connected for chief-of-staff).

## CEO test

While a chief-of-staff turn is in flight, send one harmless plain sentence in the CEO DM. Expect a background-session ack and one answer in that same chat. A slash command, a media message, or a message while idle stays on the normal path.

## Rollback

```bash
rm -rf /home/debian/hermes/profiles/chief-of-staff/plugins/auto-bg
cp -a /home/debian/hermes/profiles/chief-of-staff/config.yaml.bak-t2072u \
  /home/debian/hermes/profiles/chief-of-staff/config.yaml
systemctl --user restart hermes-gateway-7e5c0db0.service
```

Or, without a restart, `touch /home/debian/hermes/state/auto-bg/DISABLED`.
