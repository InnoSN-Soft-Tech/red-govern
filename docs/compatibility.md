# Redshift compatibility

Red-Govern supports both provisioned Amazon Redshift and Redshift Serverless,
but the system relations available to a command can differ by deployment type,
service behaviour, permissions, and account configuration.

## Automatic compatibility mode

The default compatibility settings prefer modern `SYS` views and allow
supported legacy fallbacks:

```yaml
redshift:
  compatibility:
    mode: auto
    deployment_type: auto
    version_override: null
    prefer_sys_views: true
    allow_legacy_fallbacks: true
```

Use automatic mode unless a controlled compatibility test requires an explicit
override.

## Capability detection

Run capability detection before interpreting a missing result as an empty
dataset:

```bash
red-govern capabilities
```

A relation can be:

- available and readable;
- unavailable for the current deployment;
- present but restricted by permissions;
- unsupported by the selected compatibility path.

Red-Govern uses harmless relation probes and separates missing relations from
restricted access where the database response allows that distinction.

## Serverless and provisioned behaviour

Serverless environments should not be evaluated with provisioned-only system
relations. Provisioned environments may expose legacy relations that are not
appropriate for Serverless. Red-Govern filters compatibility paths according to
the detected or configured deployment type.

## Operational guidance

- run `red-govern doctor` before a broad assessment;
- keep `deployment_type: auto` unless detection is unreliable;
- document any explicit compatibility override;
- use command-specific help for version-dependent options;
- treat partial capability access as a permissions or compatibility finding,
  not automatically as a product defect.

Review [permissions](permissions.md) and [limitations](limitations.md) when a
capability is unavailable.
