# notebooklm-py
<p align="left">
  <img src="https://raw.githubusercontent.com/teng-lin/notebooklm-py/main/notebooklm-py.png" alt="notebooklm-py logo" width="128">
</p>

**A Comprehensive NotebookLM Skill & Unofficial Python API.** Full programmatic access to NotebookLM's features—including capabilities the web UI doesn't expose—via Python, CLI, and AI agents like Claude Code, Codex, and OpenClaw.

[![PyPI version](https://img.shields.io/pypi/v/notebooklm-py.svg)](https://pypi.org/project/notebooklm-py/)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://pypi.org/project/notebooklm-py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/teng-lin/notebooklm-py/actions/workflows/test.yml/badge.svg)](https://github.com/teng-lin/notebooklm-py/actions/workflows/test.yml)
<p>
  <a href="https://trendshift.io/repositories/19116" target="_blank"><img src="https://trendshift.io/api/badge/repositories/19116" alt="teng-lin%2Fnotebooklm-py | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>
</p>

**Upstream source**: <https://github.com/teng-lin/notebooklm-py>
**This fork**: <https://github.com/win4r/notebooklm-py>

> **⚠️ Unofficial Library - Use at Your Own Risk**
>
> This library uses **undocumented Google APIs** that can change without notice.
>
> - **Not affiliated with Google** - This is a community project
> - **APIs may break** - Google can change internal endpoints anytime
> - **Rate limits apply** - Heavy usage may be throttled
>
> Best for prototypes, research, and personal projects. See [Troubleshooting](docs/troubleshooting.md) for debugging tips.

> **This is [`win4r`'s fork](https://github.com/win4r/notebooklm-py)** — adds Hermes Agent compatibility and security hardening on top of [upstream](https://github.com/teng-lin/notebooklm-py).
>
> - **Python source unchanged.** Fork's `src/` is byte-identical to upstream tag `v0.3.4`; we do not republish to PyPI.
> - **Hermes-ready layout.** [`skills/notebooklm/SKILL.md`](skills/notebooklm/SKILL.md) satisfies Hermes's 3-part identifier requirement (`owner/repo/path`) that the upstream root-level SKILL.md doesn't.
> - **Audit pinned.** Install commands below resolve the audited tag (see [`SECURITY_AUDIT.md`](skills/notebooklm/SECURITY_AUDIT.md)), not `latest`.
> - **For vanilla non-Hermes use**, prefer [upstream](https://github.com/teng-lin/notebooklm-py) directly — it gets updates first.

## What You Can Build

🤖 **AI Agent Tools** - Integrate NotebookLM into Claude Code, Codex, Hermes Agent, OpenClaw, and other LLM agents. Ships with a root [NotebookLM skill](SKILL.md) for `npx skills add` / `notebooklm skill install` (Claude Code, `.agents/`, OpenClaw), a [`skills/notebooklm/`](skills/notebooklm/SKILL.md) subdirectory layout for `hermes skills install`, and repo-level Codex guidance in [`AGENTS.md`](AGENTS.md).

📚 **Research Automation** - Bulk-import sources (URLs, PDFs, YouTube, Google Drive), run web/Drive research queries with auto-import, and extract insights programmatically. Build repeatable research pipelines.

🎙️ **Content Generation** - Generate Audio Overviews (podcasts), videos, slide decks, quizzes, flashcards, infographics, data tables, mind maps, and study guides. Full control over formats, styles, and output.

📥 **Downloads & Export** - Download all generated artifacts locally (MP3, MP4, PDF, PNG, CSV, JSON, Markdown). Export to Google Docs/Sheets. **Features the web UI doesn't offer**: batch downloads, quiz/flashcard export in multiple formats, mind map JSON extraction.

## Three Ways to Use

| Method | Best For |
|--------|----------|
| **Python API** | Application integration, async workflows, custom pipelines |
| **CLI** | Shell scripts, quick tasks, CI/CD automation |
| **Agent Integration** | Claude Code, Codex, LLM agents, natural language automation |

## Features

### Complete NotebookLM Coverage

| Category | Capabilities |
|----------|--------------|
| **Notebooks** | Create, list, rename, delete |
| **Sources** | URLs, YouTube, files (PDF, text, Markdown, Word, audio, video, images), Google Drive, pasted text; refresh, get guide/fulltext |
| **Chat** | Questions, conversation history, custom personas |
| **Research** | Web and Drive research agents (fast/deep modes) with auto-import |
| **Sharing** | Public/private links, user permissions (viewer/editor), view level control |

### Content Generation (All NotebookLM Studio Types)

| Type | Options | Download Format |
|------|---------|-----------------|
| **Audio Overview** | 4 formats (deep-dive, brief, critique, debate), 3 lengths, 50+ languages | MP3/MP4 |
| **Video Overview** | 3 formats (explainer, brief, cinematic), 9 visual styles, plus a dedicated `cinematic-video` CLI alias | MP4 |
| **Slide Deck** | Detailed or presenter format, adjustable length; individual slide revision | PDF, PPTX |
| **Infographic** | 3 orientations, 3 detail levels | PNG |
| **Quiz** | Configurable quantity and difficulty | JSON, Markdown, HTML |
| **Flashcards** | Configurable quantity and difficulty | JSON, Markdown, HTML |
| **Report** | Briefing doc, study guide, blog post, or custom prompt | Markdown |
| **Data Table** | Custom structure via natural language | CSV |
| **Mind Map** | Interactive hierarchical visualization | JSON |

### Beyond the Web UI

These features are available via API/CLI but not exposed in NotebookLM's web interface:

- **Batch downloads** - Download all artifacts of a type at once
- **Quiz/Flashcard export** - Get structured JSON, Markdown, or HTML (web UI only shows interactive view)
- **Mind map data extraction** - Export hierarchical JSON for visualization tools
- **Data table CSV export** - Download structured tables as spreadsheets
- **Slide deck as PPTX** - Download editable PowerPoint files (web UI only offers PDF)
- **Slide revision** - Modify individual slides with natural-language prompts
- **Report template customization** - Append extra instructions to built-in format templates
- **Save chat to notes** - Save Q&A answers or conversation history as notebook notes
- **Source fulltext access** - Retrieve the indexed text content of any source
- **Programmatic sharing** - Manage permissions without the UI

## Installation

This fork is **audit-pinned to tag `v0.3.4-hermes.1`** — upstream `v0.3.4` Python source plus this fork's Hermes layout, audit report, and import helper. Install from the fork tag to get a reproducible snapshot that matches [`SECURITY_AUDIT.md`](skills/notebooklm/SECURITY_AUDIT.md):

```bash
# Basic installation (from this fork's audited Hermes tag)
pip install "git+https://github.com/win4r/notebooklm-py@v0.3.4-hermes.1"

# With browser login support (required for first-time setup)
pip install "notebooklm-py[browser] @ git+https://github.com/win4r/notebooklm-py@v0.3.4-hermes.1"
playwright install chromium
```

If `playwright install chromium` fails with `TypeError: onExit is not a function`, see the Linux workaround in [Troubleshooting](docs/troubleshooting.md#linux).

> **Why `v0.3.4-hermes.1` instead of plain `v0.3.4` or PyPI?** — The plain `v0.3.4` tag (inherited from upstream) contains only upstream's `src/` and no fork assets. The `-hermes.1` suffix marks "upstream v0.3.4 src + this fork's skills/SECURITY_AUDIT.md/import_browser_cookies.py on top". Upstream's PyPI wheel 0.3.4 is unsigned (no [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) attestation) and generic install commands aren't version-pinned. Installing from this fork's named tag gives a reproducible, auditable source and activates the [upgrade guardrail](skills/notebooklm/SKILL.md). The `src/` directory is byte-identical to upstream `v0.3.4` — verified with `diff` against `git show v0.3.4:src/notebooklm/__init__.py` — so there's no functional difference, only a trust-chain swap.
>
> If you explicitly need PyPI (e.g. corporate package mirror, no GitHub access), `pip install "notebooklm-py==0.3.4"` from upstream is functionally equivalent but skips fork-local assets (`SECURITY_AUDIT.md`, `import_browser_cookies.py`, Hermes skill layout).

### Development Installation

For contributors or testing unreleased features:

```bash
pip install "git+https://github.com/win4r/notebooklm-py@main"
```

⚠️ The fork's `main` tracks upstream `main` plus this fork's Hermes-specific additions. It may contain unstable changes; use the tagged command above for production.

## Quick Start

<p align="center">
  <a href="https://asciinema.org/a/767284" target="_blank"><img src="https://asciinema.org/a/767284.svg" width="600" /></a>
  <br>
  <em>16-minute session compressed to 30 seconds</em>
</p>

### CLI

```bash
# 1. Authenticate (opens browser)
notebooklm login
# Or use Microsoft Edge (for orgs that require Edge for SSO)
# notebooklm login --browser msedge

# 2. Create a notebook and add sources
notebooklm create "My Research"
notebooklm use <notebook_id>
notebooklm source add "https://en.wikipedia.org/wiki/Artificial_intelligence"
notebooklm source add "./paper.pdf"

# 3. Chat with your sources
notebooklm ask "What are the key themes?"

# 4. Generate content
notebooklm generate audio "make it engaging" --wait
notebooklm generate video --style whiteboard --wait
notebooklm generate cinematic-video "documentary-style summary" --wait
notebooklm generate quiz --difficulty hard
notebooklm generate flashcards --quantity more
notebooklm generate slide-deck
notebooklm generate infographic --orientation portrait
notebooklm generate mind-map
notebooklm generate data-table "compare key concepts"

# 5. Download artifacts
notebooklm download audio ./podcast.mp3
notebooklm download video ./overview.mp4
notebooklm download cinematic-video ./documentary.mp4
notebooklm download quiz --format markdown ./quiz.md
notebooklm download flashcards --format json ./cards.json
notebooklm download slide-deck ./slides.pdf
notebooklm download infographic ./infographic.png
notebooklm download mind-map ./mindmap.json
notebooklm download data-table ./data.csv
```

Other useful CLI commands:

```bash
notebooklm auth check --test         # Diagnose auth/cookie issues
notebooklm agent show codex          # Print bundled Codex instructions
notebooklm agent show claude         # Print bundled Claude Code skill template
notebooklm language list             # List supported output languages
notebooklm metadata --json           # Export notebook metadata and sources
notebooklm share status              # Inspect sharing state
notebooklm source add-research "AI"  # Start web research and import sources
notebooklm skill status              # Check local agent skill installation
```

### Python API

```python
import asyncio
from notebooklm import NotebookLMClient

async def main():
    async with await NotebookLMClient.from_storage() as client:
        # Create notebook and add sources
        nb = await client.notebooks.create("Research")
        await client.sources.add_url(nb.id, "https://example.com", wait=True)

        # Chat with your sources
        result = await client.chat.ask(nb.id, "Summarize this")
        print(result.answer)

        # Generate content (podcast, video, quiz, etc.)
        status = await client.artifacts.generate_audio(nb.id, instructions="make it fun")
        await client.artifacts.wait_for_completion(nb.id, status.task_id)
        await client.artifacts.download_audio(nb.id, "podcast.mp3")

        # Generate quiz and download as JSON
        status = await client.artifacts.generate_quiz(nb.id)
        await client.artifacts.wait_for_completion(nb.id, status.task_id)
        await client.artifacts.download_quiz(nb.id, "quiz.json", output_format="json")

        # Generate mind map and export
        result = await client.artifacts.generate_mind_map(nb.id)
        await client.artifacts.download_mind_map(nb.id, "mindmap.json")

asyncio.run(main())
```

### Agent Setup

**Option 1 — CLI install** (Claude Code, `.agents/`, OpenClaw):

```bash
notebooklm skill install
```

Installs the skill into `~/.claude/skills/notebooklm` and `~/.agents/skills/notebooklm`.

**Option 2 — `npx` install** (open skills ecosystem):

```bash
npx skills add win4r/notebooklm-py
```

Fetches [SKILL.md](SKILL.md) directly from this fork. For the upstream canonical copy, substitute `teng-lin/notebooklm-py`.

**Option 3 — Hermes Agent** (uses the [`skills/notebooklm/`](skills/notebooklm/) subdirectory layout)

**Prerequisites**: Hermes Agent v0.10+ installed at the default path (`~/.hermes/hermes-agent/venv` exists), `uv` on your PATH (`brew install uv` / `pip install uv` if missing), and `~/.local/bin` on your `PATH` (already true if `which hermes` returns `~/.local/bin/hermes`).

```bash
# 1. Register this fork as a skill source and install the skill into Hermes
hermes skills tap add win4r/notebooklm-py
hermes skills install win4r/notebooklm-py/skills/notebooklm --force

# 2. Install the Python package into the Hermes venv (audited fork tag)
VIRTUAL_ENV=~/.hermes/hermes-agent/venv uv pip install \
  "notebooklm-py[browser] @ git+https://github.com/win4r/notebooklm-py@v0.3.4-hermes.1"
~/.hermes/hermes-agent/venv/bin/playwright install chromium

# 3. Expose the CLI on PATH (same pattern as `hermes` itself uses)
mkdir -p ~/.local/bin
ln -sf ~/.hermes/hermes-agent/venv/bin/notebooklm ~/.local/bin/notebooklm

# 4. Authenticate. If `notebooklm login` triggers Google's 48h new-device
#    cooldown, use the browser-session import described in the next section.
notebooklm login

# 5. Verify both the skill and the CLI are working
hermes skills list                     # should include a `notebooklm` entry
notebooklm auth check --test           # all rows should be ✓
notebooklm list                        # lists your NotebookLM notebooks
```

**Why `--force`, and the main-vs-tag caveat:**

- `--force` on `hermes skills install` is mandatory because Hermes's skills-guard flags the embedded `pip install` strings in SKILL.md as supply-chain signals. This is expected; see [`SECURITY_AUDIT.md`](skills/notebooklm/SECURITY_AUDIT.md) for the decision rationale and the upgrade protocol.
- Hermes's GitHub skill fetcher always pulls from the fork's `main` branch — there is no `--ref`/`--tag` flag ([`tools/skills_hub.py:483`](https://github.com/NousResearch/hermes-agent/blob/main/tools/skills_hub.py#L483) in upstream Hermes). This fork holds an invariant: **`main` always matches the latest audited tag** (currently `v0.3.4-hermes.1`). Before installing, check [compare view](https://github.com/win4r/notebooklm-py/compare/v0.3.4-hermes.1...main) — if `main` shows unreleased commits, wait for a re-tag before trusting the install.
- The Python package install in step 2 *is* tag-pinned via `git+...@v0.3.4-hermes.1`, so the pip path stays audit-respecting regardless of main drift.


## Importing Authentication from an Existing Browser

`notebooklm login` spawns a fresh Playwright Chromium, which Google treats as a
new device. After repeated fresh logins, Google may block new-device sign-in
for ~48 hours. If you are already signed into NotebookLM in your main browser,
you can reuse that session directly — no cooldown, no Playwright login flow.

Your existing browser is an already-trusted device, so its session cookies work
immediately when copied into the `storage_state.json` that this library reads.

### Steps

1. **Install a cookie-export extension** in your main browser:
   - Chrome / Edge / Brave / Arc: **[Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)** — open source, explicit "no network access" manifest
   - Firefox: **"cookies.txt"** by Lennon Hill

2. **Open <https://notebooklm.google.com>** and confirm the avatar in the top
   right is the Google account you want to use.

3. **Export cookies as JSON** via the extension:
   - In *Get cookies.txt LOCALLY*: click the extension icon → set **Export Format: JSON** → **Export As → JSON** → save anywhere (e.g. `/tmp/nb_cookies.json`).
   - The extension captures every cookie sent to `notebooklm.google.com`,
     including `HttpOnly` cookies such as `SID` that JavaScript cannot read.

4. **Convert to `storage_state.json`** using the helper script in this repo:

   ```bash
   python3 skills/notebooklm/import_browser_cookies.py /tmp/nb_cookies.json
   ```

   The script:
   - keeps only Google-domain cookies (drops everything else),
   - requires a session anchor (`SID`, `__Secure-1PSID`, or `__Secure-3PSID`),
   - writes `~/.notebooklm/storage_state.json` and `chmod 600` it.

   Override the output path with `--out PATH` or preview with `--dry-run`.

5. **Verify the session works**:

   ```bash
   notebooklm auth check --test   # All rows should be ✓, including "Token fetch"
   notebooklm list                # Should list your notebooks
   ```

6. **Delete the exported JSON immediately** — it contains live Google session
   credentials:

   ```bash
   rm /tmp/nb_cookies.json
   ```

### Security notes

- `~/.notebooklm/storage_state.json` contains your Google `SID` cookie. Treat
  it like a password — any process with read access can impersonate you on
  every cookie-authenticated Google service (Gmail, Drive, YouTube, etc.).
- This repo's `.gitignore` already excludes `.notebooklm/`, `storage_state.json`,
  and `*cookies*.json` to prevent accidental commits, but you should still
  audit before pushing.
- Cookies eventually expire (typically several months). When `notebooklm auth
  check` starts failing, repeat this procedure — the browser remains a trusted
  device so no 48-hour cooldown is triggered.
- For higher-risk automation, consider using a dedicated Google account with
  no access to sensitive services, rather than your primary account.


## Documentation

- **[CLI Reference](docs/cli-reference.md)** - Complete command documentation
- **[Python API](docs/python-api.md)** - Full API reference
- **[Configuration](docs/configuration.md)** - Storage and settings
- **[Release Guide](docs/releasing.md)** - Release checklist and packaging verification
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions
- **[API Stability](docs/stability.md)** - Versioning policy and stability guarantees

### For Contributors

- **[Development Guide](docs/development.md)** - Architecture, testing, and releasing
- **[RPC Development](docs/rpc-development.md)** - Protocol capture and debugging
- **[RPC Reference](docs/rpc-reference.md)** - Payload structures
- **[Changelog](CHANGELOG.md)** - Version history and release notes
- **[Security](SECURITY.md)** - Security policy and credential handling

## Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| **macOS** | ✅ Tested | Primary development platform |
| **Linux** | ✅ Tested | Fully supported |
| **Windows** | ✅ Tested | Tested in CI |

## Star History

[![Star History Chart](https://api.star-history.com/image?repos=teng-lin/notebooklm-py&type=timeline&legend=top-left)](https://www.star-history.com/?repos=teng-lin%2Fnotebooklm-py&type=timeline&legend=top-left)

## License

MIT License. See [LICENSE](LICENSE) for details.
