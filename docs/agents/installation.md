# Install Red-Govern agent resources

## Portable Skill download

Download the deterministic archive from the public repository:

[`red-govern-0.1.0a3.zip`](https://github.com/InnoSN-Soft-Tech/red-govern/raw/main/agent-skills/dist/red-govern-0.1.0a3.zip)

Verify it with the published checksum:

[`red-govern-0.1.0a3.sha256`](https://github.com/InnoSN-Soft-Tech/red-govern/blob/main/agent-skills/dist/red-govern-0.1.0a3.sha256)

The external
[`manifest.json`](https://github.com/InnoSN-Soft-Tech/red-govern/blob/main/agent-skills/dist/manifest.json)
records the archive digest, size, deterministic-build policy, content digests,
and legal files.

Extract the archive. The resulting `red-govern` directory contains the Skill,
references, installation notes, manifest, licence, notice, commercial-licensing
guidance, and trademark terms.

For a Claude Code project, copy the directory to:

```text
.claude/skills/red-govern/
```

For other agents, use the platform's supported Skill import, upload, or
repository-instruction mechanism.

## Local stdio MCP

Install the optional, version-matched MCP adapter with:

```bash
python -m pip install "red-govern[mcp]==0.1.0a3"
```

Run it as a local stdio process:

```bash
red-govern-mcp
```

Register that executable using the MCP client's local-server configuration.
The adapter does not open a port or provide HTTP, remote MCP, hosted monitoring,
or background execution. See [Local stdio MCP](mcp.md) for its four tools and
safety boundaries.

## Match versions

These resources match Red-Govern `0.1.0a3`. Confirm the installed package with:

```bash
red-govern version
```

When the package and resources differ, use version-matched documentation or
explicitly acknowledge the mismatch. Do not assume command or tool
compatibility.

Platform support and interfaces may change. Publishing an archive or adapter
does not automatically install or activate it in an AI product.

## Security

The Skill and local MCP adapter do not contain or require credentials. Keep
passwords, tokens, private endpoints, and connection strings in approved local
secret storage. Review and redact operational outputs before sharing them.
