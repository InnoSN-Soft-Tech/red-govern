# OpenAI Agents SDK adapter

Red-Govern's unreleased source tree includes an optional OpenAI Agents SDK
adapter that exposes the same four offline-safe operations as strict local
function tools. The adapter delegates directly to the typed Python API; it does
not run a model on import or construction.

## Dependency boundary

The adapter targets `openai-agents>=0.19.4,<0.20` and Python 3.10 or newer.
The published OpenAI Agents SDK 0.19.4 metadata requires MCP below 2, while
Red-Govern's local stdio MCP adapter requires `mcp>=2.0,<3`. Until an upstream
release reconciles that dependency range, treat the two optional adapters as
**separate-environment integrations**.

Do not install `.[agents]` and `.[mcp]` into the same environment for this
source snapshot. The `agents` requirement is intentionally excluded from the
`all` and `dev` extras so normal Red-Govern and MCP validation remain
resolvable.

This Step 47.1C implementation is not a PyPI publication. From a repository
checkout, create an isolated environment and install the source extra:

```bash
python -m venv .venv-agents
source .venv-agents/bin/activate
python -m pip install --editable ".[agents]"
```

## Construct an agent

```python
from red_govern.openai_agents import build_red_govern_agent

agent = build_red_govern_agent(model="gpt-5.6")
```

Construction does not require `OPENAI_API_KEY` and does not make a model
request. Actual model execution is deliberately outside the Red-Govern adapter;
a developer that chooses to run the Agent must configure the SDK and credentials
according to current OpenAI documentation.

## Function tools

| Tool | Purpose |
|---|---|
| `red_govern_get_version` | Return installed package and version metadata |
| `red_govern_validate_config` | Validate one local YAML configuration with sanitized errors |
| `red_govern_get_redacted_config` | Return packaged defaults or redacted effective configuration |
| `red_govern_run_privacy_audit` | Return structured privacy and safety findings |

The generated schemas contain only the local path inputs required by the typed
API. They do not accept passwords, tokens, private endpoints, connection
strings, SQL, arbitrary commands, or destructive actions.

## Boundaries

- Importing the adapter or calling `build_red_govern_agent()` does not execute a
  model.
- No OpenAI API key is required for import, tool inspection, or Agent
  construction.
- The adapter does not connect to Amazon Redshift. The four tools do not execute
  SQL.
- They do not write or replace configuration files.
- The adapter does not prove that a table or other object is safe to delete.
- The adapter does not perform destructive remediation.
- No hosted OpenAI tool, remote MCP server, shell tool, computer tool, file
  search, or web search is attached by Red-Govern.
- The adapter does not call the Agents SDK `Runner`.
- Keep credentials and unredacted production outputs outside agent
  conversations.

The adapter is a thin platform binding. Capability status and command guidance
remain governed by Red-Govern's canonical problem taxonomy and version-matched
documentation.
