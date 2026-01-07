"""
Advanced Data Analytics MCP Server
Provides tools for statistical analysis, data aggregations, time series analysis,
anomaly detection, and data profiling.

This MCP server works with the MSSQL MCP server to provide advanced analytics
capabilities on SQL Server data.
"""

# Configure logging to stderr BEFORE any other imports
# JSON-RPC only on stdout - logging MUST go to stderr
import logging
import sys

logging.basicConfig(
    level=logging.WARNING,
    format="%(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
    force=True,
)

import asyncio
import json
import math
import os
from collections import defaultdict
from contextlib import contextmanager
from typing import Any

import pyodbc
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Suppress noisy loggers
logging.getLogger("mcp").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Create the MCP server
server = Server("data-analytics")


def get_connection_string(database: str | None = None) -> str:
    """Build pyodbc connection string from environment variables."""
    # Support connecting to either sample or backend database
    if database == "sample" or database == "ResearchAnalytics":
        server_name = os.environ.get("SQL_SERVER_HOST", "localhost")
        port = os.environ.get("SQL_SERVER_PORT", "1433")
        db_name = os.environ.get("SQL_DATABASE_NAME", "ResearchAnalytics")
        username = os.environ.get("SQL_USERNAME", "sa")
        password = os.environ.get("SQL_PASSWORD", "")
        trust_cert = os.environ.get("SQL_TRUST_SERVER_CERTIFICATE", "true").lower() == "true"
    else:
        # Default to backend database
        server_name = os.environ.get("BACKEND_DB_HOST", "localhost")
        port = os.environ.get("BACKEND_DB_PORT", "1434")
        db_name = database or os.environ.get("BACKEND_DB_NAME", "LLM_BackEnd")
        username = os.environ.get("BACKEND_DB_USERNAME", os.environ.get("SQL_USERNAME", "sa"))
        password = os.environ.get("BACKEND_DB_PASSWORD", os.environ.get("SQL_PASSWORD", ""))
        trust_cert = os.environ.get("BACKEND_DB_TRUST_CERT", "true").lower() == "true"

    server_with_port = f"{server_name},{port}" if port else server_name

    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={server_with_port};"
        f"DATABASE={db_name};"
        f"UID={username};"
        f"PWD={password};"
    )

    if trust_cert:
        conn_str += "TrustServerCertificate=yes;"

    return conn_str


@contextmanager
def get_connection(database: str | None = None):
    """Context manager for database connections."""
    conn = pyodbc.connect(get_connection_string(database))
    try:
        yield conn
    finally:
        conn.close()


def row_to_dict(cursor, row) -> dict:
    """Convert a pyodbc row to a dictionary."""
    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row, strict=False))


# =============================================================================
# Tool Definitions
# =============================================================================

TOOLS = [
    # Statistical Analysis Tools
    Tool(
        name="descriptive_statistics",
        description="Calculate descriptive statistics (mean, median, mode, std dev, variance, min, max, quartiles) for numeric columns in a table or query result",
        inputSchema={
            "type": "object",
            "properties": {
                "table_name": {"type": "string", "description": "Table name (schema.table format)"},
                "columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Numeric columns to analyze (all if not specified)",
                },
                "where_clause": {"type": "string", "description": "Optional WHERE clause filter"},
                "database": {"type": "string", "description": "Database: 'sample' or 'backend' (default)"},
            },
            "required": ["table_name"],
        },
    ),
    Tool(
        name="correlation_analysis",
        description="Calculate correlation matrix between numeric columns to identify relationships",
        inputSchema={
            "type": "object",
            "properties": {
                "table_name": {"type": "string", "description": "Table name"},
                "columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Numeric columns to correlate (2+ required)",
                },
                "method": {
                    "type": "string",
                    "enum": ["pearson", "spearman"],
                    "description": "Correlation method",
                    "default": "pearson",
                },
                "database": {"type": "string", "description": "Database to connect to"},
            },
            "required": ["table_name", "columns"],
        },
    ),
    Tool(
        name="percentile_analysis",
        description="Calculate percentile values for a numeric column",
        inputSchema={
            "type": "object",
            "properties": {
                "table_name": {"type": "string", "description": "Table name"},
                "column": {"type": "string", "description": "Numeric column to analyze"},
                "percentiles": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Percentiles to calculate (e.g., [10, 25, 50, 75, 90, 95, 99])",
                    "default": [10, 25, 50, 75, 90, 95, 99],
                },
                "database": {"type": "string", "description": "Database to connect to"},
            },
            "required": ["table_name", "column"],
        },
    ),
    # Data Aggregation Tools
    Tool(
        name="group_aggregation",
        description="Perform GROUP BY aggregations with multiple aggregate functions",
        inputSchema={
            "type": "object",
            "properties": {
                "table_name": {"type": "string", "description": "Table name"},
                "group_by": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Columns to group by",
                },
                "aggregations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "column": {"type": "string"},
                            "function": {
                                "type": "string",
                                "enum": ["COUNT", "SUM", "AVG", "MIN", "MAX", "STDEV", "VAR"],
                            },
                            "alias": {"type": "string"},
                        },
                    },
                    "description": "Aggregations to perform",
                },
                "having": {"type": "string", "description": "HAVING clause filter"},
                "order_by": {"type": "string", "description": "ORDER BY clause"},
                "limit": {"type": "integer", "description": "Limit results", "default": 100},
                "database": {"type": "string", "description": "Database to connect to"},
            },
            "required": ["table_name", "group_by", "aggregations"],
        },
    ),
    Tool(
        name="pivot_analysis",
        description="Create a pivot table summarization",
        inputSchema={
            "type": "object",
            "properties": {
                "table_name": {"type": "string", "description": "Table name"},
                "row_column": {"type": "string", "description": "Column for rows"},
                "pivot_column": {"type": "string", "description": "Column to pivot (creates columns)"},
                "value_column": {"type": "string", "description": "Column with values to aggregate"},
                "aggregate_function": {
                    "type": "string",
                    "enum": ["SUM", "AVG", "COUNT", "MIN", "MAX"],
                    "default": "SUM",
                },
                "database": {"type": "string", "description": "Database to connect to"},
            },
            "required": ["table_name", "row_column", "pivot_column", "value_column"],
        },
    ),
    # Time Series Analysis Tools
    Tool(
        name="time_series_analysis",
        description="Analyze time series data for trends, patterns, and seasonality",
        inputSchema={
            "type": "object",
            "properties": {
                "table_name": {"type": "string", "description": "Table name"},
                "date_column": {"type": "string", "description": "Date/datetime column"},
                "value_column": {"type": "string", "description": "Numeric value column"},
                "granularity": {
                    "type": "string",
                    "enum": ["hour", "day", "week", "month", "quarter", "year"],
                    "default": "day",
                },
                "include_moving_average": {
                    "type": "boolean",
                    "description": "Include moving average",
                    "default": True,
                },
                "moving_average_window": {"type": "integer", "description": "Window size", "default": 7},
                "database": {"type": "string", "description": "Database to connect to"},
            },
            "required": ["table_name", "date_column", "value_column"],
        },
    ),
    Tool(
        name="trend_detection",
        description="Detect trends and calculate growth rates in time series data",
        inputSchema={
            "type": "object",
            "properties": {
                "table_name": {"type": "string", "description": "Table name"},
                "date_column": {"type": "string", "description": "Date column"},
                "value_column": {"type": "string", "description": "Value column"},
                "comparison_periods": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Periods to compare (e.g., ['day', 'week', 'month', 'year'])",
                    "default": ["week", "month"],
                },
                "database": {"type": "string", "description": "Database to connect to"},
            },
            "required": ["table_name", "date_column", "value_column"],
        },
    ),
    # Data Profiling Tools
    Tool(
        name="profile_table",
        description="Generate a comprehensive data profile for a table including column types, nulls, cardinality, and sample values",
        inputSchema={
            "type": "object",
            "properties": {
                "table_name": {"type": "string", "description": "Table name to profile"},
                "sample_size": {"type": "integer", "description": "Number of sample values", "default": 5},
                "database": {"type": "string", "description": "Database to connect to"},
            },
            "required": ["table_name"],
        },
    ),
    Tool(
        name="column_distribution",
        description="Analyze value distribution for a column (frequency counts, histograms)",
        inputSchema={
            "type": "object",
            "properties": {
                "table_name": {"type": "string", "description": "Table name"},
                "column": {"type": "string", "description": "Column to analyze"},
                "bins": {"type": "integer", "description": "Number of histogram bins (for numeric)", "default": 10},
                "top_n": {"type": "integer", "description": "Top N values (for categorical)", "default": 20},
                "database": {"type": "string", "description": "Database to connect to"},
            },
            "required": ["table_name", "column"],
        },
    ),
    Tool(
        name="data_quality_check",
        description="Check data quality issues: nulls, duplicates, outliers, patterns",
        inputSchema={
            "type": "object",
            "properties": {
                "table_name": {"type": "string", "description": "Table name"},
                "columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Columns to check (all if not specified)",
                },
                "check_duplicates": {"type": "boolean", "description": "Check for duplicates", "default": True},
                "check_outliers": {"type": "boolean", "description": "Check for outliers (IQR)", "default": True},
                "outlier_threshold": {"type": "number", "description": "IQR multiplier", "default": 1.5},
                "database": {"type": "string", "description": "Database to connect to"},
            },
            "required": ["table_name"],
        },
    ),
    # Anomaly Detection Tools
    Tool(
        name="detect_outliers",
        description="Detect outliers in numeric columns using IQR or Z-score method",
        inputSchema={
            "type": "object",
            "properties": {
                "table_name": {"type": "string", "description": "Table name"},
                "column": {"type": "string", "description": "Numeric column to analyze"},
                "method": {
                    "type": "string",
                    "enum": ["iqr", "zscore"],
                    "default": "iqr",
                },
                "threshold": {
                    "type": "number",
                    "description": "IQR multiplier (1.5) or Z-score threshold (3)",
                    "default": 1.5,
                },
                "return_data": {"type": "boolean", "description": "Return outlier rows", "default": True},
                "limit": {"type": "integer", "description": "Max outliers to return", "default": 100},
                "database": {"type": "string", "description": "Database to connect to"},
            },
            "required": ["table_name", "column"],
        },
    ),
    Tool(
        name="detect_anomalies_timeseries",
        description="Detect anomalies in time series data using rolling statistics",
        inputSchema={
            "type": "object",
            "properties": {
                "table_name": {"type": "string", "description": "Table name"},
                "date_column": {"type": "string", "description": "Date column"},
                "value_column": {"type": "string", "description": "Value column"},
                "window_size": {"type": "integer", "description": "Rolling window size", "default": 7},
                "std_threshold": {
                    "type": "number",
                    "description": "Standard deviations for anomaly",
                    "default": 2.0,
                },
                "database": {"type": "string", "description": "Database to connect to"},
            },
            "required": ["table_name", "date_column", "value_column"],
        },
    ),
    # Comparison & Segmentation Tools
    Tool(
        name="segment_analysis",
        description="Analyze data by segments with comparison metrics",
        inputSchema={
            "type": "object",
            "properties": {
                "table_name": {"type": "string", "description": "Table name"},
                "segment_column": {"type": "string", "description": "Column to segment by"},
                "metric_columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Numeric columns to analyze per segment",
                },
                "include_comparison": {
                    "type": "boolean",
                    "description": "Compare segments to overall",
                    "default": True,
                },
                "database": {"type": "string", "description": "Database to connect to"},
            },
            "required": ["table_name", "segment_column", "metric_columns"],
        },
    ),
    Tool(
        name="cohort_analysis",
        description="Perform cohort analysis based on a date column",
        inputSchema={
            "type": "object",
            "properties": {
                "table_name": {"type": "string", "description": "Table name"},
                "cohort_date_column": {"type": "string", "description": "Date column for cohort grouping"},
                "event_date_column": {"type": "string", "description": "Date column for events"},
                "value_column": {"type": "string", "description": "Value to aggregate"},
                "aggregate_function": {
                    "type": "string",
                    "enum": ["COUNT", "SUM", "AVG"],
                    "default": "COUNT",
                },
                "cohort_granularity": {
                    "type": "string",
                    "enum": ["day", "week", "month", "year"],
                    "default": "month",
                },
                "database": {"type": "string", "description": "Database to connect to"},
            },
            "required": ["table_name", "cohort_date_column", "event_date_column"],
        },
    ),
    # Custom Analytics Query
    Tool(
        name="run_analytics_query",
        description="Execute a custom analytics SQL query with safety checks",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "SQL query to execute (SELECT only)"},
                "database": {"type": "string", "description": "Database to connect to"},
                "limit": {"type": "integer", "description": "Max rows to return", "default": 1000},
            },
            "required": ["query"],
        },
    ),
]


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available data analytics tools."""
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute a data analytics tool."""
    try:
        result = await execute_tool(name, arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute the specified tool with arguments."""
    database = arguments.get("database")

    # Statistical Analysis
    if name == "descriptive_statistics":
        return await descriptive_statistics(
            table_name=arguments["table_name"],
            columns=arguments.get("columns"),
            where_clause=arguments.get("where_clause"),
            database=database,
        )

    elif name == "correlation_analysis":
        return await correlation_analysis(
            table_name=arguments["table_name"],
            columns=arguments["columns"],
            method=arguments.get("method", "pearson"),
            database=database,
        )

    elif name == "percentile_analysis":
        return await percentile_analysis(
            table_name=arguments["table_name"],
            column=arguments["column"],
            percentiles=arguments.get("percentiles", [10, 25, 50, 75, 90, 95, 99]),
            database=database,
        )

    # Data Aggregation
    elif name == "group_aggregation":
        return await group_aggregation(
            table_name=arguments["table_name"],
            group_by=arguments["group_by"],
            aggregations=arguments["aggregations"],
            having=arguments.get("having"),
            order_by=arguments.get("order_by"),
            limit=arguments.get("limit", 100),
            database=database,
        )

    elif name == "pivot_analysis":
        return await pivot_analysis(
            table_name=arguments["table_name"],
            row_column=arguments["row_column"],
            pivot_column=arguments["pivot_column"],
            value_column=arguments["value_column"],
            aggregate_function=arguments.get("aggregate_function", "SUM"),
            database=database,
        )

    # Time Series Analysis
    elif name == "time_series_analysis":
        return await time_series_analysis(
            table_name=arguments["table_name"],
            date_column=arguments["date_column"],
            value_column=arguments["value_column"],
            granularity=arguments.get("granularity", "day"),
            include_moving_average=arguments.get("include_moving_average", True),
            moving_average_window=arguments.get("moving_average_window", 7),
            database=database,
        )

    elif name == "trend_detection":
        return await trend_detection(
            table_name=arguments["table_name"],
            date_column=arguments["date_column"],
            value_column=arguments["value_column"],
            comparison_periods=arguments.get("comparison_periods", ["week", "month"]),
            database=database,
        )

    # Data Profiling
    elif name == "profile_table":
        return await profile_table(
            table_name=arguments["table_name"],
            sample_size=arguments.get("sample_size", 5),
            database=database,
        )

    elif name == "column_distribution":
        return await column_distribution(
            table_name=arguments["table_name"],
            column=arguments["column"],
            bins=arguments.get("bins", 10),
            top_n=arguments.get("top_n", 20),
            database=database,
        )

    elif name == "data_quality_check":
        return await data_quality_check(
            table_name=arguments["table_name"],
            columns=arguments.get("columns"),
            check_duplicates=arguments.get("check_duplicates", True),
            check_outliers=arguments.get("check_outliers", True),
            outlier_threshold=arguments.get("outlier_threshold", 1.5),
            database=database,
        )

    # Anomaly Detection
    elif name == "detect_outliers":
        return await detect_outliers(
            table_name=arguments["table_name"],
            column=arguments["column"],
            method=arguments.get("method", "iqr"),
            threshold=arguments.get("threshold", 1.5),
            return_data=arguments.get("return_data", True),
            limit=arguments.get("limit", 100),
            database=database,
        )

    elif name == "detect_anomalies_timeseries":
        return await detect_anomalies_timeseries(
            table_name=arguments["table_name"],
            date_column=arguments["date_column"],
            value_column=arguments["value_column"],
            window_size=arguments.get("window_size", 7),
            std_threshold=arguments.get("std_threshold", 2.0),
            database=database,
        )

    # Comparison & Segmentation
    elif name == "segment_analysis":
        return await segment_analysis(
            table_name=arguments["table_name"],
            segment_column=arguments["segment_column"],
            metric_columns=arguments["metric_columns"],
            include_comparison=arguments.get("include_comparison", True),
            database=database,
        )

    elif name == "cohort_analysis":
        return await cohort_analysis(
            table_name=arguments["table_name"],
            cohort_date_column=arguments["cohort_date_column"],
            event_date_column=arguments["event_date_column"],
            value_column=arguments.get("value_column"),
            aggregate_function=arguments.get("aggregate_function", "COUNT"),
            cohort_granularity=arguments.get("cohort_granularity", "month"),
            database=database,
        )

    # Custom Query
    elif name == "run_analytics_query":
        return await run_analytics_query(
            query=arguments["query"],
            database=database,
            limit=arguments.get("limit", 1000),
        )

    else:
        return {"error": f"Unknown tool: {name}"}


# =============================================================================
# Tool Implementations
# =============================================================================

async def descriptive_statistics(
    table_name: str,
    columns: list[str] | None = None,
    where_clause: str | None = None,
    database: str | None = None,
) -> dict[str, Any]:
    """Calculate descriptive statistics for numeric columns."""
    with get_connection(database) as conn:
        cursor = conn.cursor()

        # Get numeric columns if not specified
        if not columns:
            cursor.execute(
                """
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA + '.' + TABLE_NAME = ? OR TABLE_NAME = ?
                  AND DATA_TYPE IN ('int', 'bigint', 'smallint', 'tinyint',
                                   'decimal', 'numeric', 'float', 'real', 'money')
                """,
                (table_name, table_name),
            )
            columns = [row[0] for row in cursor.fetchall()]

        if not columns:
            return {"error": "No numeric columns found"}

        stats_results = {}

        for col in columns:
            where = f"WHERE {where_clause}" if where_clause else ""
            where_null = f"WHERE {col} IS NOT NULL" + (f" AND {where_clause}" if where_clause else "")

            query = f"""
                SELECT
                    COUNT({col}) as count,
                    AVG(CAST({col} AS FLOAT)) as mean,
                    STDEV(CAST({col} AS FLOAT)) as std_dev,
                    VAR(CAST({col} AS FLOAT)) as variance,
                    MIN({col}) as min_val,
                    MAX({col}) as max_val,
                    (SELECT PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {col})
                     FROM {table_name} {where_null}) as q1,
                    (SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {col})
                     FROM {table_name} {where_null}) as median,
                    (SELECT PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {col})
                     FROM {table_name} {where_null}) as q3
                FROM {table_name}
                {where}
            """

            try:
                cursor.execute(query)
                row = cursor.fetchone()

                stats_results[col] = {
                    "count": row[0],
                    "mean": row[1],
                    "std_dev": row[2],
                    "variance": row[3],
                    "min": row[4],
                    "max": row[5],
                    "q1": row[6],
                    "median": row[7],
                    "q3": row[8],
                    "iqr": (row[8] - row[6]) if row[6] and row[8] else None,
                }
            except Exception as e:
                stats_results[col] = {"error": str(e)}

        return {
            "table": table_name,
            "statistics": stats_results,
            "columns_analyzed": len(stats_results),
        }


async def correlation_analysis(
    table_name: str,
    columns: list[str],
    method: str = "pearson",
    database: str | None = None,
) -> dict[str, Any]:
    """Calculate correlation matrix between columns."""
    if len(columns) < 2:
        return {"error": "At least 2 columns required for correlation"}

    with get_connection(database) as conn:
        cursor = conn.cursor()

        # Fetch data for all columns
        cols_str = ", ".join(columns)
        query = f"SELECT {cols_str} FROM {table_name} WHERE " + " AND ".join(
            [f"{col} IS NOT NULL" for col in columns]
        )

        cursor.execute(query)
        rows = cursor.fetchall()

        if not rows:
            return {"error": "No data found with non-null values in all columns"}

        # Convert to column arrays
        data = {col: [] for col in columns}
        for row in rows:
            for i, col in enumerate(columns):
                data[col].append(float(row[i]) if row[i] is not None else 0)

        # Calculate correlation matrix
        correlation_matrix = {}
        for col1 in columns:
            correlation_matrix[col1] = {}
            for col2 in columns:
                if col1 == col2:
                    correlation_matrix[col1][col2] = 1.0
                else:
                    try:
                        if method == "pearson":
                            # Pearson correlation
                            n = len(data[col1])
                            mean1 = sum(data[col1]) / n
                            mean2 = sum(data[col2]) / n

                            numerator = sum(
                                (data[col1][i] - mean1) * (data[col2][i] - mean2)
                                for i in range(n)
                            )
                            std1 = math.sqrt(sum((x - mean1) ** 2 for x in data[col1]))
                            std2 = math.sqrt(sum((x - mean2) ** 2 for x in data[col2]))

                            corr = numerator / (std1 * std2) if std1 > 0 and std2 > 0 else 0
                        else:
                            # Spearman (rank correlation)
                            ranks1 = [sorted(data[col1]).index(x) + 1 for x in data[col1]]
                            ranks2 = [sorted(data[col2]).index(x) + 1 for x in data[col2]]
                            n = len(ranks1)

                            d_squared = sum((ranks1[i] - ranks2[i]) ** 2 for i in range(n))
                            corr = 1 - (6 * d_squared) / (n * (n ** 2 - 1))

                        correlation_matrix[col1][col2] = round(corr, 4)
                    except Exception:
                        correlation_matrix[col1][col2] = None

        return {
            "table": table_name,
            "method": method,
            "columns": columns,
            "correlation_matrix": correlation_matrix,
            "sample_size": len(rows),
        }


async def percentile_analysis(
    table_name: str,
    column: str,
    percentiles: list[float] = None,
    database: str | None = None,
) -> dict[str, Any]:
    """Calculate percentile values for a column."""
    if percentiles is None:
        percentiles = [10, 25, 50, 75, 90, 95, 99]

    with get_connection(database) as conn:
        cursor = conn.cursor()

        results = {}
        for p in percentiles:
            query = f"""
                SELECT PERCENTILE_CONT({p / 100.0}) WITHIN GROUP (ORDER BY {column})
                FROM {table_name}
                WHERE {column} IS NOT NULL
            """
            cursor.execute(query)
            row = cursor.fetchone()
            results[f"p{int(p)}"] = row[0]

        return {
            "table": table_name,
            "column": column,
            "percentiles": results,
        }


async def group_aggregation(
    table_name: str,
    group_by: list[str],
    aggregations: list[dict],
    having: str | None = None,
    order_by: str | None = None,
    limit: int = 100,
    database: str | None = None,
) -> dict[str, Any]:
    """Perform GROUP BY aggregations."""
    with get_connection(database) as conn:
        cursor = conn.cursor()

        group_cols = ", ".join(group_by)
        agg_exprs = []

        for agg in aggregations:
            col = agg["column"]
            func = agg["function"]
            alias = agg.get("alias", f"{func}_{col}")
            agg_exprs.append(f"{func}({col}) AS [{alias}]")

        agg_str = ", ".join(agg_exprs)

        query = f"""
            SELECT {group_cols}, {agg_str}
            FROM {table_name}
            GROUP BY {group_cols}
        """

        if having:
            query += f" HAVING {having}"

        if order_by:
            query += f" ORDER BY {order_by}"
        else:
            query += f" ORDER BY {group_by[0]}"

        query += f" OFFSET 0 ROWS FETCH NEXT {limit} ROWS ONLY"

        cursor.execute(query)
        rows = cursor.fetchall()
        results = [row_to_dict(cursor, row) for row in rows]

        return {
            "table": table_name,
            "group_by": group_by,
            "results": results,
            "count": len(results),
        }


async def pivot_analysis(
    table_name: str,
    row_column: str,
    pivot_column: str,
    value_column: str,
    aggregate_function: str = "SUM",
    database: str | None = None,
) -> dict[str, Any]:
    """Create a pivot table."""
    with get_connection(database) as conn:
        cursor = conn.cursor()

        # Get distinct pivot values
        cursor.execute(f"SELECT DISTINCT {pivot_column} FROM {table_name} WHERE {pivot_column} IS NOT NULL")
        pivot_values = [row[0] for row in cursor.fetchall()]

        if not pivot_values:
            return {"error": "No pivot values found"}

        # Build PIVOT query
        pivot_cols = ", ".join([f"[{v}]" for v in pivot_values])

        query = f"""
            SELECT {row_column}, {pivot_cols}
            FROM (
                SELECT {row_column}, {pivot_column}, {value_column}
                FROM {table_name}
            ) AS src
            PIVOT (
                {aggregate_function}({value_column})
                FOR {pivot_column} IN ({pivot_cols})
            ) AS pvt
            ORDER BY {row_column}
        """

        cursor.execute(query)
        rows = cursor.fetchall()
        results = [row_to_dict(cursor, row) for row in rows]

        return {
            "table": table_name,
            "row_column": row_column,
            "pivot_column": pivot_column,
            "value_column": value_column,
            "aggregate": aggregate_function,
            "pivot_values": pivot_values,
            "results": results,
            "count": len(results),
        }


async def time_series_analysis(
    table_name: str,
    date_column: str,
    value_column: str,
    granularity: str = "day",
    include_moving_average: bool = True,
    moving_average_window: int = 7,
    database: str | None = None,
) -> dict[str, Any]:
    """Analyze time series data."""
    with get_connection(database) as conn:
        cursor = conn.cursor()

        # Date truncation based on granularity
        date_formats = {
            "hour": f"DATEADD(HOUR, DATEDIFF(HOUR, 0, {date_column}), 0)",
            "day": f"CAST({date_column} AS DATE)",
            "week": f"DATEADD(WEEK, DATEDIFF(WEEK, 0, {date_column}), 0)",
            "month": f"DATEADD(MONTH, DATEDIFF(MONTH, 0, {date_column}), 0)",
            "quarter": f"DATEADD(QUARTER, DATEDIFF(QUARTER, 0, {date_column}), 0)",
            "year": f"DATEADD(YEAR, DATEDIFF(YEAR, 0, {date_column}), 0)",
        }

        date_expr = date_formats.get(granularity, date_formats["day"])

        query = f"""
            SELECT
                {date_expr} as period,
                SUM({value_column}) as total,
                COUNT(*) as count,
                AVG(CAST({value_column} AS FLOAT)) as avg_value
            FROM {table_name}
            WHERE {date_column} IS NOT NULL
            GROUP BY {date_expr}
            ORDER BY {date_expr}
        """

        cursor.execute(query)
        rows = cursor.fetchall()
        results = [row_to_dict(cursor, row) for row in rows]

        # Calculate moving average if requested
        if include_moving_average and len(results) >= moving_average_window:
            values = [r["total"] for r in results]
            for i in range(len(results)):
                if i >= moving_average_window - 1:
                    window = values[i - moving_average_window + 1 : i + 1]
                    results[i]["moving_avg"] = sum(window) / len(window)
                else:
                    results[i]["moving_avg"] = None

        return {
            "table": table_name,
            "date_column": date_column,
            "value_column": value_column,
            "granularity": granularity,
            "data": results,
            "periods": len(results),
        }


async def trend_detection(
    table_name: str,
    date_column: str,
    value_column: str,
    comparison_periods: list[str] = None,
    database: str | None = None,
) -> dict[str, Any]:
    """Detect trends and calculate growth rates."""
    if comparison_periods is None:
        comparison_periods = ["week", "month"]

    with get_connection(database) as conn:
        cursor = conn.cursor()

        trends = {}

        for period in comparison_periods:
            if period == "day":
                interval = 1
            elif period == "week":
                interval = 7
            elif period == "month":
                interval = 30
            elif period == "year":
                interval = 365
            else:
                interval = 7

            query = f"""
                WITH current_period AS (
                    SELECT SUM({value_column}) as current_total
                    FROM {table_name}
                    WHERE {date_column} >= DATEADD(DAY, -{interval}, GETDATE())
                ),
                previous_period AS (
                    SELECT SUM({value_column}) as previous_total
                    FROM {table_name}
                    WHERE {date_column} >= DATEADD(DAY, -{interval * 2}, GETDATE())
                      AND {date_column} < DATEADD(DAY, -{interval}, GETDATE())
                )
                SELECT
                    c.current_total,
                    p.previous_total,
                    CASE
                        WHEN p.previous_total > 0
                        THEN ((c.current_total - p.previous_total) / p.previous_total) * 100
                        ELSE NULL
                    END as growth_rate
                FROM current_period c, previous_period p
            """

            cursor.execute(query)
            row = cursor.fetchone()

            trends[period] = {
                "current": row[0],
                "previous": row[1],
                "growth_rate_pct": round(row[2], 2) if row[2] else None,
                "trend": "up" if row[2] and row[2] > 0 else "down" if row[2] and row[2] < 0 else "flat",
            }

        return {
            "table": table_name,
            "value_column": value_column,
            "trends": trends,
        }


async def profile_table(
    table_name: str,
    sample_size: int = 5,
    database: str | None = None,
) -> dict[str, Any]:
    """Generate comprehensive data profile for a table."""
    with get_connection(database) as conn:
        cursor = conn.cursor()

        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_rows = cursor.fetchone()[0]

        # Get column info
        cursor.execute(
            """
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA + '.' + TABLE_NAME = ? OR TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
            """,
            (table_name, table_name),
        )
        columns_info = cursor.fetchall()

        profile = {
            "table": table_name,
            "total_rows": total_rows,
            "columns": {},
        }

        for col_info in columns_info:
            col_name, data_type, nullable, max_len = col_info

            # Get column stats
            cursor.execute(
                f"""
                SELECT
                    COUNT(*) as total,
                    COUNT({col_name}) as non_null,
                    COUNT(DISTINCT {col_name}) as distinct_count
                FROM {table_name}
                """
            )
            stats = cursor.fetchone()

            null_count = stats[0] - stats[1]
            null_pct = (null_count / stats[0] * 100) if stats[0] > 0 else 0

            # Get sample values
            cursor.execute(
                f"""
                SELECT TOP {sample_size} {col_name}
                FROM {table_name}
                WHERE {col_name} IS NOT NULL
                ORDER BY NEWID()
                """
            )
            samples = [row[0] for row in cursor.fetchall()]

            profile["columns"][col_name] = {
                "data_type": data_type,
                "nullable": nullable == "YES",
                "max_length": max_len,
                "non_null_count": stats[1],
                "null_count": null_count,
                "null_pct": round(null_pct, 2),
                "distinct_count": stats[2],
                "cardinality_ratio": round(stats[2] / stats[0] * 100, 2) if stats[0] > 0 else 0,
                "sample_values": samples,
            }

        return profile


async def column_distribution(
    table_name: str,
    column: str,
    bins: int = 10,
    top_n: int = 20,
    database: str | None = None,
) -> dict[str, Any]:
    """Analyze value distribution for a column."""
    with get_connection(database) as conn:
        cursor = conn.cursor()

        # Check if column is numeric
        cursor.execute(
            """
            SELECT DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE (TABLE_SCHEMA + '.' + TABLE_NAME = ? OR TABLE_NAME = ?)
              AND COLUMN_NAME = ?
            """,
            (table_name, table_name, column),
        )
        row = cursor.fetchone()

        if not row:
            return {"error": f"Column {column} not found"}

        data_type = row[0]
        numeric_types = ["int", "bigint", "smallint", "tinyint", "decimal", "numeric", "float", "real", "money"]

        if data_type in numeric_types:
            # Histogram for numeric columns
            cursor.execute(
                f"""
                SELECT MIN({column}), MAX({column})
                FROM {table_name}
                WHERE {column} IS NOT NULL
                """
            )
            min_val, max_val = cursor.fetchone()

            if min_val is None or max_val is None:
                return {"error": "No non-null values found"}

            bin_width = (max_val - min_val) / bins if min_val != max_val else 1

            histogram = []
            for i in range(bins):
                lower = min_val + (i * bin_width)
                upper = min_val + ((i + 1) * bin_width)

                if i == bins - 1:
                    cursor.execute(
                        f"SELECT COUNT(*) FROM {table_name} WHERE {column} >= ? AND {column} <= ?",
                        (lower, upper),
                    )
                else:
                    cursor.execute(
                        f"SELECT COUNT(*) FROM {table_name} WHERE {column} >= ? AND {column} < ?",
                        (lower, upper),
                    )

                count = cursor.fetchone()[0]
                histogram.append({
                    "bin": i + 1,
                    "lower": lower,
                    "upper": upper,
                    "count": count,
                })

            return {
                "table": table_name,
                "column": column,
                "type": "numeric",
                "min": min_val,
                "max": max_val,
                "histogram": histogram,
            }
        else:
            # Frequency counts for categorical columns
            cursor.execute(
                f"""
                SELECT TOP {top_n} {column}, COUNT(*) as frequency
                FROM {table_name}
                WHERE {column} IS NOT NULL
                GROUP BY {column}
                ORDER BY COUNT(*) DESC
                """
            )

            frequencies = [{"value": row[0], "count": row[1]} for row in cursor.fetchall()]

            return {
                "table": table_name,
                "column": column,
                "type": "categorical",
                "top_values": frequencies,
            }


async def data_quality_check(
    table_name: str,
    columns: list[str] | None = None,
    check_duplicates: bool = True,
    check_outliers: bool = True,
    outlier_threshold: float = 1.5,
    database: str | None = None,
) -> dict[str, Any]:
    """Check data quality issues."""
    with get_connection(database) as conn:
        cursor = conn.cursor()

        # Get columns if not specified
        if not columns:
            cursor.execute(
                """
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA + '.' + TABLE_NAME = ? OR TABLE_NAME = ?
                """,
                (table_name, table_name),
            )
            columns = [row[0] for row in cursor.fetchall()]

        quality_report = {
            "table": table_name,
            "columns_checked": columns,
            "issues": [],
        }

        # Check nulls
        for col in columns:
            cursor.execute(
                f"SELECT COUNT(*) as total, SUM(CASE WHEN {col} IS NULL THEN 1 ELSE 0 END) as nulls FROM {table_name}"
            )
            total, nulls = cursor.fetchone()
            null_pct = (nulls / total * 100) if total > 0 else 0

            if null_pct > 0:
                quality_report["issues"].append({
                    "type": "null_values",
                    "column": col,
                    "count": nulls,
                    "percentage": round(null_pct, 2),
                    "severity": "high" if null_pct > 50 else "medium" if null_pct > 10 else "low",
                })

        # Check duplicates
        if check_duplicates:
            all_cols = ", ".join(columns)
            cursor.execute(
                f"""
                SELECT COUNT(*) as duplicate_groups
                FROM (
                    SELECT {all_cols}
                    FROM {table_name}
                    GROUP BY {all_cols}
                    HAVING COUNT(*) > 1
                ) AS dups
                """
            )
            dup_groups = cursor.fetchone()[0]

            if dup_groups > 0:
                quality_report["issues"].append({
                    "type": "duplicate_rows",
                    "duplicate_groups": dup_groups,
                    "severity": "medium",
                })

        # Check outliers for numeric columns
        if check_outliers:
            cursor.execute(
                """
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE (TABLE_SCHEMA + '.' + TABLE_NAME = ? OR TABLE_NAME = ?)
                  AND DATA_TYPE IN ('int', 'bigint', 'smallint', 'decimal', 'numeric', 'float', 'real')
                """,
                (table_name, table_name),
            )
            numeric_cols = [row[0] for row in cursor.fetchall() if row[0] in columns]

            for col in numeric_cols:
                cursor.execute(
                    f"""
                    SELECT
                        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {col}) as q1,
                        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {col}) as q3
                    FROM {table_name}
                    WHERE {col} IS NOT NULL
                    """
                )
                q1, q3 = cursor.fetchone()

                if q1 is not None and q3 is not None:
                    iqr = q3 - q1
                    lower = q1 - (outlier_threshold * iqr)
                    upper = q3 + (outlier_threshold * iqr)

                    cursor.execute(
                        f"SELECT COUNT(*) FROM {table_name} WHERE {col} < ? OR {col} > ?",
                        (lower, upper),
                    )
                    outlier_count = cursor.fetchone()[0]

                    if outlier_count > 0:
                        quality_report["issues"].append({
                            "type": "outliers",
                            "column": col,
                            "count": outlier_count,
                            "lower_bound": lower,
                            "upper_bound": upper,
                            "severity": "low",
                        })

        quality_report["total_issues"] = len(quality_report["issues"])

        return quality_report


async def detect_outliers(
    table_name: str,
    column: str,
    method: str = "iqr",
    threshold: float = 1.5,
    return_data: bool = True,
    limit: int = 100,
    database: str | None = None,
) -> dict[str, Any]:
    """Detect outliers using IQR or Z-score method."""
    with get_connection(database) as conn:
        cursor = conn.cursor()

        if method == "iqr":
            cursor.execute(
                f"""
                SELECT
                    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {column}) as q1,
                    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {column}) as q3
                FROM {table_name}
                WHERE {column} IS NOT NULL
                """
            )
            q1, q3 = cursor.fetchone()
            iqr = q3 - q1
            lower = q1 - (threshold * iqr)
            upper = q3 + (threshold * iqr)

            cursor.execute(
                f"SELECT COUNT(*) FROM {table_name} WHERE {column} < ? OR {column} > ?",
                (lower, upper),
            )
            outlier_count = cursor.fetchone()[0]

            result = {
                "table": table_name,
                "column": column,
                "method": "iqr",
                "q1": q1,
                "q3": q3,
                "iqr": iqr,
                "lower_bound": lower,
                "upper_bound": upper,
                "outlier_count": outlier_count,
            }

            if return_data and outlier_count > 0:
                cursor.execute(
                    f"""
                    SELECT TOP {limit} *
                    FROM {table_name}
                    WHERE {column} < ? OR {column} > ?
                    ORDER BY ABS({column}) DESC
                    """,
                    (lower, upper),
                )
                result["outliers"] = [row_to_dict(cursor, row) for row in cursor.fetchall()]

        else:  # zscore
            cursor.execute(
                f"""
                SELECT AVG(CAST({column} AS FLOAT)), STDEV(CAST({column} AS FLOAT))
                FROM {table_name}
                WHERE {column} IS NOT NULL
                """
            )
            mean, std = cursor.fetchone()

            if std is None or std == 0:
                return {"error": "Cannot calculate Z-scores (zero or null standard deviation)"}

            cursor.execute(
                f"""
                SELECT COUNT(*)
                FROM {table_name}
                WHERE ABS((CAST({column} AS FLOAT) - ?) / ?) > ?
                """,
                (mean, std, threshold),
            )
            outlier_count = cursor.fetchone()[0]

            result = {
                "table": table_name,
                "column": column,
                "method": "zscore",
                "mean": mean,
                "std": std,
                "threshold": threshold,
                "outlier_count": outlier_count,
            }

            if return_data and outlier_count > 0:
                cursor.execute(
                    f"""
                    SELECT TOP {limit} *, (CAST({column} AS FLOAT) - ?) / ? as zscore
                    FROM {table_name}
                    WHERE ABS((CAST({column} AS FLOAT) - ?) / ?) > ?
                    ORDER BY ABS((CAST({column} AS FLOAT) - ?) / ?) DESC
                    """,
                    (mean, std, mean, std, threshold, mean, std),
                )
                result["outliers"] = [row_to_dict(cursor, row) for row in cursor.fetchall()]

        return result


async def detect_anomalies_timeseries(
    table_name: str,
    date_column: str,
    value_column: str,
    window_size: int = 7,
    std_threshold: float = 2.0,
    database: str | None = None,
) -> dict[str, Any]:
    """Detect anomalies in time series using rolling statistics."""
    with get_connection(database) as conn:
        cursor = conn.cursor()

        query = f"""
            WITH daily_data AS (
                SELECT
                    CAST({date_column} AS DATE) as date,
                    SUM({value_column}) as value
                FROM {table_name}
                WHERE {date_column} IS NOT NULL
                GROUP BY CAST({date_column} AS DATE)
            ),
            rolling_stats AS (
                SELECT
                    date,
                    value,
                    AVG(value) OVER (ORDER BY date ROWS BETWEEN {window_size} PRECEDING AND 1 PRECEDING) as rolling_avg,
                    STDEV(value) OVER (ORDER BY date ROWS BETWEEN {window_size} PRECEDING AND 1 PRECEDING) as rolling_std
                FROM daily_data
            )
            SELECT
                date,
                value,
                rolling_avg,
                rolling_std,
                CASE
                    WHEN rolling_std > 0 AND ABS(value - rolling_avg) / rolling_std > {std_threshold}
                    THEN 1 ELSE 0
                END as is_anomaly,
                CASE
                    WHEN rolling_std > 0
                    THEN (value - rolling_avg) / rolling_std
                    ELSE 0
                END as zscore
            FROM rolling_stats
            WHERE rolling_avg IS NOT NULL
            ORDER BY date
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        all_data = []
        anomalies = []

        for row in rows:
            data_point = {
                "date": row[0],
                "value": row[1],
                "rolling_avg": row[2],
                "rolling_std": row[3],
                "is_anomaly": row[4] == 1,
                "zscore": round(row[5], 2) if row[5] else None,
            }
            all_data.append(data_point)

            if row[4] == 1:
                anomalies.append(data_point)

        return {
            "table": table_name,
            "date_column": date_column,
            "value_column": value_column,
            "window_size": window_size,
            "std_threshold": std_threshold,
            "total_points": len(all_data),
            "anomaly_count": len(anomalies),
            "anomalies": anomalies,
        }


async def segment_analysis(
    table_name: str,
    segment_column: str,
    metric_columns: list[str],
    include_comparison: bool = True,
    database: str | None = None,
) -> dict[str, Any]:
    """Analyze data by segments."""
    with get_connection(database) as conn:
        cursor = conn.cursor()

        # Build aggregation expressions
        agg_exprs = []
        for col in metric_columns:
            agg_exprs.extend([
                f"COUNT({col}) as {col}_count",
                f"SUM(CAST({col} AS FLOAT)) as {col}_sum",
                f"AVG(CAST({col} AS FLOAT)) as {col}_avg",
                f"MIN({col}) as {col}_min",
                f"MAX({col}) as {col}_max",
            ])

        agg_str = ", ".join(agg_exprs)

        query = f"""
            SELECT {segment_column}, COUNT(*) as row_count, {agg_str}
            FROM {table_name}
            WHERE {segment_column} IS NOT NULL
            GROUP BY {segment_column}
            ORDER BY COUNT(*) DESC
        """

        cursor.execute(query)
        rows = cursor.fetchall()
        segments = [row_to_dict(cursor, row) for row in rows]

        result = {
            "table": table_name,
            "segment_column": segment_column,
            "metric_columns": metric_columns,
            "segments": segments,
            "segment_count": len(segments),
        }

        if include_comparison:
            # Calculate overall stats for comparison
            cursor.execute(
                f"SELECT COUNT(*) as total, {agg_str} FROM {table_name}"
            )
            overall = row_to_dict(cursor, cursor.fetchone())
            result["overall"] = overall

        return result


async def cohort_analysis(
    table_name: str,
    cohort_date_column: str,
    event_date_column: str,
    value_column: str | None = None,
    aggregate_function: str = "COUNT",
    cohort_granularity: str = "month",
    database: str | None = None,
) -> dict[str, Any]:
    """Perform cohort analysis."""
    with get_connection(database) as conn:
        cursor = conn.cursor()

        # Date truncation based on granularity
        date_formats = {
            "day": "CAST({} AS DATE)",
            "week": "DATEADD(WEEK, DATEDIFF(WEEK, 0, {}), 0)",
            "month": "DATEADD(MONTH, DATEDIFF(MONTH, 0, {}), 0)",
            "year": "DATEADD(YEAR, DATEDIFF(YEAR, 0, {}), 0)",
        }

        date_format = date_formats.get(cohort_granularity, date_formats["month"])
        cohort_expr = date_format.format(cohort_date_column)
        event_expr = date_format.format(event_date_column)

        value_expr = f"{aggregate_function}({value_column})" if value_column else "COUNT(*)"

        query = f"""
            SELECT
                {cohort_expr} as cohort,
                DATEDIFF({cohort_granularity}, {cohort_expr}, {event_expr}) as period,
                {value_expr} as value
            FROM {table_name}
            WHERE {cohort_date_column} IS NOT NULL AND {event_date_column} IS NOT NULL
            GROUP BY {cohort_expr}, DATEDIFF({cohort_granularity}, {cohort_expr}, {event_expr})
            ORDER BY {cohort_expr}, period
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        cohorts = defaultdict(dict)
        for row in rows:
            cohort = str(row[0])
            period = row[1]
            value = row[2]
            cohorts[cohort][f"period_{period}"] = value

        return {
            "table": table_name,
            "cohort_column": cohort_date_column,
            "event_column": event_date_column,
            "granularity": cohort_granularity,
            "aggregate": aggregate_function,
            "cohorts": dict(cohorts),
        }


async def run_analytics_query(
    query: str,
    database: str | None = None,
    limit: int = 1000,
) -> dict[str, Any]:
    """Execute a custom analytics query with safety checks."""
    # Safety check - only allow SELECT statements
    query_upper = query.strip().upper()
    if not query_upper.startswith("SELECT"):
        return {"error": "Only SELECT queries are allowed"}

    # Block dangerous keywords
    dangerous = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE", "EXEC", "EXECUTE"]
    for kw in dangerous:
        if kw in query_upper:
            return {"error": f"Query contains forbidden keyword: {kw}"}

    with get_connection(database) as conn:
        cursor = conn.cursor()

        # Add limit if not present
        if "TOP" not in query_upper and "OFFSET" not in query_upper:
            query = query.replace("SELECT", f"SELECT TOP {limit}", 1)

        cursor.execute(query)
        rows = cursor.fetchall()
        results = [row_to_dict(cursor, row) for row in rows]

        return {
            "query": query,
            "results": results,
            "row_count": len(results),
        }


# =============================================================================
# Main Entry Point
# =============================================================================

async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
