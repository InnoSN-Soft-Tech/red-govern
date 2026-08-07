# Typed Python API

Red-Govern 0.1.0a3 provides a small, presentation-independent Python API for
offline-safe configuration and privacy operations.

This API is the shared contract for the CLI, the local stdio MCP adapter, the
OpenAI Agents SDK adapter, and later integrations. It does not connect to Amazon
Redshift and does not write files.

## Supported functions

```python
from red_govern.api import (
    get_redacted_config,
    get_version,
    run_privacy_audit,
    validate_config,
)
```

### `get_version()`

Returns structured package, version, platform, and alpha-status fields without
side effects.

### `validate_config(path)`

Loads and validates one local Red-Govern YAML file. A valid file returns its
configuration version and a safe source-path display.

Invalid files raise `ConfigurationError`. The API deliberately sanitizes the
error text so rejected configuration values are not repeated.

### `get_redacted_config(path=None)`

Returns effective configuration as structured data. Passing `None` uses the
packaged defaults, matching the safe default behavior of `config-show`.

The result redacts credential-related keys, Redshift endpoints and identities,
local output paths, history paths, and other environment-specific metadata.
The function reads configuration but does not modify the source file.

### `run_privacy_audit(path)`

Runs the existing Red-Govern privacy and safety audit and returns structured
findings, severity values, pass/fail status, warning count, and critical count.

Expanded home-directory paths and configured password-environment-variable
names are not returned in the agent-safe result.

## Example

```python
from pathlib import Path

from red_govern.api import (
    get_redacted_config,
    run_privacy_audit,
    validate_config,
)

config_path = Path("red-govern.yml")

validation = validate_config(config_path)
safe_config = get_redacted_config(config_path)
audit = run_privacy_audit(config_path)

print(validation.model_dump(mode="json"))
print(safe_config.model_dump(mode="json"))
print(audit.model_dump(mode="json"))
```

## Boundaries

- The API does not accept passwords, tokens, connection strings, or private
  endpoints as function parameters.
- It does not connect to Amazon Redshift.
- It does not execute SQL.
- It does not write or replace configuration files.
- It does not prove that an object is safe to delete.
- It does not perform destructive remediation.
- Operational collection functions remain outside this first API contract.
- Local stdio MCP reuses this typed API without expanding its authority; see
  [Local stdio MCP](mcp.md).
- OpenAI Agents SDK adapter also reuses this typed API without expanding its
  authority or running a model; see [OpenAI Agents SDK adapter](openai-agents.md).

Use documentation and API behavior that match the installed package version.
The current contract targets Red-Govern 0.1.0a3.
