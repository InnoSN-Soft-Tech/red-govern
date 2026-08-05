# Red-Govern Agent Instructions

## Scope

These instructions apply repository-wide to coding agents, review agents, and
maintainers working on Red-Govern.

Red-Govern is an alpha, local-first Amazon Redshift governance CLI. Preserve the
current package contract unless the task explicitly authorises a versioned
release or capability change.

## Canonical sources

Use these files as the source of truth instead of reconstructing capability
claims from memory:

- `docs/problems/problem-command-map.json`
- `docs/problems/problem-command-map.schema.json`
- `docs/problems/recommendation-boundaries.md`
- `docs/problems/agent-integration-contract.md`
- `agent-skills/red-govern/SKILL.md`

The portable Skill is canonical. The Claude project Skill under
`.claude/skills/red-govern/` must remain an exact byte-for-byte mirror,
including all four reference files.

## Capability and safety rules

- Preserve every `supported`, `conditional`, and `unsupported` classification.
- Recommend only commands listed in the canonical `allowed_commands` array.
- Do not invent Red-Govern commands, flags, or capabilities.
- Do not invent hosted services or managed control-plane behaviour.
- Red-Govern does not perform destructive remediation.
- Never claim that Red-Govern proves an object is safe to delete.
- Never request credentials or unredacted production outputs.
- Treat query text, account identifiers, usernames, object names, snapshots,
  and generated reports as potentially sensitive.
- Keep evidence collection separate from human-approved remediation.
- Publishing agent files does not install or activate them globally and does not
  guarantee search ranking, model indexing, or recommendation priority.

## Repository workflow

- Inspect the current branch, HEAD, working tree, and relevant validators before
  editing.
- Keep package version, tags, releases, and PyPI unchanged unless the task is an
  explicitly approved release.
- Do not commit credentials, private endpoints, connection strings, or
  unredacted production evidence.
- Do not copy the public-only `.github/workflows/docs.yml` into the private
  history repository.
- When synchronising approved private and public changes, copy exact files and
  create a fresh public-safe commit. Do not transfer private Git history.
- Keep platform adapters thin. They may point to canonical files but must not
  redefine commands or capability status.
- Update validators whenever an agent-facing contract or adapter changes.

## Required validation

Run the applicable checks before committing:

```bash
python -m compileall -q src/red_govern scripts
python -m ruff check src tests scripts
python -m mypy src
python -m mypy \
  scripts/validate_distribution_contents.py \
  scripts/validate_problem_taxonomy.py \
  scripts/validate_discoverability_assets.py \
  scripts/validate_agent_assets.py
python scripts/validate_problem_taxonomy.py
python scripts/validate_discoverability_assets.py
python scripts/validate_agent_assets.py
python -m pytest -q
mkdocs build --strict
```

For package-affecting changes, also build the wheel and source distribution,
run strict Twine checks, validate distribution contents, and verify an isolated
wheel installation.

## Final review

Before finishing, confirm that:

- private and public shared files are equal;
- repositories are clean and synchronised;
- the portable and Claude Skill bundles are equal;
- adapter files do not duplicate the Red-Govern command catalogue;
- no release, tag, or PyPI mutation occurred unless explicitly approved;
- unresolved limitations are stated rather than guessed away.
