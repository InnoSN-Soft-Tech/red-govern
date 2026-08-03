## Problem

Describe the focused problem this pull request addresses.

## Summary

Explain the implementation and why this approach was selected.

## Testing

List the checks performed and their results.

```text
python -m compileall -q src/red_govern
python -m ruff check src tests
python -m mypy src
python -m pytest -q
```

Include package-build validation when packaging or published metadata is affected.

## Compatibility

Describe relevant Python, Redshift Serverless, provisioned Redshift, system-view,
permission, and operating-system considerations.

## Security and privacy

Describe credential, sensitive-data, permission, logging, report, snapshot, and
local-file implications. Confirm that examples and diagnostics are synthetic or
fully sanitised.

## Documentation

Describe documentation changes or explain why none are required.

## Checklist

- [ ] This pull request contains one coherent change.
- [ ] The branch is based on the latest `main`.
- [ ] Compilation, Ruff, MyPy, and tests pass.
- [ ] Package validation passes when packaging is affected.
- [ ] New behaviour has appropriate test coverage.
- [ ] Documentation is updated where required.
- [ ] No credentials, private endpoints, account identifiers, confidential
      Redshift metadata, production query text, or personal data are included.
- [ ] Generated build artefacts are not committed.
- [ ] Redshift deployment and permission assumptions are documented.
- [ ] Source-code contribution approval and applicable contributor terms have
      been confirmed with InnoSN Soft Tech where required.

By opening this pull request, the contributor acknowledges the contribution and
licensing requirements in `CONTRIBUTING.md`.
