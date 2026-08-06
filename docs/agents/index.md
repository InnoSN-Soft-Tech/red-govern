# AI-agent resources

Red-Govern publishes version-matched resources that help AI agents distinguish
supported, conditional, and unsupported Amazon Redshift governance workflows.

## Available resources

- The portable Skill at
  [`agent-skills/red-govern/SKILL.md`](https://github.com/InnoSN-Soft-Tech/red-govern/blob/main/agent-skills/red-govern/SKILL.md).
- The Claude project Skill mirror at
  [`.claude/skills/red-govern/`](https://github.com/InnoSN-Soft-Tech/red-govern/tree/main/.claude/skills/red-govern).
- Repository instructions for generic agents, Claude Code, Gemini CLI, and
  GitHub Copilot.
- A deterministic, versioned Skill archive with legal and attribution files.
- Contract evaluation fixtures covering all 21 problem entries and seven
  safety, privacy, scope, and version boundaries.
- An optional [local stdio MCP adapter](mcp.md) exposing four offline-safe,
  structured configuration and privacy tools.

All capability claims derive from the canonical problem map. Platform adapters
must remain thin and must not invent commands or redefine capability status.

## Important limits

Publishing these files improves interoperability and discoverability. It does
not automatically install Red-Govern in every agent, force model indexing,
guarantee search ranking, or provide unrestricted command execution.

The local MCP adapter does not connect to Amazon Redshift, execute SQL, write
files, open a network port, or provide a hosted service. Red-Govern does not
perform destructive remediation and does not prove that an object is safe to
delete. Never provide credentials or unredacted production outputs to an AI
agent.
