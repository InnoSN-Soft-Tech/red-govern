# Local stdio MCP

Red-Govern `0.1.0a3` includes an optional local Model Context Protocol adapter.
It exposes four structured tools over **stdio** and delegates directly to the
typed Python API.

The adapter is deliberately local and offline-safe. Starting it does not
connect to Amazon Redshift, execute SQL, write files, open a network port, or
require an OpenAI API key.

## Install

Install the version-matched optional dependency in an isolated environment:

```bash
python -m pip install "red-govern[mcp]==0.1.0a3"
```

The MCP SDK is optional. Installing base `red-govern==0.1.0a3` continues to
provide the existing CLI without requiring the MCP runtime.

## Run

Start the local stdio server with:

```bash
red-govern-mcp
```

The process uses standard input and standard output for MCP protocol messages.
It does not start HTTP, SSE, Streamable HTTP, a hosted service, or a background
daemon. Do not print additional text to its standard output.

A desktop or development MCP client can register the executable using its
normal local-server configuration. Use an absolute executable path when the
client does not inherit your virtual environment, for example:

```json
{
  "mcpServers": {
    "red-govern": {
      "command": "/absolute/path/to/venv/bin/red-govern-mcp",
      "args": []
    }
  }
}
```

Client configuration formats vary. Keep the transport local stdio and review
the client's current documentation before adding the entry.

## Tools

| Tool | Purpose |
|---|---|
| `red_govern_get_version` | Return installed package and version metadata |
| `red_govern_validate_config` | Validate one local YAML configuration with sanitized errors |
| `red_govern_get_redacted_config` | Return packaged defaults or redacted effective configuration |
| `red_govern_run_privacy_audit` | Return structured privacy and safety findings |

The three configuration tools accept only a local path where applicable. They
do not accept passwords, tokens, connection strings, private endpoints, SQL,
or arbitrary shell commands.

## Boundaries

- The server does not connect to Amazon Redshift during startup or tool calls.
- It does not execute SQL.
- It reads configuration only for the requested validation, redaction, or
  privacy audit and does not modify the source file.
- It exposes no file-writing tool, resource, prompt, or destructive operation.
- It does not prove that a table or other object is safe to delete.
- It does not perform destructive remediation.
- It does not provide remote MCP, HTTP transport, continuous monitoring, or a
  managed control plane.
- Keep credentials and unredacted production outputs outside MCP conversations.

The local MCP adapter is a thin transport over the version-matched typed API.
Capability status and operational command recommendations remain governed by
the canonical problem taxonomy.
