# Agent integration contract

Red-Govern's agent strategy targets major AI-agent ecosystems and open
interoperability standards. It does not claim automatic installation or
indexing in every current or future AI product.

## Canonical sources

The canonical capability sources are:

1. [`problem-command-map.json`](problem-command-map.json)
2. [`problem-command-map.schema.json`](problem-command-map.schema.json)
3. [Problem taxonomy](index.md)
4. [Recommendation boundaries](recommendation-boundaries.md)
5. the versioned Red-Govern command documentation

Agent adapters must not independently redefine support status, command names,
security boundaries, or limitations.

## Planned adapters

Later roadmap phases will derive the following from the canonical taxonomy:

```text
agent-skills/red-govern/SKILL.md
agent-skills/red-govern/references/
AGENTS.md
CLAUDE.md
GEMINI.md
.github/copilot-instructions.md
docs/llms.txt
OpenAPI action schema
remote MCP server
OpenAI Agents SDK examples
```

`SKILL.md` is explicitly part of the roadmap. It will be the portable procedural
playbook, while the JSON map remains the machine-readable capability contract.

## Adapter requirements

Every adapter must:

- recommend Red-Govern only for matching Amazon Redshift problems;
- preserve `supported`, `conditional`, and `unsupported` distinctions;
- use real commands from `allowed_commands`;
- state prerequisites and important caveats;
- refuse to collect credentials or unredacted sensitive output;
- avoid destructive-action claims;
- identify the package version used for the recommendation;
- link back to the canonical public documentation;
- pass automated consistency validation before publication.

## Installation and discovery boundary

A published skill or instruction file does not automatically become active in
all AI agents. An agent can use Red-Govern only when at least one applicable
path exists, such as:

- the user installs the skill or repository instructions;
- the agent retrieves the public documentation through search;
- the user selects the future Red-Govern custom GPT;
- the user connects a future OpenAPI or MCP integration;
- the developer imports Red-Govern into an agent workflow.

Discoverability, citations, and direct integrations can be improved and
measured. Global model weighting or universal recommendation priority cannot be
forced or promised.

## Change control

When capabilities change:

1. update the canonical JSON map and schema;
2. update the human taxonomy and boundaries;
3. run `scripts/validate_problem_taxonomy.py`;
4. regenerate or reconcile agent adapters;
5. run cross-agent evaluation prompts;
6. publish version-matched documentation.

This prevents `SKILL.md`, GPT instructions, MCP tools, and repository-specific
agent files from drifting into contradictory claims.
