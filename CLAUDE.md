# Claude Code Instructions

Follow `AGENTS.md` as the repository-wide source of working rules.

Claude Code can discover the project Skill at
`.claude/skills/red-govern/SKILL.md`. That directory must remain an exact mirror
of `agent-skills/red-govern/`; do not edit the mirror independently.

For Redshift governance recommendations, consult the canonical problem map and
preserve its `supported`, `conditional`, and `unsupported` classifications.

Red-Govern does not perform destructive remediation. Never request credentials
or unredacted production outputs. Do not invent Red-Govern commands, flags, or
capabilities.

Keep this adapter short and non-conflicting because multiple instruction files
may be loaded together.
