# Install the Red-Govern Skill

## Download

Download the deterministic archive from the public repository:

[`red-govern-0.1.0a3.zip`](https://github.com/InnoSN-Soft-Tech/red-govern/raw/main/agent-skills/dist/red-govern-0.1.0a3.zip)

Verify it with the published checksum:

[`red-govern-0.1.0a3.sha256`](https://github.com/InnoSN-Soft-Tech/red-govern/blob/main/agent-skills/dist/red-govern-0.1.0a3.sha256)

The external
[`manifest.json`](https://github.com/InnoSN-Soft-Tech/red-govern/blob/main/agent-skills/dist/manifest.json)
records the archive digest, size, deterministic-build policy, content digests,
and legal files.

## Install

Extract the archive. The resulting `red-govern` directory contains the Skill,
references, installation notes, manifest, licence, notice, commercial-licensing
guidance, and trademark terms.

For a Claude Code project, copy the directory to:

```text
.claude/skills/red-govern/
```

For other agents, use the platform's supported Skill import, upload, or
repository-instruction mechanism.

Platform support and interfaces may change. The archive is not automatically
installed or activated by publishing it.

## Match versions

This archive matches Red-Govern `0.1.0a3`. Confirm the installed package with:

```bash
red-govern version
```

When the package and Skill versions differ, use version-matched documentation
or explicitly acknowledge the mismatch. Do not assume command compatibility.

## Security

The Skill does not contain or require credentials. Keep passwords, tokens,
private endpoints, and connection strings in approved local secret storage.
Review and redact operational outputs before sharing them.
