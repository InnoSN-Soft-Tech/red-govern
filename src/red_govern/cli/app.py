"""Command-line interface for Red-Govern."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from red_govern import __version__
from red_govern.analyzers import (
    QueryBreakdownRow,
    QueryPerformanceSeverity,
    QueryPerformanceThresholds,
    QuotaStatus,
    analyse_object_quota,
    analyse_query_breakdown,
    analyse_query_issues,
    analyse_query_performance,
    analyse_query_workload,
)
from red_govern.capabilities import (
    detect_capabilities,
    summarise_permissions,
)
from red_govern.classification import (
    classify_inventory,
    load_classification_rules,
)
from red_govern.collectors import (
    collect_object_inventory,
    collect_query_history,
    collect_query_performance,
    collect_running_queries,
)
from red_govern.config import (
    load_config,
    load_default_config,
    write_default_config,
)
from red_govern.connections import test_connection
from red_govern.exceptions import (
    AuthenticationError,
    CapabilityDetectionError,
    ClassificationError,
    ConfigurationError,
    QueryResolutionError,
    RedshiftConnectionError,
    RedshiftQueryError,
    ReportError,
)
from red_govern.history import (
    detect_inventory_changes,
    save_inventory_snapshot,
)
from red_govern.reports import (
    build_excel_workbook,
    build_json_report,
    write_excel_report,
    write_json_report,
)
from red_govern.security import audit_privacy

app = typer.Typer(
    name="red-govern",
    help=("Local-first governance and operational intelligence for Amazon Redshift."),
    no_args_is_help=True,
    add_completion=False,
)

report_app = typer.Typer(
    help="Generate local Red-Govern governance reports.",
    no_args_is_help=True,
)

app.add_typer(report_app, name="report")

queries_app = typer.Typer(
    help="Inspect Redshift query workload.",
    no_args_is_help=True,
)

app.add_typer(queries_app, name="queries")

console = Console()

DEFAULT_CONFIG_PATH = Path("red-govern.yml")


@app.callback()
def main() -> None:
    """Run Red-Govern commands."""


@app.command()
def version() -> None:
    """Display the installed Red-Govern version."""
    console.print(f"Red-Govern {__version__}")


@app.command()
def init(
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Path for the generated configuration file.",
        ),
    ] = DEFAULT_CONFIG_PATH,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Replace an existing configuration file.",
        ),
    ] = False,
) -> None:
    """Create a safe default Red-Govern configuration."""
    try:
        destination = write_default_config(output, overwrite=force)
    except ConfigurationError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Created configuration:[/green] {destination}")
    console.print(
        "[yellow]Add your Redshift connection details before running database checks.[/yellow]"
    )


@app.command("config-validate")
def config_validate(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Configuration file to validate.",
        ),
    ] = DEFAULT_CONFIG_PATH,
) -> None:
    """Validate a Red-Govern configuration file."""
    try:
        validated = load_config(config)
    except ConfigurationError as exc:
        console.print(f"[red]Invalid configuration:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Configuration is valid.[/green] Version: {validated.config_version}")


@app.command("config-show")
def config_show(
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Configuration file to display. Defaults to packaged settings.",
        ),
    ] = None,
) -> None:
    """Display effective configuration with no credential values."""
    try:
        loaded = load_config(config) if config else load_default_config()
    except ConfigurationError as exc:
        console.print(f"[red]Unable to load configuration:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    safe_data = loaded.model_dump(mode="json", by_alias=True)

    console.print(
        yaml.safe_dump(
            safe_data,
            sort_keys=False,
            default_flow_style=False,
        )
    )

@app.command()
def capabilities(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Configuration file used for Redshift capability detection.",
        ),
    ] = DEFAULT_CONFIG_PATH,
) -> None:
    """Detect available Redshift system views and features."""
    try:
        loaded = load_config(config)
        report = detect_capabilities(loaded.redshift)
    except (
        AuthenticationError,
        CapabilityDetectionError,
        ConfigurationError,
        RedshiftConnectionError,
    ) as exc:
        console.print(f"[red]Capability detection failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    summary = summarise_permissions(report)

    overview = Table(show_header=False, box=None)
    overview.add_column("Property", style="bold")
    overview.add_column("Value")
    overview.add_row("Deployment", report.deployment_type.value)
    overview.add_row("Server version", report.server_version)
    overview.add_row(
        "Accessible relations",
        str(summary.accessible_relations),
    )
    overview.add_row(
        "Permission-restricted",
        str(summary.inaccessible_relations),
    )
    overview.add_row("Missing relations", str(summary.missing_relations))

    console.print(
        Panel(
            overview,
            title="Red-Govern Capabilities",
        )
    )

    views_table = Table(
        "Relation",
        "Family",
        "Exists",
        "Accessible",
    )

    for view in report.views:
        views_table.add_row(
            view.relation,
            view.family.value,
            "Yes" if view.available else "No",
            "Yes" if view.accessible else "No",
        )

    console.print(views_table)

@app.command()
def inventory(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Configuration file used for inventory collection.",
        ),
    ] = DEFAULT_CONFIG_PATH,
) -> None:
    """Collect and display a normalised Redshift object inventory."""
    try:
        loaded = load_config(config)
        capability_report = detect_capabilities(loaded.redshift)
        result = collect_object_inventory(
            loaded.redshift,
            capability_report,
        )
    except (
        AuthenticationError,
        CapabilityDetectionError,
        ConfigurationError,
        QueryResolutionError,
        RedshiftConnectionError,
        RedshiftQueryError,
    ) as exc:
        console.print(f"[red]Inventory collection failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    summary = Table(show_header=False, box=None)
    summary.add_column("Property", style="bold")
    summary.add_column("Value")
    summary.add_row("Objects", str(result.total_objects))
    summary.add_row(
        "Query",
        result.resolution.query.query_id,
    )
    summary.add_row(
        "Source family",
        result.resolution.selected_family.value,
    )
    summary.add_row(
        "Fallback used",
        "Yes" if result.resolution.used_fallback else "No",
    )

    console.print(
        Panel(
            summary,
            title="Red-Govern Object Inventory",
        )
    )

    objects = Table(
        "Database",
        "Schema",
        "Object",
        "Type",
    )

    for record in result.records:
        objects.add_row(
            record.database_name,
            record.schema_name,
            record.object_name,
            record.object_type.value,
        )

    console.print(objects)

@app.command()
def quota(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Configuration file used for quota analysis.",
        ),
    ] = DEFAULT_CONFIG_PATH,
) -> None:
    """Analyse object inventory against the configured quota."""
    try:
        loaded = load_config(config)

        if not loaded.governance.object_quota.enabled:
            console.print(
                "[yellow]Object-quota analysis is disabled "
                "in the configuration.[/yellow]"
            )
            raise typer.Exit(code=0)

        capability_report = detect_capabilities(loaded.redshift)

        inventory_result = collect_object_inventory(
            loaded.redshift,
            capability_report,
        )

        analysis = analyse_object_quota(
            inventory_result,
            loaded.governance.object_quota,
        )
    except (
        AuthenticationError,
        CapabilityDetectionError,
        ConfigurationError,
        QueryResolutionError,
        RedshiftConnectionError,
        RedshiftQueryError,
    ) as exc:
        console.print(f"[red]Quota analysis failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    status_styles = {
        QuotaStatus.UNKNOWN: "yellow",
        QuotaStatus.HEALTHY: "green",
        QuotaStatus.WARNING: "yellow",
        QuotaStatus.CRITICAL: "red",
        QuotaStatus.EXCEEDED: "bold red",
    }

    status_style = status_styles[analysis.status]

    summary = Table(show_header=False, box=None)
    summary.add_column("Property", style="bold")
    summary.add_column("Value")

    summary.add_row(
        "Status",
        f"[{status_style}]{analysis.status.value}[/{status_style}]",
    )
    summary.add_row(
        "Current objects",
        str(analysis.current_objects),
    )

    if analysis.quota_known:
        summary.add_row(
            "Quota limit",
            str(analysis.quota_limit),
        )
        summary.add_row(
            "Remaining capacity",
            str(analysis.remaining_capacity),
        )
        summary.add_row(
            "Utilisation",
            f"{analysis.utilisation_percentage:.2f}%",
        )
    else:
        summary.add_row("Quota limit", "Not configured")
        summary.add_row("Remaining capacity", "Unknown")
        summary.add_row("Utilisation", "Unknown")

    console.print(
        Panel(
            summary,
            title="Red-Govern Object Quota",
        )
    )

    schema_table = Table(
        "Schema",
        "Objects",
        "% of inventory",
    )

    for item in analysis.by_schema:
        schema_table.add_row(
            item.name,
            str(item.count),
            f"{item.percentage_of_inventory:.2f}%",
        )

    console.print(schema_table)

    if not analysis.quota_known:
        console.print(
            "\n[yellow]Set governance.object_quota.limit_override "
            "after confirming the applicable quota for this "
            "Redshift environment.[/yellow]"
        )

@app.command()
def classify(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Configuration file used for object classification.",
        ),
    ] = DEFAULT_CONFIG_PATH,
) -> None:
    """Collect and classify Redshift objects."""
    try:
        loaded = load_config(config)

        if not loaded.classification.enabled:
            console.print(
                "[yellow]Classification is disabled "
                "in the configuration.[/yellow]"
            )
            raise typer.Exit(code=0)

        ruleset = load_classification_rules(
            loaded.classification.rules_file
        )

        capability_report = detect_capabilities(loaded.redshift)

        inventory_result = collect_object_inventory(
            loaded.redshift,
            capability_report,
        )

        result = classify_inventory(
            inventory_result,
            ruleset,
        )
    except (
        AuthenticationError,
        CapabilityDetectionError,
        ClassificationError,
        ConfigurationError,
        QueryResolutionError,
        RedshiftConnectionError,
        RedshiftQueryError,
    ) as exc:
        console.print(f"[red]Classification failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    summary = Table(show_header=False, box=None)
    summary.add_column("Property", style="bold")
    summary.add_column("Value")
    summary.add_row("Objects", str(result.total_objects))
    summary.add_row("Classified", str(result.classified_count))
    summary.add_row("Unclassified", str(result.unclassified_count))
    summary.add_row("Conflicts", str(result.conflict_count))

    console.print(
        Panel(
            summary,
            title="Red-Govern Classification",
        )
    )

    table = Table(
        "Database",
        "Schema",
        "Object",
        "Classifications",
        "Conflict",
    )

    for item in result.objects:
        labels = ", ".join(
            f"{dimension.dimension}={dimension.label}"
            for dimension in item.dimensions
            if dimension.label is not None
        )

        table.add_row(
            item.record.database_name,
            item.record.schema_name,
            item.record.object_name,
            labels or "Unclassified",
            "Yes" if item.has_conflict else "No",
        )

    console.print(table)

@report_app.command("json")
def report_json(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Configuration file used to generate the report.",
        ),
    ] = DEFAULT_CONFIG_PATH,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help=(
                "Output JSON path. Defaults to outputs.json.path "
                "from the configuration."
            ),
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Replace an existing report file.",
        ),
    ] = False,
) -> None:
    """Generate a local JSON governance report."""
    try:
        loaded = load_config(config)

        capability_report = detect_capabilities(
            loaded.redshift
        )

        inventory_result = collect_object_inventory(
            loaded.redshift,
            capability_report,
        )

        quota_analysis = analyse_object_quota(
            inventory_result,
            loaded.governance.object_quota,
        )

        classification_result = None

        if loaded.classification.enabled:
            ruleset = load_classification_rules(
                loaded.classification.rules_file
            )
            classification_result = classify_inventory(
                inventory_result,
                ruleset,
            )

        report = build_json_report(
            capabilities=capability_report,
            inventory=inventory_result,
            quota=quota_analysis,
            classification=classification_result,
        )

        destination = (
            output
            if output is not None
            else loaded.outputs.json_output.path
        )

        report_path = write_json_report(
            report,
            destination,
            overwrite=force,
        )
    except (
        AuthenticationError,
        CapabilityDetectionError,
        ClassificationError,
        ConfigurationError,
        QueryResolutionError,
        RedshiftConnectionError,
        RedshiftQueryError,
        ReportError,
    ) as exc:
        console.print(
            f"[red]JSON report generation failed:[/red] {exc}"
        )
        raise typer.Exit(code=1) from exc

    console.print(
        f"[green]JSON report created:[/green] {report_path}"
    )
    console.print(
        f"Objects: {inventory_result.total_objects}; "
        f"Quota status: {quota_analysis.status.value}"
    )

@app.command("privacy-audit")
def privacy_audit(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Configuration file to audit.",
        ),
    ] = DEFAULT_CONFIG_PATH,
) -> None:
    """Audit effective Red-Govern privacy and safety settings."""
    try:
        loaded = load_config(config)
        result = audit_privacy(loaded)
    except ConfigurationError as exc:
        console.print(f"[red]Privacy audit failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    summary = Table(show_header=False, box=None)
    summary.add_column("Property", style="bold")
    summary.add_column("Value")
    summary.add_row(
        "Overall result",
        "[green]Passed[/green]"
        if result.passed
        else "[red]Failed[/red]",
    )
    summary.add_row("Warnings", str(result.warning_count))
    summary.add_row("Critical failures", str(result.critical_count))

    console.print(
        Panel(
            summary,
            title="Red-Govern Privacy Audit",
        )
    )

    findings = Table(
        "Control",
        "Effective Value",
        "Severity",
        "Result",
        "Details",
    )

    for finding in result.findings:
        findings.add_row(
            finding.control,
            finding.effective_value,
            finding.severity.value,
            (
                "[green]Pass[/green]"
                if finding.passed
                else "[red]Fail[/red]"
            ),
            finding.message,
        )

    console.print(findings)

    if not result.passed:
        raise typer.Exit(code=2)


@report_app.command("excel")
def report_excel(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Configuration file used to generate the report.",
        ),
    ] = DEFAULT_CONFIG_PATH,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help=(
                "Output Excel path. Defaults to outputs.excel.path "
                "from the configuration."
            ),
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Replace an existing Excel report.",
        ),
    ] = False,
) -> None:
    """Generate a local Excel governance report."""
    try:
        loaded = load_config(config)

        capability_report = detect_capabilities(
            loaded.redshift
        )

        inventory_result = collect_object_inventory(
            loaded.redshift,
            capability_report,
        )

        quota_analysis = analyse_object_quota(
            inventory_result,
            loaded.governance.object_quota,
        )

        classification_result = None

        if loaded.classification.enabled:
            ruleset = load_classification_rules(
                loaded.classification.rules_file
            )

            classification_result = classify_inventory(
                inventory_result,
                ruleset,
            )

        workbook = build_excel_workbook(
            capabilities=capability_report,
            inventory=inventory_result,
            quota=quota_analysis,
            classification=classification_result,
        )

        destination = (
            output
            if output is not None
            else loaded.outputs.excel.path
        )

        report_path = write_excel_report(
            workbook,
            destination,
            overwrite=force,
        )
    except (
        AuthenticationError,
        CapabilityDetectionError,
        ClassificationError,
        ConfigurationError,
        QueryResolutionError,
        RedshiftConnectionError,
        RedshiftQueryError,
        ReportError,
    ) as exc:
        console.print(
            f"[red]Excel report generation failed:[/red] {exc}"
        )
        raise typer.Exit(code=1) from exc

    console.print(
        f"[green]Excel report created:[/green] {report_path}"
    )
    console.print(
        f"Objects: {inventory_result.total_objects}; "
        f"Quota status: {quota_analysis.status.value}"
    )


@queries_app.command("summary")
def queries_summary(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Configuration used for query-history collection.",
        ),
    ] = DEFAULT_CONFIG_PATH,
) -> None:
    """Display a summary of recent Redshift queries."""
    try:
        loaded = load_config(config)

        capability_report = detect_capabilities(
            loaded.redshift
        )

        history_result = collect_query_history(
            loaded.redshift,
            capability_report,
        )

        analysis = analyse_query_workload(
            history_result
        )
    except (
        AuthenticationError,
        CapabilityDetectionError,
        ConfigurationError,
        QueryResolutionError,
        RedshiftConnectionError,
        RedshiftQueryError,
    ) as exc:
        console.print(
            f"[red]Query summary failed:[/red] {exc}"
        )
        raise typer.Exit(code=1) from exc

    summary = Table(show_header=False, box=None)
    summary.add_column("Metric", style="bold")
    summary.add_column("Value")

    summary.add_row(
        "Total queries",
        str(analysis.total_queries),
    )
    summary.add_row(
        "Succeeded",
        str(analysis.succeeded_queries),
    )
    summary.add_row(
        "Failed",
        str(analysis.failed_queries),
    )
    summary.add_row(
        "Cancelled",
        str(analysis.cancelled_queries),
    )
    summary.add_row(
        "Running",
        str(analysis.running_queries),
    )
    summary.add_row(
        "Failure rate",
        f"{analysis.failure_rate:.2f}%",
    )
    summary.add_row(
        "Cancellation rate",
        f"{analysis.cancellation_rate:.2f}%",
    )
    summary.add_row(
        "Average elapsed",
        (
            f"{analysis.average_elapsed_ms:.2f} ms"
            if analysis.average_elapsed_ms is not None
            else "Unknown"
        ),
    )
    summary.add_row(
        "Maximum elapsed",
        (
            f"{analysis.maximum_elapsed_ms} ms"
            if analysis.maximum_elapsed_ms is not None
            else "Unknown"
        ),
    )
    summary.add_row(
        "Average queue time",
        (
            f"{analysis.average_queue_ms:.2f} ms"
            if analysis.average_queue_ms is not None
            else "Unknown"
        ),
    )

    console.print(
        Panel(
            summary,
            title="Red-Govern Query Summary",
        )
    )

@queries_app.command("running")
def queries_running(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Configuration used for active-query collection.",
        ),
    ] = DEFAULT_CONFIG_PATH,
) -> None:
    """Display currently active Redshift queries."""
    try:
        loaded = load_config(config)

        capability_report = detect_capabilities(
            loaded.redshift
        )

        result = collect_running_queries(
            loaded.redshift,
            capability_report,
        )
    except (
        AuthenticationError,
        CapabilityDetectionError,
        ConfigurationError,
        QueryResolutionError,
        RedshiftConnectionError,
        RedshiftQueryError,
    ) as exc:
        console.print(
            f"[red]Running-query collection failed:[/red] {exc}"
        )
        raise typer.Exit(code=1) from exc

    table = Table(
        "Query ID",
        "User",
        "Database",
        "Type",
        "Elapsed",
        "Queue",
        "Started",
    )

    for record in result.records:
        table.add_row(
            record.query_id,
            record.user_name or "Unknown",
            record.database_name or "Unknown",
            record.query_type or "Unknown",
            (
                f"{record.elapsed_ms:,} ms"
                if record.elapsed_ms is not None
                else "Unknown"
            ),
            (
                f"{record.queue_ms:,} ms"
                if record.queue_ms is not None
                else "Unknown"
            ),
            (
                record.started_at.isoformat()
                if record.started_at is not None
                else "Unknown"
            ),
        )

    console.print(
        Panel(
            f"Active queries: {result.total_queries}",
            title="Red-Govern Running Queries",
        )
    )
    console.print(table)

@queries_app.command("issues")
def queries_issues(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Configuration used for query-history collection.",
        ),
    ] = DEFAULT_CONFIG_PATH,
    slow_seconds: Annotated[
        int,
        typer.Option(
            "--slow-seconds",
            min=1,
            help="Duration after which a successful query is considered slow.",
        ),
    ] = 60,
) -> None:
    """Display failed, cancelled and slow Redshift queries."""
    try:
        loaded = load_config(config)

        capability_report = detect_capabilities(
            loaded.redshift
        )

        history_result = collect_query_history(
            loaded.redshift,
            capability_report,
        )

        analysis = analyse_query_issues(
            history_result,
            slow_threshold_ms=slow_seconds * 1000,
        )
    except (
        AuthenticationError,
        CapabilityDetectionError,
        ConfigurationError,
        QueryResolutionError,
        RedshiftConnectionError,
        RedshiftQueryError,
    ) as exc:
        console.print(
            f"[red]Query-issue analysis failed:[/red] {exc}"
        )
        raise typer.Exit(code=1) from exc

    summary = Table(show_header=False, box=None)
    summary.add_column("Metric", style="bold")
    summary.add_column("Value")
    summary.add_row(
        "Issues detected",
        str(analysis.total_issues),
    )
    summary.add_row(
        "Failed",
        str(analysis.failed_count),
    )
    summary.add_row(
        "Cancelled",
        str(analysis.cancelled_count),
    )
    summary.add_row(
        "Slow",
        str(analysis.slow_count),
    )
    summary.add_row(
        "Slow threshold",
        f"{slow_seconds} seconds",
    )

    console.print(
        Panel(
            summary,
            title="Red-Govern Query Issues",
        )
    )

    issues_table = Table(
        "Query ID",
        "Issue",
        "User",
        "Database",
        "Type",
        "Elapsed",
        "Queue",
        "Error",
    )

    for issue in analysis.issues:
        issues_table.add_row(
            issue.query_id,
            issue.kind.value,
            issue.user_name or "Unknown",
            issue.database_name or "Unknown",
            issue.query_type or "Unknown",
            (
                f"{issue.elapsed_ms:,} ms"
                if issue.elapsed_ms is not None
                else "Unknown"
            ),
            (
                f"{issue.queue_ms:,} ms"
                if issue.queue_ms is not None
                else "Unknown"
            ),
            issue.error_message or "None",
        )

    console.print(issues_table)

def _build_query_breakdown_table(
    dimension: str,
    rows: tuple[QueryBreakdownRow, ...],
) -> Table:
    """Build a Rich table for one workload dimension."""
    table = Table(
        dimension,
        "Total",
        "Succeeded",
        "Failed",
        "Cancelled",
        "Running",
        "Other",
        "Avg elapsed",
        "Avg queue",
        title=f"Workload by {dimension}",
    )

    for row in rows:
        table.add_row(
            row.name,
            str(row.total_queries),
            str(row.succeeded_queries),
            str(row.failed_queries),
            str(row.cancelled_queries),
            str(row.running_queries),
            str(row.other_queries),
            (
                f"{row.average_elapsed_ms:,.2f} ms"
                if row.average_elapsed_ms is not None
                else "Unknown"
            ),
            (
                f"{row.average_queue_ms:,.2f} ms"
                if row.average_queue_ms is not None
                else "Unknown"
            ),
        )

    return table

@queries_app.command("breakdown")
def queries_breakdown(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Configuration used for query-history collection.",
        ),
    ] = DEFAULT_CONFIG_PATH,
) -> None:
    """Display workload breakdowns by user, database, and query type."""
    try:
        loaded = load_config(config)

        capability_report = detect_capabilities(
            loaded.redshift
        )

        history_result = collect_query_history(
            loaded.redshift,
            capability_report,
        )

        analysis = analyse_query_breakdown(
            history_result
        )
    except (
        AuthenticationError,
        CapabilityDetectionError,
        ConfigurationError,
        QueryResolutionError,
        RedshiftConnectionError,
        RedshiftQueryError,
    ) as exc:
        console.print(
            f"[red]Query-breakdown analysis failed:[/red] {exc}"
        )
        raise typer.Exit(code=1) from exc

    summary = Table(
        show_header=False,
        box=None,
    )
    summary.add_column(
        "Metric",
        style="bold",
    )
    summary.add_column("Value")
    summary.add_row(
        "Total queries",
        str(analysis.total_queries),
    )
    summary.add_row(
        "Users",
        str(len(analysis.by_user)),
    )
    summary.add_row(
        "Databases",
        str(len(analysis.by_database)),
    )
    summary.add_row(
        "Query types",
        str(len(analysis.by_query_type)),
    )

    console.print(
        Panel(
            summary,
            title="Red-Govern Query Workload Breakdown",
        )
    )

    console.print(
        _build_query_breakdown_table(
            "User",
            analysis.by_user,
        )
    )
    console.print(
        _build_query_breakdown_table(
            "Database",
            analysis.by_database,
        )
    )
    console.print(
        _build_query_breakdown_table(
            "Query type",
            analysis.by_query_type,
        )
    )

@queries_app.command("performance")
def queries_performance(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help=(
                "Configuration used for query-performance "
                "collection."
            ),
        ),
    ] = DEFAULT_CONFIG_PATH,
    slow_seconds: Annotated[
        int,
        typer.Option(
            "--slow-seconds",
            min=1,
            help=(
                "Elapsed duration after which a query is "
                "considered slow."
            ),
        ),
    ] = 60,
    queue_seconds: Annotated[
        int,
        typer.Option(
            "--queue-seconds",
            min=0,
            help=(
                "Queue duration after which a query is "
                "considered delayed."
            ),
        ),
    ] = 10,
    cpu_percent: Annotated[
        float,
        typer.Option(
            "--cpu-percent",
            min=0.0,
            help="CPU-usage percentage considered excessive.",
        ),
    ] = 80.0,
    skew_ratio: Annotated[
        float,
        typer.Option(
            "--skew-ratio",
            min=1.0,
            help="Legacy CPU or I/O skew ratio considered high.",
        ),
    ] = 2.0,
    skew_percent: Annotated[
        float,
        typer.Option(
            "--skew-percent",
            min=0.01,
            max=100.0,
            help=(
                "SYS data or time skew percentage considered "
                "high."
            ),
        ),
    ] = 50.0,
    spill_blocks: Annotated[
        int,
        typer.Option(
            "--spill-blocks",
            min=0,
            help=(
                "Temporary disk blocks after which spilling "
                "is reported."
            ),
        ),
    ] = 1,
    alert_count: Annotated[
        int,
        typer.Option(
            "--alert-count",
            min=0,
            help=(
                "Redshift alert count after which a query is "
                "flagged."
            ),
        ),
    ] = 1,
) -> None:
    """Display query-performance issues for recent Redshift queries."""
    try:
        loaded = load_config(config)

        capability_report = detect_capabilities(
            loaded.redshift
        )

        result = collect_query_performance(
            loaded.redshift,
            capability_report,
        )

        thresholds = QueryPerformanceThresholds(
            slow_query_ms=slow_seconds * 1000,
            queue_wait_ms=queue_seconds * 1000,
            cpu_usage_percent=cpu_percent,
            skew_ratio=skew_ratio,
            spill_blocks=spill_blocks,
            data_time_skew_percent=skew_percent,
            alert_count=alert_count,
        )

        analysis = analyse_query_performance(
            result.records,
            thresholds=thresholds,
        )
    except (
        AuthenticationError,
        CapabilityDetectionError,
        ConfigurationError,
        QueryResolutionError,
        RedshiftConnectionError,
        RedshiftQueryError,
    ) as exc:
        console.print(
            "[red]Query-performance analysis failed:"
            f"[/red] {exc}"
        )
        raise typer.Exit(code=1) from exc

    warning_count = sum(
        issue.severity
        == QueryPerformanceSeverity.WARNING
        for issue in analysis.issues
    )
    critical_count = sum(
        issue.severity
        == QueryPerformanceSeverity.CRITICAL
        for issue in analysis.issues
    )

    summary = Table(
        show_header=False,
        box=None,
    )
    summary.add_column(
        "Metric",
        style="bold",
    )
    summary.add_column("Value")

    summary.add_row(
        "Queries analysed",
        str(len(result.records)),
    )
    summary.add_row(
        "Issues detected",
        str(len(analysis.issues)),
    )
    summary.add_row(
        "Warnings",
        str(warning_count),
    )
    summary.add_row(
        "Critical issues",
        str(critical_count),
    )
    summary.add_row(
        "Slow threshold",
        f"{slow_seconds} seconds",
    )
    summary.add_row(
        "Queue threshold",
        f"{queue_seconds} seconds",
    )
    summary.add_row(
        "CPU threshold",
        f"{cpu_percent:.2f}%",
    )
    summary.add_row(
        "CPU/I/O skew ratio",
        f"{skew_ratio:.2f}",
    )
    summary.add_row(
        "Data/time skew threshold",
        f"{skew_percent:.2f}%",
    )

    console.print(
        Panel(
            summary,
            title="Red-Govern Query Performance",
        )
    )

    issues_table = Table(
        "Query ID",
        "Severity",
        "Issue",
        "Metric",
        "Value",
        "Threshold",
        "Details",
    )

    for issue in analysis.issues:
        issues_table.add_row(
            issue.query_id,
            issue.severity.value,
            issue.issue_type.value,
            issue.metric_name,
            f"{issue.metric_value:,.2f}",
            f"{issue.threshold:,.2f}",
            issue.message,
        )

    console.print(issues_table)

@app.command()
def doctor(
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help=(
                "Configuration file. When omitted, only local package diagnostics are performed."
            ),
        ),
    ] = None,
) -> None:
    """Validate the local setup and optionally test Redshift connectivity."""
    table = Table(show_header=False, box=None)
    table.add_column("Check", style="bold")
    table.add_column("Status")

    table.add_row("Package", "Installed")
    table.add_row("Version", __version__)
    table.add_row("Local-first mode", "Enabled")
    table.add_row("Telemetry", "Disabled")
    table.add_row("Read-only mode", "Enabled")

    if config is None:
        table.add_row("Configuration", "Not supplied")
        table.add_row("Redshift connection", "Not tested")

        console.print(
            Panel(
                table,
                title="Red-Govern Doctor",
                subtitle="Local package diagnostic",
            )
        )

        console.print("\n[yellow]Provide --config to test Redshift connectivity.[/yellow]")
        return

    try:
        loaded = load_config(config)
        result = test_connection(loaded.redshift)
    except (
        AuthenticationError,
        ConfigurationError,
        RedshiftConnectionError,
        RedshiftQueryError,
    ) as exc:
        table.add_row("Configuration", str(config))
        table.add_row("Redshift connection", "Failed")

        console.print(
            Panel(
                table,
                title="Red-Govern Doctor",
                subtitle="Connection diagnostic",
            )
        )
        console.print(f"\n[red]Error:[/red] {exc}")

        raise typer.Exit(code=1) from exc

    table.add_row("Configuration", str(config))
    table.add_row("Redshift connection", "Successful")
    table.add_row("Database", result.database)
    table.add_row("User", result.user)
    table.add_row("Latency", f"{result.latency_ms:.2f} ms")

    console.print(
        Panel(
            table,
            title="Red-Govern Doctor",
            subtitle="Connection diagnostic",
        )
    )

@app.command()
def snapshot(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Configuration file used to collect and save a snapshot.",
        ),
    ] = DEFAULT_CONFIG_PATH,
) -> None:
    """Collect and persist a local object-inventory snapshot."""
    try:
        loaded = load_config(config)
        capability_report = detect_capabilities(loaded.redshift)

        inventory_result = collect_object_inventory(
            loaded.redshift,
            capability_report,
        )

        snapshot_result = save_inventory_snapshot(
            loaded.history.path,
            inventory_result,
        )
    except (
        AuthenticationError,
        CapabilityDetectionError,
        ConfigurationError,
        QueryResolutionError,
        RedshiftConnectionError,
        RedshiftQueryError,
        OSError,
        ValueError,
    ) as exc:
        console.print(f"[red]Snapshot failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(
        f"[green]Snapshot saved.[/green] "
        f"Run ID: {snapshot_result.run_id}; "
        f"Objects: {snapshot_result.total_objects}"
    )

@app.command()
def changes(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Configuration containing the local history path.",
        ),
    ] = DEFAULT_CONFIG_PATH,
) -> None:
    """Compare the two latest local inventory snapshots."""
    try:
        loaded = load_config(config)
        result = detect_inventory_changes(loaded.history.path)
    except (
        ConfigurationError,
        OSError,
        ValueError,
    ) as exc:
        console.print(f"[red]Change analysis failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    summary = Table(show_header=False, box=None)
    summary.add_column("Property", style="bold")
    summary.add_column("Value")
    summary.add_row("Current run", str(result.current_run_id))
    summary.add_row(
        "Previous run",
        (
            str(result.previous_run_id)
            if result.previous_run_id is not None
            else "None"
        ),
    )
    summary.add_row("Added objects", str(result.added_count))
    summary.add_row("Removed objects", str(result.removed_count))

    console.print(
        Panel(
            summary,
            title="Red-Govern Inventory Changes",
        )
    )

    added_table = Table(
        "Database",
        "Schema",
        "Added object",
        "Type",
    )

    for record in result.added:
        added_table.add_row(
            record.database_name,
            record.schema_name,
            record.object_name,
            record.object_type.value,
        )

    console.print(added_table)

    removed_table = Table(
        "Database",
        "Schema",
        "Removed object",
        "Type",
    )

    for record in result.removed:
        removed_table.add_row(
            record.database_name,
            record.schema_name,
            record.object_name,
            record.object_type.value,
        )

    console.print(removed_table)

if __name__ == "__main__":
    app()
