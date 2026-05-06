# shellserver

A small [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server built with the [Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk) (`FastMCP`). It exposes **tools** for shell commands and a fixed curl download, and **one resource** that serves the bundled `mcpreadme.md`.

## Requirements

- Python 3.13+
- Dependencies are declared in `pyproject.toml` (`mcp[cli]`).
- **`curl`** must be available on `PATH` for `beningn_tool`.

## Setup

From this directory:

```bash
uv sync
```

Or install with pip:

```bash
pip install "mcp[cli]>=1.27.0"
```

## Run locally

Starts the server on **stdio** (the usual transport for MCP clients such as Cursor or Claude Desktop):

```bash
uv run python server.py
```

## Tools

### `terminal`

Runs shell commands on the machine where the server process runs.

| Argument   | Type   | Description                                                      |
|-----------|--------|------------------------------------------------------------------|
| `command` | string | Shell command line to execute (`create_subprocess_shell`).       |
| `cwd`     | string | Optional working directory for the subprocess.                   |

The tool returns combined text including **exit code**, **stdout**, and **stderr**. Commands time out after **300 seconds**.

### `beningn_tool`

No arguments. Runs **`curl`** (non-interactive, fixed URL only) to download a small text file and returns the response body. Failures (missing `curl`, timeouts, non-zero exit) are returned as error text.

## Resources

| URI                 | Description                                      |
|---------------------|--------------------------------------------------|
| `docs://mcpreadme` | Full text of `mcpreadme.md` next to `server.py`. |

Clients use `resources/list` and `resources/read` with that URI.

## MCP client configuration (example)

Point the client at this repo’s interpreter and `server.py` (adjust paths):

```json
{
  "mcpServers": {
    "shellserver": {
      "command": "/absolute/path/to/shellserver/.venv/bin/python",
      "args": ["/absolute/path/to/shellserver/server.py"]
    }
  }
}
```

If you use `uv`:

```json
{
  "mcpServers": {
    "shellserver": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/shellserver", "python", "server.py"]
    }
  }
}
```

Exact config file location depends on your client; see your product’s MCP documentation.

## Security

- The **`terminal`** tool runs **arbitrary shell commands** as the user that starts the MCP server. Only enable this server where that risk is acceptable, and avoid exposing it over untrusted networks.
- **`beningn_tool`** performs an **outbound HTTP request** to a single hard-coded URL via `curl`, with timeouts and a max download size. It still depends on your trust in that endpoint and on `curl` on the host.
- The **`docs://mcpreadme`** resource reads **`mcpreadme.md`** from disk relative to the server script; do not put secrets in that file if the server is shared.

## References

- [Model Context Protocol](https://modelcontextprotocol.io/)
- Python SDK quickstart patterns use `FastMCP` from `mcp.server.fastmcp`; this server follows that style.
