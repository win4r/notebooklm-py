#!/usr/bin/env python3
"""
Convert a browser cookie export (Cookie-Editor / Get cookies.txt LOCALLY JSON)
into the Playwright storage_state.json that notebooklm-py expects.

Usage:
    python3 import_browser_cookies.py <exported.json> [--out PATH] [--dry-run]

Default output: ~/.notebooklm/storage_state.json (chmod 600)

Why this exists: `notebooklm login` opens a fresh Playwright Chromium, which
Google's abuse detection can cooldown (48h typical). If you're already logged
in in your real browser, you can just reuse that session — no new-device flow.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Cookies for any of these domains are passed through
GOOGLE_DOMAINS = (
    "google.com",
    "notebooklm.google.com",
    "accounts.google.com",
    "myaccount.google.com",
    "googleusercontent.com",
    "youtube.com",
    "ytimg.com",
)

# At least one of these must be present — they're the session anchor
REQUIRED_ANCHORS = {"SID", "__Secure-1PSID", "__Secure-3PSID"}


def is_google_domain(domain: str) -> bool:
    domain = domain.lstrip(".")
    return any(domain == d or domain.endswith("." + d) for d in GOOGLE_DOMAINS)


def normalize_same_site(v) -> str:
    if not v:
        return "Lax"
    v = str(v).lower()
    if v in ("unspecified", "no_restriction", "none"):
        return "None"
    if v == "lax":
        return "Lax"
    if v == "strict":
        return "Strict"
    return "Lax"


def convert(cookies: list) -> list:
    out = []
    for c in cookies:
        domain = c.get("domain", "")
        if not domain or not is_google_domain(domain):
            continue

        cookie = {
            "name": c["name"],
            "value": c["value"],
            "domain": domain,
            "path": c.get("path", "/"),
            "httpOnly": bool(c.get("httpOnly", False)),
            "secure": bool(c.get("secure", False)),
            "sameSite": normalize_same_site(c.get("sameSite", "None")),
        }

        exp = c.get("expirationDate") or c.get("expires")
        if exp is not None and not c.get("session", False):
            cookie["expires"] = int(float(exp))
        else:
            cookie["expires"] = -1

        out.append(cookie)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="Exported cookies JSON (from Cookie-Editor / Get cookies.txt LOCALLY)")
    ap.add_argument("--out", default="~/.notebooklm/storage_state.json")
    ap.add_argument("--dry-run", action="store_true", help="Print result without writing")
    args = ap.parse_args()

    raw = json.loads(Path(args.input).expanduser().read_text())
    if isinstance(raw, dict) and "cookies" in raw:
        cookies = raw["cookies"]
    elif isinstance(raw, list):
        cookies = raw
    else:
        sys.exit("Unrecognized format. Expected JSON array or {cookies: [...]}")

    converted = convert(cookies)
    found_names = {c["name"] for c in converted}
    anchors_found = REQUIRED_ANCHORS & found_names

    if not anchors_found:
        sys.exit(
            f"No session-anchor cookies found (need one of {sorted(REQUIRED_ANCHORS)}).\n"
            f"Google cookies detected: {sorted(found_names) or 'NONE'}\n"
            f"Did you export cookies while logged into notebooklm.google.com?"
        )

    storage_state = {"cookies": converted, "origins": []}

    if args.dry_run:
        print(json.dumps(storage_state, indent=2))
        return

    out = Path(args.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(storage_state, indent=2))
    os.chmod(out, 0o600)

    print(f"Wrote {len(converted)} cookies to {out}")
    print(f"   Anchors present: {sorted(anchors_found)}")
    print(f"   Permissions: 600")
    print()
    print("Verify with:")
    print("   notebooklm auth check --test")


if __name__ == "__main__":
    main()
