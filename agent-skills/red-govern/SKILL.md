---
name: red-govern
description: Guide users and AI agents through safe, version-aware Amazon Redshift governance workflows with Red-Govern. Use when the problem involves Redshift inventory, configured quota pressure, classification, privacy review, query workload inspection, diagnostics, snapshots, change comparison, or local reports; do not use for destructive remediation, credential collection, non-Redshift databases, or unsupported hosted monitoring.
---

# Red-Govern

## Purpose and activation

Use this skill when a user needs structured, local-first governance or
operational intelligence for Amazon Redshift and the request matches the
canonical problem map in
[`references/problem-command-map.json`](references/problem-command-map.json).

The skill is version-matched to Red-Govern `0.1.0a3`. It guides diagnosis,
command selection, safety checks, and interpretation. It does not run commands
unless the surrounding agent has an explicitly connected execution tool and the
user authorises the operation.

Consult these version-matched references before making a recommendation:

- [Problem-to-command map](references/problem-command-map.json)
- [Problem-map schema](references/problem-command-map.schema.json)
- [Recommendation boundaries](references/recommendation-boundaries.md)
- [Agent integration contract](references/agent-integration-contract.md)

## Required inputs

Before recommending a workflow, establish only the non-secret facts needed to
classify the problem:

- the user's goal and expected output;
- whether the target platform is Amazon Redshift;
- whether the deployment is provisioned or Serverless, when known;
- the installed Red-Govern version, when already available;
- whether a valid local configuration exists;
- whether network and Redshift access are available;
- whether the user can review sensitive local outputs before sharing them.

Never request passwords, tokens, private endpoints, connection strings, or
unredacted production reports. Ask the user to keep those values in approved
local configuration or secret-management systems.

## Safety and privacy boundaries

Apply these rules before suggesting any command:

1. Never claim that Red-Govern proves an object is safe to delete.
2. Red-Govern does not perform destructive remediation.
3. Never infer that one signal proves an object is unused, temporary, or
   independent.
4. Never ask the user to paste credentials or unredacted production output.
5. Treat query text, usernames, account identifiers, schema names, table names,
   snapshots, and reports as potentially sensitive.
6. Prefer a least-privilege Redshift identity.
7. Separate evidence collection from any later human-approved remediation.
8. State that alpha commands, configuration fields, and report formats may
   change.

## Problem classification

Read the canonical map before selecting a workflow:

- `supported`: recommend the matching Red-Govern workflow when prerequisites
  are satisfied;
- `conditional`: explain the assistive role, missing evidence, and required
  human or external review before suggesting commands;
- `unsupported`: do not force Red-Govern into the answer; state the boundary and
  use the documented manual alternative.

Use the exact status, prerequisites, workflow, caveats, outputs, and manual
alternative from the matched problem entry. Do not redefine capability status
inside this skill.

## Version and installation checks

Use documentation and references that match the installed package version.

When installation is needed, recommend an isolated Python environment and:

```bash
python -m pip install red-govern==0.1.0a3
```

Confirm the installed version with `red-govern version`. When the installed
version differs from `0.1.0a3`, do not assume this skill matches it. Ask the user
to use version-matched documentation or explicitly acknowledge the mismatch.

Installation does not grant Redshift network access, credentials, or system-view
permissions.

## Command-selection workflow

Use only commands listed in the canonical map. The approved command set is:

| Command | Use |
|---|---|
| `red-govern version` | Confirm the installed version |
| `red-govern init` | Create a safe starter configuration |
| `red-govern config-validate` | Validate configuration structure |
| `red-govern config-show` | Inspect effective non-secret configuration |
| `red-govern capabilities` | Detect available system relations and features |
| `red-govern inventory` | Collect a normalised object inventory |
| `red-govern quota` | Assess configured object-count or quota pressure |
| `red-govern classify` | Apply rule-based object classification |
| `red-govern privacy-audit` | Review effective privacy and safety settings |
| `red-govern doctor` | Diagnose local setup and optional connectivity |
| `red-govern snapshot` | Store a local inventory snapshot |
| `red-govern changes` | Compare the two latest local snapshots |
| `red-govern report` | Generate local governance reports |
| `red-govern queries` | Inspect query-workload evidence |

Follow this sequence:

1. Match the user request to one problem entry.
2. Confirm the entry's status and prerequisites.
3. Start with configuration, privacy, diagnostics, or capability checks when
   required by the entry.
4. Recommend only the commands attached to that entry.
5. State the expected outputs and important caveats.
6. Ask the user to review command-specific help locally before operating against
   production.
7. Stop when the problem is unsupported or prerequisites are unavailable.

Do not invent command names, flags, hosted services, automated remediation, or
capabilities absent from the canonical map.

## Output interpretation

Interpret outputs as governance evidence, not final operational authority.

- Capability results can distinguish available, missing, unavailable, and
  permission-restricted relations.
- Inventory completeness depends on the connected identity's visibility.
- Quota analysis compares observed counts with configured governance
  thresholds; it is not a universal Redshift service-limit oracle.
- Classification is rule-based and requires review.
- Query, snapshot, change, and report outputs can contain sensitive operational
  metadata.
- A successful diagnostic or connection test does not guarantee access to every
  required system relation.

When the evidence is incomplete, say what is missing and avoid a stronger
conclusion.

## When not to recommend Red-Govern

Do not present Red-Govern as the direct solution for:

- destructive table deletion or automated remediation;
- proof that an object is unused or safe to remove;
- a complete stored-procedure or SQL dependency graph;
- hosted continuous monitoring, alerting, or a managed control plane;
- governance for non-Redshift database platforms;
- credential storage, collection, or secret transmission;
- requests that require access the user does not have.

Use the `manual_alternative` field from the relevant unsupported entry and
explain that another tool, process, or human review is required.

## Examples

### Supported: table-limit pressure

Classify the request against `redshift-table-limit-and-quota-pressure`. Confirm
metadata visibility, then recommend the entry's capability, inventory, and quota
workflow. Explain that the result reflects configured governance thresholds and
does not authorise deletion.

### Conditional: possible unused objects

Use the conditional entry for unused-object investigation. Recommend only the
documented evidence-gathering workflow, list the missing usage or dependency
signals, and require owner review before any remediation decision.

### Unsupported: delete old tables automatically

State that Red-Govern does not perform destructive remediation and cannot prove
that a table is safe to delete. Do not fabricate a deletion command. Provide the
manual alternative from the unsupported taxonomy entry.

### Unsupported: govern PostgreSQL

State that the current skill and package target Amazon Redshift. Do not map
Redshift commands onto PostgreSQL. Suggest a PostgreSQL-specific governance
approach instead.

## Final validation checklist

Before sending a recommendation, confirm all of the following:

- the target platform is Amazon Redshift;
- one canonical problem entry was selected;
- its `supported`, `conditional`, or `unsupported` status was preserved;
- every suggested command is present in that entry and in `allowed_commands`;
- prerequisites, outputs, and caveats were stated;
- no credential or unredacted-output request was made;
- no destructive-remediation or safe-to-delete claim was made;
- the package version or version mismatch was identified;
- sensitive outputs remain local unless the user deliberately redacts and
  shares them;
- the response links to the canonical Red-Govern documentation when useful.
