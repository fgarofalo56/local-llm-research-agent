"""
RAG Search Example

Demonstrates how to use the RAG (Retrieval-Augmented Generation) tools
for knowledge base search and document retrieval. Shows:
- Hybrid vector + keyword search
- Knowledge source listing
- Document content retrieval
- Search result filtering

Prerequisites:
1. SQL Server 2025 (LLM_BackEnd database) running on port 1434
2. Documents indexed in the vector store
3. Ollama running with nomic-embed-text for embeddings
4. Environment variables set in .env file
"""

import asyncio
import os
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.tools import RAGTools, create_rag_tools
from src.utils.config import settings
from src.utils.logger import setup_logging


async def demo_list_knowledge_sources(rag_tools: RAGTools) -> None:
    """List all available knowledge sources."""
    print("\n" + "=" * 60)
    print("DEMO: List Knowledge Sources")
    print("=" * 60)
    print("\nRetrieving all indexed knowledge sources...")
    print("-" * 60)

    try:
        sources = await rag_tools.list_knowledge_sources()

        if not sources:
            print("No knowledge sources found. Upload documents first!")
            return

        print(f"\nFound {len(sources)} knowledge sources:\n")
        for source in sources:
            print(f"  Source: {source.name}")
            print(f"    Type: {source.source_type}")
            print(f"    Documents: {source.document_count}")
            print(f"    Chunks: {source.chunk_count}")
            if source.last_updated:
                print(f"    Last Updated: {source.last_updated}")
            print()
    except Exception as e:
        print(f"Error listing sources: {e}")


async def demo_hybrid_search(rag_tools: RAGTools) -> None:
    """Demonstrate hybrid vector + keyword search."""
    print("\n" + "=" * 60)
    print("DEMO: Hybrid Search (Vector + Keyword)")
    print("=" * 60)
    print("\nSearching with combined semantic similarity and keyword matching.")
    print("Query: 'SQL Server vector search similarity'")
    print("-" * 60)

    try:
        results = await rag_tools.search_knowledge_base(
            query="SQL Server vector search similarity",
            top_k=5,
            min_score=0.3,
        )

        if not results:
            print("No results found. Make sure documents are indexed!")
            return

        print(f"\nFound {len(results)} results:\n")
        for i, result in enumerate(results, 1):
            print(f"[{i}] Document: {result.document_id}, Chunk: {result.chunk_id}")
            print(f"    Source: {result.source} ({result.source_type})")
            print(f"    Scores: Combined={result.relevance_score:.4f}, "
                  f"Vector={result.vector_score:.4f}, Text={result.text_score:.4f}")
            print(f"    Content Preview: {result.content[:150]}...")
            print()
    except Exception as e:
        print(f"Error during search: {e}")


async def demo_filtered_search(rag_tools: RAGTools) -> None:
    """Demonstrate search with source filtering."""
    print("\n" + "=" * 60)
    print("DEMO: Filtered Search by Source")
    print("=" * 60)
    print("\nSearching within a specific source/collection.")
    print("-" * 60)

    try:
        # First, get available sources
        sources = await rag_tools.list_knowledge_sources()

        if not sources:
            print("No sources available for filtering.")
            return

        # Use the first available source for filtering
        filter_source = sources[0].name
        print(f"Filtering search to source: {filter_source}")

        results = await rag_tools.search_knowledge_base(
            query="research analytics",
            top_k=3,
            source_filter=filter_source,
            min_score=0.2,
        )

        print(f"\nFound {len(results)} results from '{filter_source}':\n")
        for i, result in enumerate(results, 1):
            print(f"[{i}] Score: {result.relevance_score:.4f}")
            print(f"    Content: {result.content[:200]}...")
            print()
    except Exception as e:
        print(f"Error during filtered search: {e}")


async def demo_keyword_search(rag_tools: RAGTools) -> None:
    """Demonstrate keyword-only search."""
    print("\n" + "=" * 60)
    print("DEMO: Keyword-Only Search")
    print("=" * 60)
    print("\nSearching using keywords without vector similarity.")
    print("Keywords: ['database', 'query']")
    print("-" * 60)

    try:
        results = await rag_tools.search_by_keywords(
            keywords=["database", "query"],
            top_k=5,
            match_all=False,  # Match any keyword
        )

        print(f"\nFound {len(results)} results:\n")
        for i, result in enumerate(results, 1):
            print(f"[{i}] Source: {result.source}")
            print(f"    Content: {result.content[:150]}...")
            print()
    except Exception as e:
        print(f"Error during keyword search: {e}")


async def demo_get_document(rag_tools: RAGTools) -> None:
    """Demonstrate full document retrieval."""
    print("\n" + "=" * 60)
    print("DEMO: Full Document Retrieval")
    print("=" * 60)
    print("\nRetrieving a complete document by ID.")
    print("-" * 60)

    try:
        # First search to get a document ID
        results = await rag_tools.search_knowledge_base(
            query="research",
            top_k=1,
        )

        if not results:
            print("No documents found to retrieve.")
            return

        doc_id = results[0].document_id
        print(f"Retrieving document ID: {doc_id}")

        doc = await rag_tools.get_document_content(doc_id)

        if doc:
            print(f"\nDocument: {doc.source}")
            print(f"Type: {doc.source_type}")
            print(f"Word Count: {doc.word_count}")
            print(f"Chunks: {len(doc.chunks)}")
            print(f"\nFirst 500 characters of content:")
            print("-" * 40)
            print(doc.full_content[:500])
            print("...")
        else:
            print(f"Document {doc_id} not found.")
    except Exception as e:
        print(f"Error retrieving document: {e}")


async def main():
    """Run all RAG search demonstrations."""
    setup_logging()

    print("=" * 60)
    print("RAG Search Example - Local LLM Research Agent")
    print("=" * 60)
    print(f"\nBackend Database: {settings.backend_db_host}:{settings.backend_db_port}")
    print(f"Database Name: {settings.backend_db_name}")
    print(f"Vector Store Type: {settings.vector_store_type}")
    print("\nThis example demonstrates RAG tools for knowledge base search.")

    # Create database session factory
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    # Build connection string for SQL Server 2025 backend
    connection_string = (
        f"mssql+aioodbc://{settings.backend_db_username or settings.sql_username}:"
        f"{settings.backend_db_password or settings.sql_password}@"
        f"{settings.backend_db_host}:{settings.backend_db_port}/"
        f"{settings.backend_db_name}?"
        f"driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
    )

    engine = create_async_engine(connection_string, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # Create RAG tools instance
    rag_tools = create_rag_tools(session_factory)

    try:
        # Run demonstrations
        await demo_list_knowledge_sources(rag_tools)
        await demo_hybrid_search(rag_tools)
        await demo_filtered_search(rag_tools)
        await demo_keyword_search(rag_tools)
        await demo_get_document(rag_tools)

        print("\n" + "=" * 60)
        print("RAG Search Example Complete")
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure:")
        print("1. SQL Server 2025 (LLM_BackEnd) is running on port 1434")
        print("2. Documents have been uploaded and indexed")
        print("3. Ollama is running with nomic-embed-text model")
        print("4. Environment variables are set in .env file")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
