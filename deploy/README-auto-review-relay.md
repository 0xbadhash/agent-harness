# Auto-review relay — install and rollback

Source of truth for the box copies. Install only under a CEO stamp; the
default state is "built, not installed".

## Files

| Here | On the box |
|------|------------|
| `deploy/auto-review-relay.py` | `/opt/catalyxt/ops/auto-review-relay.py` |
| `deploy/hooks/grok-auto-review-relay.sh` | `~/.grok/hooks/auto-review-relay.sh` |
| `deploy/hooks/grok-notification.json` | `~/.grok/hooks/auto-review-relay.json` |
| `deploy/auto-review-relay-watch.service` | `~/.config/systemd/user/` |
| `deploy/auto-review-relay-digest.service` | `~/.config/systemd/user/` |
| `deploy/auto-review-relay-digest.timer` | `~/.config/systemd/user/` |

## Install

```sh
install -m 0755 deploy/auto-review-relay.py /opt/catalyxt/ops/auto-review-relay.py
install -d ~/.grok/hooks
install -m 0755 deploy/hooks/grok-auto-review-relay.sh ~/.grok/hooks/auto-review-relay.sh
install -m 0644 deploy/hooks/grok-notification.json ~/.grok/hooks/auto-review-relay.json
install -m 0644 deploy/auto-review-relay-watch.service \
  deploy/auto-review-relay-digest.service deploy/auto-review-relay-digest.timer \
  ~/.config/systemd/user/
install -d /var/lib/pilot/auto-review-relay
systemctl --user daemon-reload
systemctl --user enable --now auto-review-relay-watch.service
systemctl --user enable --now auto-review-relay-digest.timer
```

The Grok hook applies to new sessions only; an already-running session picks it
up when it restarts.

## Prove it without sending

```sh
AUTO_REVIEW_STATE=/tmp/arr python3 /opt/catalyxt/ops/auto-review-relay.py \
  --hook --harness grok --dry < tests/fixtures/auto_review/grok_permission_prompt.json
```

## Rollback

- Instant stop, no restart: `touch /var/lib/pilot/auto-review-relay/DISABLED`.
- Full stop: `systemctl --user disable --now auto-review-relay-watch.service auto-review-relay-digest.timer`,
  then remove `~/.grok/hooks/auto-review-relay.json`.
- The relay never types into a pane; removing the units leaves tmux untouched.
