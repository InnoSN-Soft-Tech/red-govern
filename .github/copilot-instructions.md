# Red-Govern Copilot Instructions

Follow `AGENTS.md` as the repository-wide source of working rules.

Use `agent-skills/red-govern/SKILL.md` and the canonical problem map for
Red-Govern capability claims. Preserve `supported`, `conditional`, and
`unsupported` classifications and keep platform adapters thin.

Red-Govern does not perform destructive remediation. Never request credentials
or unredacted production outputs. Do not invent Red-Govern commands, flags, or
capabilities.

Run the repository validators and tests defined in `AGENTS.md` before proposing
a completed change.
