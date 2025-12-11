"""
Schema Indexer
Phase 2.1: Backend Infrastructure & RAG Pipeline

Indexes database schema information into the vector store for RAG-enhanced queries.
"""

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.rag.redis_vector_store import RedisVectorStore

logger = structlog.get_logger()


class SchemaIndexer:
    """Index database schema into vector store for RAG-enhanced queries."""

    def __init__(self, vector_store: RedisVectorStore):
        """
        Initialize the schema indexer.

        Args:
            vector_store: Redis vector store instance
        """
        self.vector_store = vector_store

    async def index_schema(self, db: AsyncSession) -> dict:
        """
        Extract and index database schema information.

        Args:
            db: Database session

        Returns:
            Dictionary with indexing statistics
        """
        logger.info("indexing_database_schema")

        # Get all tables
        tables_query = text("""
            SELECT
                t.TABLE_NAME,
                t.TABLE_TYPE
            FROM INFORMATION_SCHEMA.TABLES t
            WHERE t.TABLE_SCHEMA = 'dbo'
            AND t.TABLE_TYPE = 'BASE TABLE'
        """)

        result = await db.execute(tables_query)
        tables = result.fetchall()

        chunks = []
        for table in tables:
            table_name = table[0]

            # Get columns for this table
            columns_query = text("""
                SELECT
                    c.COLUMN_NAME,
                    c.DATA_TYPE,
                    c.IS_NULLABLE,
                    c.CHARACTER_MAXIMUM_LENGTH,
                    ISNULL(ep.value, '') as DESCRIPTION
                FROM INFORMATION_SCHEMA.COLUMNS c
                LEFT JOIN sys.extended_properties ep
                    ON ep.major_id = OBJECT_ID(c.TABLE_SCHEMA + '.' + c.TABLE_NAME)
                    AND ep.minor_id = COLUMNPROPERTY(
                        OBJECT_ID(c.TABLE_SCHEMA + '.' + c.TABLE_NAME),
                        c.COLUMN_NAME,
                        'ColumnId'
                    )
                    AND ep.name = 'MS_Description'
                WHERE c.TABLE_NAME = :table_name
                AND c.TABLE_SCHEMA = 'dbo'
                ORDER BY c.ORDINAL_POSITION
            """)

            cols_result = await db.execute(columns_query, {"table_name": table_name})
            columns = cols_result.fetchall()

            # Build schema description
            schema_text = f"Table: {table_name}\n"
            schema_text += "Columns:\n"
            for col in columns:
                col_name, data_type, nullable, max_len, desc = col
                schema_text += f"  - {col_name} ({data_type}"
                if max_len:
                    schema_text += f", max length: {max_len}"
                schema_text += f", nullable: {nullable})"
                if desc:
                    schema_text += f" - {desc}"
                schema_text += "\n"

            chunks.append(schema_text)

        # Get relationships
        fk_query = text("""
            SELECT
                fk.name AS FK_NAME,
                tp.name AS PARENT_TABLE,
                cp.name AS PARENT_COLUMN,
                tr.name AS REFERENCED_TABLE,
                cr.name AS REFERENCED_COLUMN
            FROM sys.foreign_keys fk
            INNER JOIN sys.foreign_key_columns fkc
                ON fk.object_id = fkc.constraint_object_id
            INNER JOIN sys.tables tp
                ON fkc.parent_object_id = tp.object_id
            INNER JOIN sys.columns cp
                ON fkc.parent_object_id = cp.object_id
                AND fkc.parent_column_id = cp.column_id
            INNER JOIN sys.tables tr
                ON fkc.referenced_object_id = tr.object_id
            INNER JOIN sys.columns cr
                ON fkc.referenced_object_id = cr.object_id
                AND fkc.referenced_column_id = cr.column_id
        """)

        fk_result = await db.execute(fk_query)
        relationships = fk_result.fetchall()

        if relationships:
            rel_text = "Database Relationships:\n"
            for rel in relationships:
                fk_name, parent, parent_col, ref, ref_col = rel
                rel_text += f"  - {parent}.{parent_col} references {ref}.{ref_col}\n"
            chunks.append(rel_text)

        # Add to vector store
        await self.vector_store.add_document(
            document_id="schema",
            chunks=chunks,
            source="database_schema",
            source_type="schema",
            metadata={
                "table_count": len(tables),
                "relationship_count": len(relationships),
            },
        )

        logger.info(
            "schema_indexed",
            tables=len(tables),
            relationships=len(relationships),
            chunks=len(chunks),
        )

        return {
            "tables_indexed": len(tables),
            "relationships_indexed": len(relationships),
            "chunks_created": len(chunks),
        }

    async def refresh_schema(self, db: AsyncSession) -> dict:
        """
        Refresh the schema index (delete old, create new).

        Args:
            db: Database session

        Returns:
            Dictionary with refresh statistics
        """
        # Delete existing schema chunks
        deleted = await self.vector_store.delete_document("schema")
        logger.info("schema_chunks_deleted", count=deleted)

        # Re-index
        stats = await self.index_schema(db)
        stats["deleted_chunks"] = deleted

        return stats
