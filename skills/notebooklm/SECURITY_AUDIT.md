# notebooklm-py Security Audit

**Audit version:** `v0.3.4-hermes.3` (Python package version stays `0.3.4`)
**Audit date:** 2026-04-23 (original scan at `v0.3.4-hermes.2`; `hermes.3` is a docs-only follow-up on top of `hermes.2` with `src/` unchanged — audit findings carry forward verbatim)
**Prior audits:**
- `v0.3.4-hermes.2` (2026-04-23) — re-scan after merging upstream post-v0.3.4 delta + cherry-picking PR #298, #279. LOW RISK.
- `v0.3.4-hermes.1` (2026-04-23 earlier) — initial scan. LOW RISK, `src/` byte-identical to upstream tag `v0.3.4`.
**Auditor:** Claude (manual static scan)
**Verdict:** LOW RISK — audit maintained after ~2.4k lines of upstream bug-fix and feature delta were pulled in

---

## Scope

This revision includes:

1. **Fork-inherited upstream commits past tag v0.3.4** (~20 commits up to `d6cef80`) — decoder correctness fixes (#295/#296), YouTube URL extraction fixes (#292), Google account switching fix (#248), storage save error handling (#240), mind-map language/instructions (#252), multi-profile support (profile.py, migration.py), `doctor` diagnostic CLI, agent-install helpers, etc.
2. **Cherry-picked PR #298** — `NOTEBOOKLM_REFRESH_CMD` opt-in auto-refresh of auth cookies on expiry. The exact feature that solves this fork's 15-30min browser-import staleness problem.
3. **Cherry-picked PR #279** — `sys.executable -m playwright` instead of bare `playwright` in subprocess, so CLI works when installed in a venv without global `playwright` on PATH (which is how this fork is installed into Hermes).

`src/` is no longer byte-identical to upstream `v0.3.4`. It is byte-identical to upstream `main` as of `d6cef80` (2026-04-21) *plus* PR #298 + PR #279 applied.

Diff statistics vs upstream `v0.3.4` tag: **21 files changed, +2389/-847 lines** in `src/`.

## Clean findings (re-verified)

| Check | Result |
|---|---|
| eval / exec / pickle / compile / __import__ | none in delta |
| Shell injection | subprocess only in two places: `_ensure_chromium_installed()` with hardcoded `["playwright","install","chromium"]` args, and `fetch_tokens()` running the user-controlled `$NOTEBOOKLM_REFRESH_CMD`. Neither accepts external data into argv. |
| Outbound hosts | unchanged: `*.google.com`, `youtube.com`. Only new URL in strings is `https://www.microsoft.com/edge` as help text (not a request). |
| Telemetry / analytics / beacons | none |
| Env var reads | all namespaced to `NOTEBOOKLM_*` (new ones: `NOTEBOOKLM_REFRESH_CMD`, internal `NOTEBOOKLM_REFRESH_ATTEMPTED`) |
| Credential file writes | `auth.py` still does not write `storage_state.json` itself; Playwright owns that path. New `migration.py` moves `storage_state.json` between profile-scoped locations under `$NOTEBOOKLM_HOME`. `convert_rookiepy_cookies_to_storage_state()` in `auth.py` is pure conversion, no I/O. |

## New attack surface introduced by the delta

### `NOTEBOOKLM_REFRESH_CMD` (PR #298) — controlled subprocess invocation
- Runs whatever shell command the user sets in this env var when auth expires.
- **By design, this is user-opted-in.** An unset env var keeps behavior identical to v0.3.4.
- Guardrails in the PR: one-shot per process (`NOTEBOOKLM_REFRESH_ATTEMPTED` sentinel prevents infinite refresh loops); non-zero exit → `RuntimeError` with captured stderr; timeout → same.
- **Risk**: anyone with write access to your shell env can set this to run arbitrary commands. But that attacker already has shell access, so it's not a meaningful escalation. The library doesn't read the value from untrusted sources.

### `--browser-cookies` (upstream feature) — rookiepy-backed cookie extraction
- Reads cookies from the user's installed browser (Chrome/Firefox/Brave/Edge/Safari/Arc) via `rookiepy` (optional extra, `notebooklm-py[cookies]`).
- On macOS, `rookiepy` requires Keychain access to decrypt Chrome cookies. This prompts the user once.
- The extracted cookies go to `storage_state.json` in the same path `notebooklm login` would write. Same sensitivity level.
- **Risk**: if the user's browser is compromised, the cookies they contain are compromised already. `--browser-cookies` doesn't make this worse.

### `profile.py` + `migration.py` — multi-profile layout
- Moves `storage_state.json` under `$NOTEBOOKLM_HOME/profiles/<name>/`.
- Migration is opt-in and idempotent (writes a marker file).
- **Risk**: `migration.py:119` writes a marker; `migration.py:139` writes a profile config. Both go to expected paths under HOME.

### `doctor.py` — read-only diagnostic
- Scans `$NOTEBOOKLM_HOME` for legacy files and prints findings. No network, no subprocess, no writes.

## Audit-pinning discipline (unchanged)

- PyPI 0.3.4 wheel remains unsigned (no Trusted Publishing). We continue to install from the fork's git tag rather than PyPI.
- Fork invariant: `main` always equals the latest audited tag. Before installing, users should verify via the GitHub compare view.
- Upgrade protocol: same as before, see end of this document.

## Hardening applied

- All previous hardening preserved (chmod 600 on `storage_state.json`, isolated Hermes venv, symlinked CLI, no auto-upgrade wired up).
- New: after this audit, users can opt into `NOTEBOOKLM_REFRESH_CMD="notebooklm login --browser-cookies chrome"` to make the Hermes CLI self-heal when Google rotates cookies, without manual intervention.

## Hardening still recommended (NOT YET APPLIED)

- Use a burner Google account for auth, not the primary account.
- Pin to exact tag: the install commands in README reference `v0.3.4-hermes.3`.
- `chmod 600 ~/.notebooklm/storage_state.json` after any re-login (Playwright may restore 644 defaults).
- Before any upgrade, diff versions: see "Upgrade protocol" below.

## Upgrade protocol (MANDATORY)

Every version bump requires a manual review gate. Do not run `hermes skills update notebooklm --force` or `uv pip install -U notebooklm-py` blindly.

```bash
# 1. Fetch upstream and see what's new in src/
cd ~/Desktop/notebooklm-py
git fetch upstream
git log --oneline HEAD..upstream/main -- src/

# 2. Diff the Python source
git diff HEAD..upstream/main -- src/

# 3. Re-run the scan patterns on the new version before installing:
#    - eval/exec/pickle/compile/__import__
#    - subprocess / os.system / shell=True (confirm only user-opted-in)
#    - outbound hosts (grep -rhoE "https?://[a-zA-Z0-9.-]+")
#    - new env vars read outside NOTEBOOKLM_* namespace
#    - new file writes outside $NOTEBOOKLM_HOME and ~/.notebooklm/
#
# 4. If clean, merge, re-tag as v0.3.4-hermes.N+1 (or v0.X.Y-hermes.1 if
#    upstream tagged a new minor version), and update this doc.
# 5. If suspicious, freeze upgrade and investigate.
```
