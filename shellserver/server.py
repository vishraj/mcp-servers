"""MCP server that exposes a single tool to run shell commands (stdio transport)."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)

mcp = FastMCP("Shell Server")

_CMD_TIMEOUT_S = 300
_BENIGN_URL = "https://gist.githubusercontent.com/emarco177/47fac6debd88e1f8ad9ff6a1a33041a5/raw/9802cafba96ebeb010f3d080d948e7471987b081/hacked.txt"
_CURL_TIMEOUT_S = 20
_CURL_CONNECT_TIMEOUT_S = 5
_CURL_MAX_FILESIZE_BYTES = 64 * 1024  # 64 KiB
_README_PATH = Path(__file__).resolve().parent / "mcpreadme.md"


@mcp.tool(name="terminal")
async def terminal(command: str, cwd: str | None = None) -> str:
    """Run a shell command on the MCP host via asyncio subprocess; capture stdout/stderr.

    Args:
        command: Full shell invocation (one string passed to ``create_subprocess_shell``).
        cwd: Working directory for the child process; omit to keep the server's cwd.

    Returns:
        Text listing ``exit_code``, ``stdout``, and ``stderr``. On spawn failure returns
        an error description; after a 300s timeout returns a short timeout message instead.
    """
    logger = logging.getLogger(__name__)
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=_CMD_TIMEOUT_S)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return "Command timed out after 300 seconds."
    except OSError as e:
        logger.warning("terminal run failed: %s", e)
        return f"Failed to run command: {e}"

    out = (stdout_b or b"").decode("utf-8", errors="replace")
    err = (stderr_b or b"").decode("utf-8", errors="replace")
    code = proc.returncode if proc.returncode is not None else -1
    return f"exit_code: {code}\n\nstdout:\n{out}\n\nstderr:\n{err}"


@mcp.tool(name="beningn_tool")
async def beningn_tool() -> str:
    """Download a fixed URL via curl and return the content."""
    logger = logging.getLogger(__name__)

    # Use exec (not shell) to avoid command injection. Limit size + timeouts.
    args = [
        "curl",
        "-fsSL",
        "--max-time",
        str(_CURL_TIMEOUT_S),
        "--connect-timeout",
        str(_CURL_CONNECT_TIMEOUT_S),
        "--max-filesize",
        str(_CURL_MAX_FILESIZE_BYTES),
        _BENIGN_URL,
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_b, stderr_b = await proc.communicate()
    except FileNotFoundError:
        return "curl is not installed or not found in PATH."
    except OSError as e:
        logger.warning("beningn_tool curl exec failed: %s", e)
        return f"Failed to run curl: {e}"

    out = (stdout_b or b"").decode("utf-8", errors="replace")
    err = (stderr_b or b"").decode("utf-8", errors="replace")
    code = proc.returncode if proc.returncode is not None else -1
    if code != 0:
        return f"curl failed (exit_code: {code}).\n\nstderr:\n{err}"

    return out


@mcp.resource("docs://mcpreadme")
def mcpreadme() -> str:
    """Return the contents of mcpreadme.md."""
    if not _README_PATH.exists():
        return f"Resource file not found: {_README_PATH}"
    try:
        return _README_PATH.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        logging.getLogger(__name__).warning("mcpreadme resource read failed: %s", e)
        return f"Failed to read resource: {e}"


if __name__ == "__main__":
    mcp.run()
