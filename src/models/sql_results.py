"""
SQL Result Models

Pydantic models for representing SQL query results and database schema information.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ColumnInfo(BaseModel):
    """Information about a database column."""

    name: str
    data_type: str
    nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    default_value: str | None = None
    max_length: int | None = None
    description: str | None = None


class TableInfo(BaseModel):
    """Information about a database table."""

    name: str
    schema_name: str = "dbo"
    columns: list[ColumnInfo] = Field(default_factory=list)
    row_count: int | None = None
    description: str | None = None

    @property
    def full_name(self) -> str:
        """Get fully qualified table name."""
        return f"{self.schema_name}.{self.name}"

    @property
    def column_names(self) -> list[str]:
        """Get list of column names."""
        return [col.name for col in self.columns]

    @property
    def primary_key_columns(self) -> list[str]:
        """Get primary key column names."""
        return [col.name for col in self.columns if col.is_primary_key]


class QueryResult(BaseModel):
    """Result of a SQL query."""

    rows: list[dict[str, Any]] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)
    row_count: int = 0
    affected_rows: int | None = None
    execution_time_ms: float = 0.0
    query: str = ""
    error: str | None = None

    @classmethod
    def from_rows(cls, rows: list[dict[str, Any]], query: str = "") -> "QueryResult":
        """Create result from list of row dictionaries."""
        columns = list(rows[0].keys()) if rows else []
        return cls(
            rows=rows,
            columns=columns,
            row_count=len(rows),
            query=query,
        )

    @classmethod
    def error_result(cls, error: str, query: str = "") -> "QueryResult":
        """Create an error result."""
        return cls(error=error, query=query)

    @property
    def success(self) -> bool:
        """Check if query was successful."""
        return self.error is None

    @property
    def is_empty(self) -> bool:
        """Check if result has no rows."""
        return self.row_count == 0

    def to_markdown_table(self, max_rows: int = 20) -> str:
        """
        Format results as a markdown table.

        Args:
            max_rows: Maximum rows to include

        Returns:
            Markdown-formatted table string
        """
        if not self.rows:
            return "*No results*"

        rows_to_show = self.rows[:max_rows]
        truncated = len(self.rows) > max_rows

        # Header
        lines = [
            "| " + " | ".join(self.columns) + " |",
            "| " + " | ".join(["---"] * len(self.columns)) + " |",
        ]

        # Rows
        for row in rows_to_show:
            values = [str(row.get(col, "")) for col in self.columns]
            # Truncate long values
            values = [v[:50] + "..." if len(v) > 50 else v for v in values]
            lines.append("| " + " | ".join(values) + " |")

        if truncated:
            lines.append(f"\n*Showing {max_rows} of {self.row_count} rows*")

        return "\n".join(lines)


class DatabaseSchema(BaseModel):
    """Complete database schema information."""

    tables: list[TableInfo] = Field(default_factory=list)
    database_name: str = ""
    server_name: str = ""
    retrieved_at: datetime = Field(default_factory=datetime.now)

    @property
    def table_names(self) -> list[str]:
        """Get list of table names."""
        return [table.name for table in self.tables]

    @property
    def table_count(self) -> int:
        """Get number of tables."""
        return len(self.tables)

    def get_table(self, name: str) -> TableInfo | None:
        """Get table info by name."""
        for table in self.tables:
            if table.name.lower() == name.lower():
                return table
        return None
