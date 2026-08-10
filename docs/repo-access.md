# Who can change agent-harness (public repo)

## Goal

- **Public** read / fork / open PRs is fine.
- **Only the owner (`0xbadhash`)** decides what lands on `main`.
- Automation (Grok/agents on the VPS) must **not** be able to silently ship to `main`.

## What is already true

| Control | Effect |
|--------|--------|
| No collaborators | Nobody else has write access (only the owner account). |
| Branch protection on `main` | Direct pushes blocked; **PR required**. |
| Require 1 approving review + Code Owners | Merge needs a formal approval from `@0xbadhash` (CODEOWNERS). |
| Enforce for admins | Even admin tokens cannot skip PR rules on classic protection. |
| Ruleset `main-owner-only-merge` | No force-push / no delete `main`; PR + code-owner review + last-push approval. |
| No force-push / no delete branch | History safety. |

## Critical: same identity = agents *are* “you”

If the VPS uses a **Personal Access Token for `0xbadhash`**, every agent commit is legally *your* GitHub user. Branch protection still forces a **PR**, but:

1. GitHub **does not allow the PR author to approve their own PR**.
2. If that token is also **admin** and something grants a **bypass**, the agent can still merge.

So protection alone is not enough. You need **credential separation**.

## Recommended setup (do this)

### 1. Owner machine only for merge

- **You** review PRs in the GitHub UI and click **Approve** + **Merge**.
- Do not store your primary password or classic “all-repo” PAT on the VPS.

### 2. Automation bot account (recommended)

Create a second GitHub user, e.g. `0xbadhash-bot` (or a machine user):

1. Invite it as a **collaborator with Write** (not Admin) on `agent-harness` **or** only grant a fine-grained PAT scoped to open PRs.
2. On the VPS, set `GH_TOKEN` / `GITHUB_TOKEN` for agents to the **bot** token only.
3. Bot workflow: push branch → open PR → stop. **You** approve.

Fine-grained PAT (owner account, safer alternative if no second user):

- Resource owner: `0xbadhash`
- Repository access: **only** `agent-harness` (or none for harness if agents must not touch it)
- Permissions: **Contents: Read** + **Pull requests: Write** (can open PR from a fork workflow)  
  — avoid **Contents: Write** on `main` if you can work with fork PRs; for same-repo branches you need Contents: Write, but rules still block merge without your approval.

### 3. Never put Admin tokens on agents

- VPS tokens: **Write** max, no Admin, no `delete_repo`, no org owner.
- Prefer fine-grained, short-lived, single-repo.

### 4. Optional: stop agents from touching harness at all

If harness releases are always manual from your laptop:

```bash
# on VPS: remove push URL for agent-harness only
cd ~/agent-harness
git remote set-url --push origin no_push
# or use a read-only deploy key
```

Products can still `install_into_product.sh` from the local clone without pushing the SoT.

### 5. GitHub UI checklist

Repo → **Settings** → **Rules** / **Branches**:

- [x] Ruleset on `main` (active)
- [x] Classic branch protection (PR + code owners + enforce admins)
- [ ] Collaborators: only you (and optional bot Write)
- [ ] Actions: limit who can approve workflow runs if needed
- [x] Secret scanning + push protection (already on)

## How *you* land a change after this

```bash
git checkout -b feat/my-change
# ... commit ...
git push -u origin HEAD
gh pr create --fill
# open GitHub → Review → Approve (cannot self-approve if author is you)
# If self-approve is blocked: use bot as PR author, or temporarily use a second account review
gh pr merge --squash
```

Solo-owner note: if **you** open the PR as `0xbadhash`, GitHub will not let you approve yourself. Prefer **bot opens PR → you approve**, or add a trusted second account solely for the second review.

## Personal vs org repos

User-owned repos **cannot** set “restrict who can push” to a user list (org-only). Protection is: **no direct push to main** (PR required) + **reviews** + **no extra collaborators**.

## Related

- `.github/CODEOWNERS` — `* @0xbadhash`
- `docs/protect-list-merge.md` — product-side script forks (unrelated to GitHub access)
