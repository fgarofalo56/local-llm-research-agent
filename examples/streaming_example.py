"""
Streaming Example

Demonstrates how to use streaming responses with the research agent.
Streaming allows you to display text as it's generated, providing
a better user experience for longer responses.

Features demonstrated:
- Basic streaming output
- Progress indicators
- Combining streaming with Rich console formatting
- Error handling during streams

Prerequisites:
1. Ollama or Foundry Local running with a compatible model
2. MSSQL MCP Server setup and configured
3. Environment variables set in .env file
"""

import asyncio
import os
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.research_agent import create_research_agent
from src.utils.config import settings
from src.utils.logger import setup_logging

# Optional: Rich console for better formatting
try:
    from rich.console import Console
    from rich.live import Live
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.spinner import Spinner

    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False


async def demo_basic_streaming() -> None:
    """Basic streaming - print chunks as they arrive."""
    print("\n" + "=" * 60)
    print("DEMO: Basic Streaming Output")
    print("=" * 60)
    print()

    agent = create_research_agent(readonly=True)

    print("Agent: ", end="", flush=True)
    async for chunk in agent.chat_stream("What tables are available in the database?"):
        print(chunk, end="", flush=True)
    print("\n")


async def demo_streaming_with_spinner() -> None:
    """Streaming with a spinner during initial processing."""
    print("\n" + "=" * 60)
    print("DEMO: Streaming with Progress Indicator")
    print("=" * 60)
    print()

    agent = create_research_agent(readonly=True)

    # Show "thinking" message while waiting for first chunk
    print("Agent is thinking...", end="", flush=True)
    first_chunk = True

    async for chunk in agent.chat_stream("Describe the Projects table schema."):
        if first_chunk:
            # Clear the thinking message
            print("\r" + " " * 30 + "\r", end="", flush=True)
            print("Agent: ", end="", flush=True)
            first_chunk = False
        print(chunk, end="", flush=True)

    print("\n")


async def demo_streaming_with_rich() -> None:
    """Streaming with Rich console formatting."""
    if not RICH_AVAILABLE:
        print("\n[Skipping Rich demo - install with: pip install rich]")
        return

    console.print("\n" + "=" * 60)
    console.print("[bold cyan]DEMO: Streaming with Rich Formatting[/]")
    console.print("=" * 60)
    console.print()

    agent = create_research_agent(readonly=True)

    # Collect full response for markdown rendering
    full_response = ""

    console.print("[bold green]Agent:[/] ", end="")

    async for chunk in agent.chat_stream(
        "Give me a summary of the database schema. What entities are tracked?"
    ):
        full_response += chunk
        console.print(chunk, end="")

    console.print("\n")


async def demo_streaming_qa_session() -> None:
    """Interactive Q&A session with streaming responses."""
    print("\n" + "=" * 60)
    print("DEMO: Streaming Q&A Session")
    print("=" * 60)
    print()

    agent = create_research_agent(readonly=True)

    questions = [
        "How many departments are there?",
        "What project statuses exist in the system?",
        "Which department has the highest budget?",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n[Question {i}]: {question}")
        print("-" * 40)
        print("Answer: ", end="", flush=True)

        async for chunk in agent.chat_stream(question):
            print(chunk, end="", flush=True)

        print("\n")


async def demo_streaming_error_handling() -> None:
    """Demonstrate error handling during streaming."""
    print("\n" + "=" * 60)
    print("DEMO: Error Handling in Streams")
    print("=" * 60)
    print()

    agent = create_research_agent(readonly=True)

    try:
        chunks_received = 0
        async for chunk in agent.chat_stream("What is the total budget across all projects?"):
            print(chunk, end="", flush=True)
            chunks_received += 1

        print(f"\n\n[Received {chunks_received} chunks successfully]")

    except Exception as e:
        print(f"\n[Stream error: {e}]")
        print("[This is expected if there's a connection issue]")


async def demo_streaming_with_timing() -> None:
    """Streaming with timing information."""
    import time

    print("\n" + "=" * 60)
    print("DEMO: Streaming with Timing")
    print("=" * 60)
    print()

    agent = create_research_agent(readonly=True)

    start_time = time.time()
    first_token_time = None
    chunk_count = 0
    total_chars = 0

    print("Agent: ", end="", flush=True)

    async for chunk in agent.chat_stream(
        "List the top 3 researchers by publication count with their details."
    ):
        if first_token_time is None:
            first_token_time = time.time()

        print(chunk, end="", flush=True)
        chunk_count += 1
        total_chars += len(chunk)

    end_time = time.time()

    print("\n")
    print("-" * 40)
    print(f"Time to first token: {(first_token_time - start_time) * 1000:.0f}ms")
    print(f"Total time: {(end_time - start_time) * 1000:.0f}ms")
    print(f"Chunks received: {chunk_count}")
    print(f"Characters generated: {total_chars}")
    if end_time > first_token_time:
        tokens_per_sec = total_chars / (end_time - first_token_time)
        print(f"Generation speed: ~{tokens_per_sec:.0f} chars/sec")


async def main():
    """Run all streaming demonstrations."""
    setup_logging()

    print("=" * 60)
    print("Streaming Example - Local LLM Research Agent")
    print("=" * 60)
    print(f"\nProvider: {settings.default_provider}")
    print(f"Model: {settings.default_model}")

    try:
        await demo_basic_streaming()
        await demo_streaming_with_spinner()
        await demo_streaming_with_rich()
        await demo_streaming_qa_session()
        await demo_streaming_with_timing()
        await demo_streaming_error_handling()

        print("\n" + "=" * 60)
        print("All streaming demos completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure:")
        print("1. Your LLM provider is running (Ollama or Foundry Local)")
        print("2. MSSQL MCP Server is configured correctly")
        print("3. Environment variables are set in .env file")
        raise


if __name__ == "__main__":
    asyncio.run(main())
