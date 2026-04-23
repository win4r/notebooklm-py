# notebooklm-py Security Audit

**Audited version:** `notebooklm-py==0.3.4`
**Audit date:** 2026-04-23
**Auditor:** Claude (manual static scan)
**Verdict:** LOW RISK — usable for research/prototype, not for main Google account

---

## Scope

42 Python files, ~17K LOC in the installed PyPI wheel, plus the SKILL.md in this directory. Upstream: https://github.com/teng-lin/notebooklm-py (tag v0.3.4 byte-identical to PyPI wheel — verified by `diff` against `git show v0.3.4:src/notebooklm/__init__.py`).

## Clean findings

| Check | Result |
|---|---|
| eval / exec / pickle / compile / __import__ | none |
| Shell injection (subprocess with user input) | none — only `["playwright","install","chromium"]` hardcoded |
| Outbound hosts | `*.google.com`, `youtube.com` only (expected for a NotebookLM client) |
| Telemetry / analytics / beacons | none |
| Env var reads | namespaced to `NOTEBOOKLM_*`; does not sniff generic secrets |
| Credential file writes | Python code never writes `storage_state.json`; Playwright manages it (standard pattern) |
| `_version_check.py` | 20 lines, pure `sys.version_info` check, no network |

## Watch items (not blockers)

1. **No PyPI attestation.** Wheels 0.3.4 uploaded 2026-03-12 without Trusted Publishing / GitHub Actions build attestation. A future version could be published by someone who compromises teng-lin's PyPI account without cryptographic detection.

2. **Undocumented Google APIs.** Self-acknowledged in README. Availability risk (Google can break it) and account-flagging risk (Google abuse detection may mark the session).

3. **`storage_state.json` holds Google SID cookie.** This cookie grants account-wide access to all cookie-authenticated Google services (Gmail, Drive, YouTube, etc.). Any code with filesystem read, including Hermes agent's shell tool, can exfiltrate it.

4. **Hermes skills-guard flagged SKILL.md as CAUTION** (community + 3 × `pip install` supply-chain patterns). Install required `--force`. Decision is recorded in `~/.hermes/.hub/` audit log.

## Hardening applied

- Installed into isolated Hermes venv (`~/.hermes/hermes-agent/venv`) — not system Python.
- CLI reachable via symlink `~/.local/bin/notebooklm` (same pattern as `hermes` itself).
- No auto-upgrade wired up.

## Hardening recommended (NOT YET APPLIED)

- Use a burner Google account for `notebooklm login`, not the primary account.
- Pin to exact version: `uv pip install 'notebooklm-py==0.3.4'` in all install docs.
- Verify `chmod 600 ~/.notebooklm/storage_state.json` is in effect.
- Before any upgrade, diff versions: see "Upgrade protocol" below.

## Upgrade protocol (MANDATORY)

Every version bump requires a manual review gate. Do not run `hermes skills update notebooklm --force` or `uv pip install -U notebooklm-py` blindly.

```bash
# 1. Fetch upstream tag diff
cd ~/Desktop/notebooklm-py
git fetch upstream
git log --oneline v0.3.4..upstream/main  # see what's changed

# 2. Diff the Python source
git diff v0.3.4..upstream/main -- src/notebooklm/

# 3. Re-run the scan patterns on the new version before installing:
#    - eval/exec/pickle/compile/__import__
#    - subprocess / os.system / shell=True
#    - outbound hosts (grep -rhoE "https?://[a-zA-Z0-9.-]+")
#    - new env vars read outside NOTEBOOKLM_* namespace
#    - new file writes in auth.py
#
# 4. If clean, pin the new version and update this doc.
# 5. If suspicious, freeze upgrade and investigate.
```

## Contact

If this skill stops working because Google changed an API: that's expected, not a security issue. If you see unexpected network calls, credential access outside `~/.notebooklm/`, or subprocess calls with user input: that's a security issue — investigate before upgrading further.
