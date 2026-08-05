# Red-Govern Agent Skill Bundle

This directory is the installation and attribution document included in the
deterministic Red-Govern `0.1.0a3` Skill archive.

## Contents

The archive contains:

- the portable `SKILL.md`;
- four version-matched references;
- this installation document;
- an internal content manifest;
- `LICENSE.md`;
- `COMMERCIAL_LICENSE.md`;
- `NOTICE`;
- `TRADEMARKS.md`.

## Installation

Extract the archive and place the resulting `red-govern` directory in a Skill
location supported by the target agent platform.

For a Claude Code project, the repository-local location is:

```text
.claude/skills/red-govern/
```

For another agent, use that platform's supported Skill import, upload, or
repository-instruction mechanism. Platform availability and user interfaces can
change. Publishing or downloading this archive does not automatically install,
activate, or index Red-Govern in every AI agent.

The Skill supplies guidance and routing rules. It does not grant Redshift
network access, credentials, permissions, or command-execution capability.

## Validation

From the Red-Govern source repository, validate the tracked archive with:

```bash
python scripts/build_agent_skill_distribution.py --check
python scripts/evaluate_agent_skill.py
python scripts/validate_agent_assets.py
```

The evaluation suite is deterministic contract validation. It does not execute
or score a live language model.

## Safety

Red-Govern does not perform destructive remediation. Never use the Skill to
claim that an object is safe to delete, collect credentials, or request
unredacted production reports.

## Copyright, licence, and trademarks

Copyright © InnoSN Soft Tech.

The bundled Red-Govern materials are source-available under the PolyForm
Perimeter License 1.0.1. The complete terms are included as `LICENSE.md`.

A separate written commercial licence may be required for a competing hosted
service, SaaS platform, library, plug-in, integration, interface, or other
competing product. See `COMMERCIAL_LICENSE.md`.

Required notices are included in `NOTICE`. Red-Govern and associated branding
are subject to the terms in `TRADEMARKS.md`.

Commercial enquiries: `info@snsoft.tech`
