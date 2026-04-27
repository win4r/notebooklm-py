"""CLI helper utilities.

Provides common functionality for all CLI commands:
- Authentication handling (get_client)
- Async execution (run_async)
- Error handling
- JSON/Rich output formatting
- Context management (current notebook/conversation)
- @with_client decorator for command boilerplate reduction
"""

import asyncio
import json
import logging
import os
import time
from functools import wraps
from typing import TYPE_CHECKING

import click
from rich.console import Console
from rich.table import Table

from ..auth import (
    AuthTokens,
    fetch_tokens,
    load_auth_from_storage,
)
from ..exceptions import RPCTimeoutError
from ..paths import get_context_path
from ..types import ArtifactType

if TYPE_CHECKING:
    from ..types import Artifact

console = Console()
logger = logging.getLogger(__name__)

# CLI artifact type name aliases
_CLI_ARTIFACT_ALIASES = {
    "flashcard": "flashcards",  # CLI uses singular, enum uses plural
}


def cli_name_to_artifact_type(name: str) -> ArtifactType | None:
    """Convert CLI artifact type name to ArtifactType enum.

    Args:
        name: CLI artifact type name (e.g., "video", "slide-deck", "flashcard").
            Use "all" to get None (no filter).

    Returns:
        ArtifactType enum member, or None if name is "all".

    Raises:
        KeyError: If name is not a valid artifact type.
    """
    if name == "all":
        return None

    # Handle aliases
    name = _CLI_ARTIFACT_ALIASES.get(name, name)

    # Convert kebab-case to snake_case and uppercase for enum lookup
    enum_name = name.upper().replace("-", "_")
    return ArtifactType[enum_name]


# =============================================================================
# ASYNC EXECUTION
# =============================================================================


def run_async(coro):
    """Run async coroutine in sync context."""
    return asyncio.run(coro)


def _normalize_import_key(source: dict) -> tuple[str, str] | None:
    """Build a stable matching key for a research source import candidate."""
    if not isinstance(source, dict):
        return None

    url = source.get("url")
    if isinstance(url, str) and url:
        return ("url", url)

    title = source.get("title")
    if isinstance(title, str) and title:
        return ("title", title)

    return None


def _source_object_import_key(source) -> tuple[str, str] | None:
    """Build the same stable key from a Source object returned by sources.list()."""
    url = getattr(source, "url", None)
    if isinstance(url, str) and url:
        return ("url", url)

    title = getattr(source, "title", None)
    if isinstance(title, str) and title:
        return ("title", title)

    return None


async def _find_newly_imported_sources(
    client,
    notebook_id: str,
    expected_sources: list[dict],
    baseline_source_ids: set[str],
) -> list[dict[str, str]]:
    """Inspect notebook sources and return newly imported matches for expected sources."""
    current_sources = await client.sources.list(notebook_id)
    expected_key_order = [
        key for source in expected_sources if (key := _normalize_import_key(source)) is not None
    ]
    if not expected_key_order:
        return []

    available_by_key: dict[tuple[str, str], list[dict[str, str]]] = {}
    for source in current_sources:
        source_id = getattr(source, "id", None)
        if not isinstance(source_id, str) or source_id in baseline_source_ids:
            continue

        key = _source_object_import_key(source)
        if key is None:
            continue

        available_by_key.setdefault(key, []).append(
            {"id": source_id, "title": getattr(source, "title", "") or ""}
        )

    matched: list[dict[str, str]] = []
    for key in expected_key_order:
        bucket = available_by_key.get(key)
        if bucket:
            matched.append(bucket.pop(0))

    return matched


async def import_with_retry(
    client,
    notebook_id: str,
    task_id: str,
    sources: list[dict],
    *,
    max_elapsed: float = 1800,
    initial_delay: float = 5,
    backoff_factor: float = 2,
    max_delay: float = 60,
    json_output: bool = False,
) -> list[dict[str, str]]:
    """Retry research import on RPC timeouts with exponential backoff.

    This is intentionally CLI-only policy. Library consumers calling
    `client.research.import_sources()` directly still get one-shot behavior.

    Important: IMPORT_RESEARCH can time out even when the server already created
    notebook sources. Before retrying, re-check the notebook and stop if all
    requested sources already appeared; otherwise retry only the remaining ones.
    """
    started_at = time.monotonic()
    delay = initial_delay
    attempt = 1
    baseline_source_ids = {
        source.id for source in await client.sources.list(notebook_id) if isinstance(source.id, str)
    }
    pending_sources = list(sources)
    imported_matches: list[dict[str, str]] = []

    while pending_sources:
        try:
            imported = await client.research.import_sources(notebook_id, task_id, pending_sources)
            return imported_matches + imported
        except RPCTimeoutError:
            recovered = await _find_newly_imported_sources(
                client,
                notebook_id,
                pending_sources,
                baseline_source_ids,
            )
            if recovered:
                imported_matches.extend(recovered)
                baseline_source_ids.update(item["id"] for item in recovered)
                recovered_count = len(recovered)
                pending_sources = pending_sources[recovered_count:]
                if not pending_sources:
                    logger.warning(
                        "IMPORT_RESEARCH timed out for notebook %s but all requested sources appeared in notebook; suppressing retry",
                        notebook_id,
                    )
                    return imported_matches

            elapsed = time.monotonic() - started_at
            remaining = max_elapsed - elapsed
            if remaining <= 0:
                raise

            sleep_for = min(delay, max_delay, remaining)
            logger.warning(
                "IMPORT_RESEARCH timed out for notebook %s; retrying in %.1fs (attempt %d, %.1fs elapsed, %d sources still pending)",
                notebook_id,
                sleep_for,
                attempt + 1,
                elapsed,
                len(pending_sources),
            )
            if not json_output:
                console.print(
                    f"[yellow]Import timed out; retrying in {sleep_for:.0f}s "
                    f"(attempt {attempt + 1}, {len(pending_sources)} still pending)[/yellow]"
                )
            await asyncio.sleep(sleep_for)
            delay = min(delay * backoff_factor, max_delay)
            attempt += 1

    return imported_matches


# =============================================================================
# AUTHENTICATION
# =============================================================================


def get_client(ctx) -> tuple[dict, str, str]:
    """Get auth components from context.

    Args:
        ctx: Click context with optional storage_path in obj

    Returns:
        Tuple of (cookies, csrf_token, session_id)

    Raises:
        FileNotFoundError: If auth storage not found
    """
    storage_path = ctx.obj.get("storage_path") if ctx.obj else None
    cookies = load_auth_from_storage(storage_path)
    csrf, session_id = run_async(fetch_tokens(cookies))
    return cookies, csrf, session_id


def get_auth_tokens(ctx) -> AuthTokens:
    """Get AuthTokens object from context.

    Args:
        ctx: Click context

    Returns:
        AuthTokens ready for client construction
    """
    cookies, csrf, session_id = get_client(ctx)
    return AuthTokens(cookies=cookies, csrf_token=csrf, session_id=session_id)


# =============================================================================
# CONTEXT MANAGEMENT
# =============================================================================


def _get_context_value(key: str) -> str | None:
    """Read a single value from context.json."""
    context_file = get_context_path()
    if not context_file.exists():
        return None
    try:
        data = json.loads(context_file.read_text(encoding="utf-8"))
        return data.get(key)
    except json.JSONDecodeError:
        logger.warning(
            "Context file %s is corrupted; cannot read '%s'. Run 'notebooklm clear' to reset.",
            context_file,
            key,
        )
        return None
    except OSError as e:
        logger.warning("Cannot read context file %s: %s", context_file, e)
        return None


def _set_context_value(key: str, value: str | None) -> None:
    """Set or clear a single value in context.json."""
    context_file = get_context_path()
    if not context_file.exists():
        return
    try:
        data = json.loads(context_file.read_text(encoding="utf-8"))
        if value is not None:
            data[key] = value
        elif key in data:
            del data[key]
        context_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except json.JSONDecodeError:
        logger.warning(
            "Context file %s is corrupted; cannot update '%s'. Run 'notebooklm clear' to reset.",
            context_file,
            key,
        )
    except OSError as e:
        logger.warning("Failed to write context file %s for key '%s': %s", context_file, key, e)


def get_current_notebook() -> str | None:
    """Get the current notebook ID from context."""
    return _get_context_value("notebook_id")


def set_current_notebook(
    notebook_id: str,
    title: str | None = None,
    is_owner: bool | None = None,
    created_at: str | None = None,
):
    """Set the current notebook context.

    conversation_id is never preserved — the server owns the canonical ID per
    notebook, and a stale local value would silently use the wrong UUID.
    """
    context_file = get_context_path()
    context_file.parent.mkdir(parents=True, exist_ok=True)

    data: dict[str, str | bool] = {"notebook_id": notebook_id}
    if title:
        data["title"] = title
    if is_owner is not None:
        data["is_owner"] = is_owner
    if created_at:
        data["created_at"] = created_at

    context_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def clear_context() -> bool:
    """Clear the current context.

    Returns True if a context file was removed, False if none existed.
    """
    context_file = get_context_path()
    if context_file.exists():
        context_file.unlink()
        return True
    return False


def get_current_conversation() -> str | None:
    """Get the current conversation ID from context."""
    return _get_context_value("conversation_id")


def set_current_conversation(conversation_id: str | None):
    """Set or clear the current conversation ID in context."""
    _set_context_value("conversation_id", conversation_id)


def validate_id(entity_id: str, entity_name: str = "ID") -> str:
    """Validate and normalize an entity ID.

    Args:
        entity_id: The ID to validate
        entity_name: Name for error messages (e.g., "notebook", "source")

    Returns:
        Stripped ID

    Raises:
        click.ClickException: If ID is empty or whitespace-only
    """
    if not entity_id or not entity_id.strip():
        raise click.ClickException(f"{entity_name} ID cannot be empty")
    return entity_id.strip()


def require_notebook(notebook_id: str | None) -> str:
    """Get notebook ID from argument or context, raise if neither.

    Args:
        notebook_id: Optional notebook ID from command argument

    Returns:
        Notebook ID (from argument or context), validated and stripped

    Raises:
        SystemExit: If no notebook ID available
        click.ClickException: If notebook ID is empty/whitespace
    """
    if notebook_id:
        return validate_id(notebook_id, "Notebook")
    current = get_current_notebook()
    if current:
        return validate_id(current, "Notebook")
    console.print(
        "[red]No notebook specified. Use 'notebooklm use <id>' to set context or provide notebook_id.[/red]"
    )
    raise SystemExit(1)


async def _resolve_partial_id(
    partial_id: str,
    list_fn,
    entity_name: str,
    list_command: str,
) -> str:
    """Generic partial ID resolver.

    Allows users to type partial IDs like 'abc' instead of full UUIDs.
    Matches are case-insensitive prefix matches.

    Args:
        partial_id: Full or partial ID to resolve
        list_fn: Async function that returns list of items with id/title attributes
        entity_name: Name for error messages (e.g., "notebook", "source")
        list_command: CLI command to list items (e.g., "list", "source list")

    Returns:
        Full ID of the matched item

    Raises:
        click.ClickException: If ID is empty, no match, or ambiguous match
    """
    # Validate and normalize the ID
    partial_id = validate_id(partial_id, entity_name)

    # Skip resolution for IDs that look complete (20+ chars)
    if len(partial_id) >= 20:
        return partial_id

    items = await list_fn()
    matches = [item for item in items if item.id.lower().startswith(partial_id.lower())]

    if len(matches) == 1:
        if matches[0].id != partial_id:
            title = matches[0].title or "(untitled)"
            console.print(f"[dim]Matched: {matches[0].id[:12]}... ({title})[/dim]")
        return matches[0].id
    elif len(matches) == 0:
        raise click.ClickException(
            f"No {entity_name} found starting with '{partial_id}'. "
            f"Run 'notebooklm {list_command}' to see available {entity_name}s."
        )
    else:
        lines = [f"Ambiguous ID '{partial_id}' matches {len(matches)} {entity_name}s:"]
        for item in matches[:5]:
            title = item.title or "(untitled)"
            lines.append(f"  {item.id[:12]}... {title}")
        if len(matches) > 5:
            lines.append(f"  ... and {len(matches) - 5} more")
        lines.append("\nSpecify more characters to narrow down.")
        raise click.ClickException("\n".join(lines))


async def resolve_notebook_id(client, partial_id: str) -> str:
    """Resolve partial notebook ID to full ID."""
    return await _resolve_partial_id(
        partial_id,
        list_fn=lambda: client.notebooks.list(),
        entity_name="notebook",
        list_command="list",
    )


async def resolve_source_id(client, notebook_id: str, partial_id: str) -> str:
    """Resolve partial source ID to full ID."""
    return await _resolve_partial_id(
        partial_id,
        list_fn=lambda: client.sources.list(notebook_id),
        entity_name="source",
        list_command="source list",
    )


async def resolve_artifact_id(client, notebook_id: str, partial_id: str) -> str:
    """Resolve partial artifact ID to full ID."""
    return await _resolve_partial_id(
        partial_id,
        list_fn=lambda: client.artifacts.list(notebook_id),
        entity_name="artifact",
        list_command="artifact list",
    )


async def resolve_note_id(client, notebook_id: str, partial_id: str) -> str:
    """Resolve partial note ID to full ID."""
    return await _resolve_partial_id(
        partial_id,
        list_fn=lambda: client.notes.list(notebook_id),
        entity_name="note",
        list_command="note list",
    )


async def resolve_source_ids(
    client, notebook_id: str, source_ids: tuple[str, ...]
) -> list[str] | None:
    """Resolve multiple partial source IDs to full IDs.

    Args:
        client: NotebookLM client
        notebook_id: Resolved notebook ID
        source_ids: Tuple of partial source IDs from CLI

    Returns:
        List of resolved source IDs, or None if no source IDs provided
    """
    if not source_ids:
        return None
    resolved = []
    for sid in source_ids:
        resolved.append(await resolve_source_id(client, notebook_id, sid))
    return resolved


# =============================================================================
# ERROR HANDLING
# =============================================================================


def handle_error(e: Exception):
    """Handle and display errors consistently."""
    console.print(f"[red]Error: {e}[/red]")
    raise SystemExit(1)


def handle_auth_error(json_output: bool = False):
    """Handle authentication errors with helpful context."""
    from ..paths import get_path_info, get_storage_path

    path_info = get_path_info()
    storage_path = get_storage_path()
    has_env_var = bool(os.environ.get("NOTEBOOKLM_AUTH_JSON"))
    has_home_env = bool(os.environ.get("NOTEBOOKLM_HOME"))
    storage_source = path_info["home_source"]

    if json_output:
        json_error_response(
            "AUTH_REQUIRED",
            "Auth not found. Run 'notebooklm login' first.",
            extra={
                "checked_paths": {
                    "storage_file": str(storage_path),
                    "storage_source": storage_source,
                    "env_var": "NOTEBOOKLM_AUTH_JSON" if has_env_var else None,
                },
                "help": "Run 'notebooklm login' or set NOTEBOOKLM_AUTH_JSON",
            },
        )
    else:
        console.print("[red]Not logged in.[/red]\n")
        console.print("[dim]Checked locations:[/dim]")
        console.print(f"  • Storage file: [cyan]{storage_path}[/cyan]")
        if has_home_env:
            console.print("    [dim](via $NOTEBOOKLM_HOME)[/dim]")
        env_status = "[yellow]set but invalid[/yellow]" if has_env_var else "[dim]not set[/dim]"
        console.print(f"  • NOTEBOOKLM_AUTH_JSON: {env_status}")
        console.print("\n[bold]Options to authenticate:[/bold]")
        console.print("  1. Run: [green]notebooklm login[/green]")
        console.print("  2. Set [cyan]NOTEBOOKLM_AUTH_JSON[/cyan] env var (for CI/CD)")
        console.print("  3. Use [cyan]--storage /path/to/file.json[/cyan] flag")
        raise SystemExit(1)


# =============================================================================
# DECORATORS
# =============================================================================


def with_client(f):
    """Decorator that handles auth, async execution, and errors for CLI commands.

    This decorator eliminates boilerplate from commands that need:
    - Authentication (get AuthTokens from context)
    - Async execution (run coroutine with asyncio.run)
    - Error handling (auth errors, general exceptions)

    The decorated function stays SYNC (Click doesn't support async) but returns
    a coroutine. The decorator runs the coroutine and handles errors.

    Usage:
        @cli.command("list")
        @click.option("--json", "json_output", is_flag=True)
        @with_client
        def list_notebooks(ctx, json_output, client_auth):
            async def _run():
                async with NotebookLMClient(client_auth) as client:
                    notebooks = await client.notebooks.list()
                    output_notebooks(notebooks, json_output)
            return _run()

    Args:
        f: Function that accepts client_auth (AuthTokens) and returns a coroutine

    Returns:
        Decorated function with Click pass_context
    """

    @wraps(f)
    @click.pass_context
    def wrapper(ctx, *args, **kwargs):
        cmd_name = f.__name__
        start = time.monotonic()
        logger.debug("CLI command starting: %s", cmd_name)

        json_output = kwargs.get("json_output", False)

        def log_result(status: str, detail: str = "") -> float:
            elapsed = time.monotonic() - start
            if detail:
                logger.debug("CLI command %s: %s (%.3fs) - %s", status, cmd_name, elapsed, detail)
            else:
                logger.debug("CLI command %s: %s (%.3fs)", status, cmd_name, elapsed)
            return elapsed

        try:
            try:
                auth = get_auth_tokens(ctx)
            except FileNotFoundError:
                log_result("failed", "not authenticated")
                handle_auth_error(json_output)
                return  # unreachable (handle_auth_error raises SystemExit), but keeps mypy happy
            coro = f(ctx, *args, client_auth=auth, **kwargs)
            result = run_async(coro)
            log_result("completed")
            return result
        except Exception as e:
            log_result("failed", str(e))
            if json_output:
                json_error_response("ERROR", str(e))
            else:
                handle_error(e)

    return wrapper


# =============================================================================
# OUTPUT FORMATTING
# =============================================================================


def json_output_response(data: dict) -> None:
    """Print JSON response (no colors for machine parsing)."""
    click.echo(json.dumps(data, indent=2, default=str))


def json_error_response(code: str, message: str, extra: dict | None = None) -> None:
    """Print JSON error and exit (no colors for machine parsing).

    Args:
        code: Error code (e.g., "AUTH_REQUIRED", "ERROR")
        message: Human-readable error message
        extra: Optional additional data to include in response
    """
    response = {"error": True, "code": code, "message": message}
    if extra:
        response.update(extra)
    click.echo(json.dumps(response, indent=2))
    raise SystemExit(1)


_RESULT_TYPE_LABELS = {
    1: "Web",
    2: "Drive",
    5: "Report",
    "web": "Web",
    "drive": "Drive",
    "report": "Report",
}


def display_research_sources(sources: list[dict], max_display: int = 10) -> None:
    """Display research sources in a formatted table.

    Args:
        sources: List of source dicts with 'title', 'url', and optional 'result_type' keys
        max_display: Maximum sources to show before truncating (default 10)
    """
    console.print(f"[bold]Found {len(sources)} sources[/bold]")

    if sources:
        # Only show Type column if any source has result_type
        has_types = any("result_type" in s for s in sources)

        table = Table(show_header=True, header_style="bold")
        table.add_column("Title", style="cyan")
        if has_types:
            table.add_column("Type", style="yellow")
        table.add_column("URL", style="dim")
        for src in sources[:max_display]:
            row = [src.get("title", "Untitled")[:50]]
            if has_types:
                rt: int | None = src.get("result_type")
                label = (
                    _RESULT_TYPE_LABELS.get(rt, str(rt) if rt is not None else "")
                    if rt is not None
                    else ""
                )
                row.append(label)
            row.append(src.get("url", "")[:60])
            table.add_row(*row)
        if len(sources) > max_display:
            extra_row = [f"... and {len(sources) - max_display} more"]
            if has_types:
                extra_row.append("")
            extra_row.append("")
            table.add_row(*extra_row)
        console.print(table)


def display_report(report: str, max_chars: int = 1000, json_hint: bool = True) -> None:
    """Display a research report, truncated for terminal output.

    Args:
        report: The report markdown text.
        max_chars: Maximum characters to display (default 1000).
        json_hint: Whether to suggest --json for full output in truncation message.
    """
    if not report:
        return
    console.print("\n[bold]Report:[/bold]")
    console.print(report[:max_chars], markup=False)
    if len(report) > max_chars:
        hint = " use --json for full report" if json_hint else ""
        console.print(
            f"[dim]... (truncated,{hint})[/dim]" if hint else "[dim]... (truncated)[/dim]"
        )


# =============================================================================
# TYPE DISPLAY HELPERS
# =============================================================================


def get_artifact_type_display(artifact: "Artifact") -> str:
    """Get display string for artifact type.

    Args:
        artifact: Artifact object

    Returns:
        Display string with emoji
    """
    from notebooklm import ArtifactType

    kind = artifact.kind

    # Map ArtifactType enum to display strings
    display_map = {
        ArtifactType.AUDIO: "🎧 Audio",
        ArtifactType.VIDEO: "🎬 Video",
        ArtifactType.QUIZ: "📝 Quiz",
        ArtifactType.FLASHCARDS: "🃏 Flashcards",
        ArtifactType.MIND_MAP: "🧠 Mind Map",
        ArtifactType.INFOGRAPHIC: "🖼️ Infographic",
        ArtifactType.SLIDE_DECK: "📊 Slide Deck",
        ArtifactType.DATA_TABLE: "📈 Data Table",
    }

    # Handle report subtypes specially
    if kind == ArtifactType.REPORT:
        report_displays = {
            "briefing_doc": "📋 Briefing Doc",
            "study_guide": "📚 Study Guide",
            "blog_post": "✍️ Blog Post",
            "report": "📄 Report",
        }
        return report_displays.get(artifact.report_subtype or "report", "📄 Report")

    return display_map.get(kind, f"Unknown ({kind})")


def get_source_type_display(source_type: str) -> str:
    """Get display string for source type.

    Args:
        source_type: Type string from Source.kind (SourceType str enum)

    Returns:
        Display string with emoji
    """
    # Extract value if it's a SourceType enum, otherwise use as-is
    type_str = source_type.value if hasattr(source_type, "value") else str(source_type)
    type_map = {
        # From SourceType str enum values (types.py)
        "google_docs": "📄 Google Docs",
        "google_slides": "📊 Google Slides",
        "google_spreadsheet": "📊 Google Sheets",
        "pdf": "📄 PDF",
        "pasted_text": "📝 Pasted Text",
        "docx": "📝 DOCX",
        "web_page": "🌐 Web Page",
        "markdown": "📝 Markdown",
        "youtube": "🎬 YouTube",
        "media": "🎵 Media",
        "google_drive_audio": "🎧 Drive Audio",
        "google_drive_video": "🎬 Drive Video",
        "image": "🖼️ Image",
        "csv": "📊 CSV",
        "epub": "📕 EPUB",
        "unknown": "❓ Unknown",
    }
    return type_map.get(type_str, f"❓ {type_str}")
