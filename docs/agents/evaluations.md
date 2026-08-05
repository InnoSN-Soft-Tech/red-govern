# Agent contract evaluations and distribution

## Evaluation suite

The tracked fixture suite contains 28 deterministic cases:

- 21 problem-routing cases, one for every canonical taxonomy entry;
- seven boundary cases covering destructive remediation, safe-to-delete claims,
  credential sharing, unredacted output, non-Redshift platforms, hosted
  monitoring, and version mismatch.

Run it with:

```bash
python scripts/evaluate_agent_skill.py
```

The evaluator checks fixture integrity against the canonical problem map. It
does not invoke or score a live language model, so passing it is evidence of
contract consistency rather than proof of model behaviour.

## Distribution reproducibility

The archive is created with sorted entries, fixed timestamps, fixed file modes,
and stored compression. Rebuild or validate it with:

```bash
python scripts/build_agent_skill_distribution.py --write
python scripts/build_agent_skill_distribution.py --check
```

The tracked archive must reproduce byte-for-byte on Python 3.10–3.13.

## Legal attribution

The archive includes `LICENSE.md`, `COMMERCIAL_LICENSE.md`, `NOTICE`, and
`TRADEMARKS.md`. Redistribution must preserve those files and the internal
manifest.
