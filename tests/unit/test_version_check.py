"""Tests for Python version check (#117)."""

import subprocess
import sys
import textwrap


def test_version_check_exits_on_old_python():
    """Verify that _version_check produces a clear error on unsupported Python."""
    script = textwrap.dedent("""\
        import sys
        from unittest.mock import patch

        with patch.object(sys, "version_info", (3, 9, 0)):
            from notebooklm._version_check import check_python_version
            check_python_version()
    """)
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "requires Python 3.10 or later" in result.stderr
    assert "3.9.0" in result.stderr


def test_version_check_passes_on_supported_python():
    """Verify that the version check passes on the current (supported) Python."""
    from notebooklm._version_check import check_python_version

    # Should not raise on current Python (>= 3.10)
    check_python_version()
