"""Built-in Red-Govern query definitions."""

from __future__ import annotations

from red_govern.capabilities import DeploymentType, ViewFamily
from red_govern.query_registry.registry import (
    QueryDefinition,
    QueryPurpose,
    QueryRegistry,
)
from red_govern.query_registry.validator import validate_read_only_query


def build_builtin_registry() -> QueryRegistry:
    """Build the packaged query registry."""
    registry = QueryRegistry()

    definitions = (
        QueryDefinition(
            query_id="object_inventory_svv_v1",
            purpose=QueryPurpose.OBJECT_INVENTORY,
            query_version="1.0.0",
            result_schema="object_inventory_v1",
            sql="""
SELECT
    table_database,
    table_schema,
    table_name,
    table_type
FROM pg_catalog.svv_tables
WHERE table_schema NOT IN (
    'pg_catalog',
    'information_schema'
)
ORDER BY
    table_database,
    table_schema,
    table_name
""".strip(),
            family=ViewFamily.SVV,
            deployment_types=(
                DeploymentType.PROVISIONED,
                DeploymentType.SERVERLESS,
            ),
            required_relations=("pg_catalog.svv_tables",),
            priority=200,
        ),
        QueryDefinition(
            query_id="object_inventory_information_schema_v1",
            purpose=QueryPurpose.OBJECT_INVENTORY,
            query_version="1.0.0",
            result_schema="object_inventory_v1",
            sql="""
SELECT
    table_catalog,
    table_schema,
    table_name,
    table_type
FROM information_schema.tables
WHERE table_schema NOT IN (
    'pg_catalog',
    'information_schema'
)
ORDER BY
    table_catalog,
    table_schema,
    table_name
""".strip(),
            family=ViewFamily.INFORMATION_SCHEMA,
            deployment_types=(
                DeploymentType.PROVISIONED,
                DeploymentType.SERVERLESS,
                DeploymentType.UNKNOWN,
            ),
            required_relations=("information_schema.tables",),
            priority=100,
        ),
        QueryDefinition(
            query_id="query_history_sys_v1",
            purpose=QueryPurpose.QUERY_HISTORY,
            query_version="1.0.0",
            result_schema="query_history_v1",
            sql="""
SELECT
    query_id,
    username AS user_name,
    database_name,
    status,
    query_type,
    start_time,
    end_time,
    CAST(elapsed_time / 1000 AS BIGINT) AS elapsed_ms,
    CAST(queue_time / 1000 AS BIGINT) AS queue_ms,
    error_message
FROM pg_catalog.sys_query_history
ORDER BY start_time DESC
LIMIT 1000
""".strip(),
            family=ViewFamily.SYS,
            deployment_types=(
                DeploymentType.PROVISIONED,
                DeploymentType.SERVERLESS,
            ),
            required_relations=("pg_catalog.sys_query_history",),
            priority=300,
        ),
        QueryDefinition(
            query_id="running_queries_sys_v1",
            purpose=QueryPurpose.RUNNING_QUERIES,
            query_version="1.0.0",
            result_schema="query_history_v1",
            sql="""
SELECT
    query_id,
    username AS user_name,
    database_name,
    status,
    query_type,
    start_time,
    end_time,
    CAST(elapsed_time / 1000 AS BIGINT) AS elapsed_ms,
    CAST(queue_time / 1000 AS BIGINT) AS queue_ms,
    error_message
FROM pg_catalog.sys_query_history
WHERE status IN (
    'planning',
    'queued',
    'running',
    'returning'
)
ORDER BY start_time ASC
LIMIT 1000
""".strip(),
            family=ViewFamily.SYS,
            deployment_types=(
                DeploymentType.PROVISIONED,
                DeploymentType.SERVERLESS,
            ),
            required_relations=("pg_catalog.sys_query_history",),
            priority=300,
        ),
        QueryDefinition(
            query_id="running_queries_stv_v1",
            purpose=QueryPurpose.RUNNING_QUERIES,
            query_version="1.0.0",
            result_schema="query_history_v1",
            sql="""
SELECT
    CAST(pid AS VARCHAR) AS query_id,
    user_name,
    db_name AS database_name,
    status,
    NULL AS query_type,
    starttime AS start_time,
    NULL AS end_time,
    CAST(duration / 1000 AS BIGINT) AS elapsed_ms,
    NULL AS queue_ms,
    NULL AS error_message
FROM pg_catalog.stv_recents
WHERE status <> 'Done'
ORDER BY starttime ASC
LIMIT 1000
""".strip(),
            family=ViewFamily.STV,
            deployment_types=(DeploymentType.PROVISIONED,),
            required_relations=("pg_catalog.stv_recents",),
            priority=100,
        ),
        QueryDefinition(
            query_id="query_history_stl_v1",
            purpose=QueryPurpose.QUERY_HISTORY,
            query_version="1.0.0",
            result_schema="query_history_v1",
            sql="""
SELECT
    query AS query_id,
    NULL AS user_name,
    database AS database_name,
    CASE
        WHEN aborted = 1 THEN 'cancelled'
        ELSE 'succeeded'
    END AS status,
    NULL AS query_type,
    starttime AS start_time,
    endtime AS end_time,
    DATEDIFF(milliseconds, starttime, endtime) AS elapsed_ms,
    NULL AS queue_ms,
    NULL AS error_message
FROM pg_catalog.stl_query
ORDER BY starttime DESC
LIMIT 1000
""".strip(),
            family=ViewFamily.STL,
            deployment_types=(DeploymentType.PROVISIONED,),
            required_relations=("pg_catalog.stl_query",),
            priority=100,
        ),
        QueryDefinition(
            query_id="query_performance_sys_v1",
            purpose=QueryPurpose.QUERY_PERFORMANCE,
            query_version="1.0.0",
            result_schema="query_performance_v1",
            sql="""
SELECT
    history.query_id,
    history.user_id,
    TRIM(history.username) AS user_name,
    TRIM(history.database_name) AS database_name,
    TRIM(history.status) AS status,
    TRIM(history.query_type) AS query_type,
    history.start_time,
    history.end_time,
    CAST(history.elapsed_time / 1000 AS BIGINT) AS elapsed_ms,
    CAST(history.queue_time / 1000 AS BIGINT) AS queue_ms,
    CAST(history.execution_time / 1000 AS BIGINT) AS execution_ms,
    CAST(NULL AS BIGINT) AS cpu_ms,
    CAST(NULL AS DECIMAL(38, 2)) AS cpu_usage_percent,
    COALESCE(detail.blocks_read, 0) AS blocks_read,
    COALESCE(detail.blocks_write, 0) AS blocks_write,
    COALESCE(detail.temp_blocks_to_disk, 0) AS temp_blocks_to_disk,
    COALESCE(detail.input_rows, 0) AS input_rows,
    COALESCE(detail.output_rows, 0) AS output_rows,
    COALESCE(detail.input_bytes, 0) AS input_bytes,
    COALESCE(detail.output_bytes, 0) AS output_bytes,
    history.returned_rows,
    history.returned_bytes,
    CAST(NULL AS DECIMAL(38, 2)) AS cpu_skew,
    CAST(NULL AS DECIMAL(38, 2)) AS io_skew,
    detail.data_skewness,
    detail.time_skewness,
    COALESCE(detail.alert_count, 0) AS alert_count
FROM pg_catalog.sys_query_history AS history
LEFT JOIN (
    SELECT
        query_id,
        SUM(COALESCE(blocks_read, 0)) AS blocks_read,
        SUM(COALESCE(blocks_write, 0)) AS blocks_write,
        SUM(
            COALESCE(spilled_block_local_disk, 0)
            + COALESCE(spilled_block_remote_disk, 0)
        ) AS temp_blocks_to_disk,
        SUM(COALESCE(input_rows, 0)) AS input_rows,
        SUM(COALESCE(output_rows, 0)) AS output_rows,
        SUM(COALESCE(input_bytes, 0)) AS input_bytes,
        SUM(COALESCE(output_bytes, 0)) AS output_bytes,
        MAX(data_skewness) AS data_skewness,
        MAX(time_skewness) AS time_skewness,
        SUM(
            CASE
                WHEN alert IS NOT NULL
                    AND TRIM(alert) <> ''
                THEN 1
                ELSE 0
            END
        ) AS alert_count
    FROM pg_catalog.sys_query_detail
    WHERE LOWER(TRIM(metrics_level)) = 'step'
    GROUP BY query_id
) AS detail
    ON history.query_id = detail.query_id
WHERE history.status IN (
    'success',
    'failed',
    'canceled'
)
ORDER BY history.start_time DESC
LIMIT 1000
""".strip(),
            family=ViewFamily.SYS,
            deployment_types=(
                DeploymentType.PROVISIONED,
                DeploymentType.SERVERLESS,
            ),
            required_relations=(
                "pg_catalog.sys_query_history",
                "pg_catalog.sys_query_detail",
            ),
            priority=300,
        ),
        QueryDefinition(
            query_id="query_performance_svl_v1",
            purpose=QueryPurpose.QUERY_PERFORMANCE,
            query_version="1.0.0",
            result_schema="query_performance_v1",
            sql="""
SELECT
    CAST(query AS BIGINT) AS query_id,
    userid AS user_id,
    CAST(NULL AS VARCHAR(128)) AS user_name,
    CAST(NULL AS VARCHAR(128)) AS database_name,
    CAST(NULL AS VARCHAR(16)) AS status,
    CAST(NULL AS VARCHAR(32)) AS query_type,
    CAST(NULL AS TIMESTAMP) AS start_time,
    CAST(NULL AS TIMESTAMP) AS end_time,
    CAST(
        (query_execution_time + query_queue_time) * 1000
        AS BIGINT
    ) AS elapsed_ms,
    CAST(query_queue_time * 1000 AS BIGINT) AS queue_ms,
    CAST(query_execution_time * 1000 AS BIGINT) AS execution_ms,
    CAST(query_cpu_time * 1000 AS BIGINT) AS cpu_ms,
    query_cpu_usage_percent AS cpu_usage_percent,
    query_blocks_read AS blocks_read,
    CAST(NULL AS BIGINT) AS blocks_write,
    query_temp_blocks_to_disk AS temp_blocks_to_disk,
    scan_row_count AS input_rows,
    return_row_count AS output_rows,
    CAST(NULL AS BIGINT) AS input_bytes,
    CAST(NULL AS BIGINT) AS output_bytes,
    return_row_count AS returned_rows,
    CAST(NULL AS BIGINT) AS returned_bytes,
    cpu_skew,
    io_skew,
    CAST(NULL AS INTEGER) AS data_skewness,
    CAST(NULL AS INTEGER) AS time_skewness,
    CAST(NULL AS BIGINT) AS alert_count
FROM pg_catalog.svl_query_metrics_summary
ORDER BY query DESC
LIMIT 1000
""".strip(),
            family=ViewFamily.SVL,
            deployment_types=(DeploymentType.PROVISIONED,),
            required_relations=(
                "pg_catalog.svl_query_metrics_summary",
            ),
            priority=100,
        ),
    )

    for definition in definitions:
        validate_read_only_query(definition)
        registry.register(definition)

    return registry
