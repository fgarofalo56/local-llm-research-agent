"""
Test Script: Three Chat Methods
================================

Demonstrates and tests all three chat methods:
1. chat() - Simple text response with caching
2. chat_stream() - Streaming chunks for UX
3. chat_with_details() - Full metadata response

Run this to verify session management and see the differences.
"""

import asyncio
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.agent.core import ResearchAgent
from src.mcp.client import MCPClientManager

console = Console()


async def test_method_1_basic_chat(agent: ResearchAgent):
    """Test Method 1: chat() - Basic text response with caching."""
    console.print("\n" + "="*70)
    console.print(Panel.fit(
        "[bold cyan]Method 1: chat()[/]\n"
        "[dim]Simple text response with caching[/]",
        border_style="cyan"
    ))
    
    message = "What tables are in the database?"
    
    # First call - will hit LLM
    console.print(f"\n[yellow]→[/] Sending: [dim]{message}[/]")
    start = time.time()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Processing...", total=None)
        response = await agent.chat(message)
        progress.update(task, completed=True)
    
    duration = (time.time() - start) * 1000
    
    console.print(f"\n[green]✓[/] Response ({duration:.0f}ms):")
    console.print(Panel(response[:300] + "..." if len(response) > 300 else response))
    
    # Second call - should hit cache (instant)
    console.print(f"\n[yellow]→[/] Sending SAME message again (testing cache):")
    start = time.time()
    
    cached_response = await agent.chat(message)
    cache_duration = (time.time() - start) * 1000
    
    console.print(f"[green]✓[/] Cached response ({cache_duration:.0f}ms) - [bold green]{duration/cache_duration:.0f}x faster![/]")
    console.print(f"[dim]Response matches: {response == cached_response}[/]")
    
    return {
        "method": "chat()",
        "duration_ms": duration,
        "cached_duration_ms": cache_duration,
        "response_length": len(response),
    }


async def test_method_2_streaming(agent: ResearchAgent):
    """Test Method 2: chat_stream() - Streaming chunks for UX."""
    console.print("\n" + "="*70)
    console.print(Panel.fit(
        "[bold magenta]Method 2: chat_stream()[/]\n"
        "[dim]AsyncIterator yielding text chunks[/]",
        border_style="magenta"
    ))
    
    message = "List all researchers"
    
    console.print(f"\n[yellow]→[/] Sending: [dim]{message}[/]")
    console.print("[green]✓[/] Streaming response:\n")
    console.print("[dim]" + "-"*70 + "[/]")
    
    start = time.time()
    chunk_count = 0
    full_response = ""
    
    # Stream the response
    async for chunk in agent.chat_stream(message):
        console.print(chunk, end="", style="cyan")
        full_response += chunk
        chunk_count += 1
        await asyncio.sleep(0.02)  # Simulate typing delay for visual effect
    
    console.print()  # New line after streaming
    console.print("[dim]" + "-"*70 + "[/]")
    
    duration = (time.time() - start) * 1000
    
    # Get stats after streaming
    stats = agent.get_last_response_stats()
    
    console.print(f"\n[green]✓[/] Streaming complete:")
    console.print(f"  • Duration: {duration:.0f}ms")
    console.print(f"  • Chunks: {chunk_count}")
    console.print(f"  • Total length: {len(full_response)} chars")
    if stats.get("token_usage"):
        tokens = stats["token_usage"]
        console.print(f"  • Tokens: {tokens.total_tokens} (input: {tokens.input_tokens}, output: {tokens.output_tokens})")
    
    return {
        "method": "chat_stream()",
        "duration_ms": duration,
        "chunk_count": chunk_count,
        "response_length": len(full_response),
        "token_usage": stats.get("token_usage"),
    }


async def test_method_3_detailed(agent: ResearchAgent):
    """Test Method 3: chat_with_details() - Full metadata response."""
    console.print("\n" + "="*70)
    console.print(Panel.fit(
        "[bold yellow]Method 3: chat_with_details()[/]\n"
        "[dim]AgentResponse with full metadata[/]",
        border_style="yellow"
    ))
    
    message = "Count how many projects are active"
    
    console.print(f"\n[yellow]→[/] Sending: [dim]{message}[/]")
    
    start = time.time()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Processing...", total=None)
        response = await agent.chat_with_details(message)
        progress.update(task, completed=True)
    
    actual_duration = (time.time() - start) * 1000
    
    # Create metadata table
    table = Table(title="AgentResponse Metadata", border_style="yellow")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    
    table.add_row("Success", "✓ Yes" if response.success else "✗ No")
    table.add_row("Model", response.model)
    table.add_row("Duration (reported)", f"{response.duration_ms:.0f}ms")
    table.add_row("Duration (actual)", f"{actual_duration:.0f}ms")
    table.add_row("Response Length", f"{len(response.content)} chars")
    table.add_row("Tool Calls", str(len(response.tool_calls)))
    
    if response.token_usage:
        table.add_row(
            "Token Usage",
            f"{response.token_usage.total_tokens} "
            f"({response.token_usage.input_tokens} in, "
            f"{response.token_usage.output_tokens} out)"
        )
    
    if response.error:
        table.add_row("Error", f"[red]{response.error}[/]")
    
    console.print()
    console.print(table)
    
    console.print(f"\n[green]✓[/] Response content:")
    console.print(Panel(response.content[:300] + "..." if len(response.content) > 300 else response.content))
    
    return {
        "method": "chat_with_details()",
        "duration_ms": response.duration_ms,
        "model": response.model,
        "response_length": len(response.content),
        "token_usage": response.token_usage,
        "success": response.success,
    }


async def main():
    """Run all three test methods."""
    console.print(Panel.fit(
        "[bold white]Testing Three Chat Methods[/]\n"
        "[dim]Demonstrates chat(), chat_stream(), and chat_with_details()[/]",
        title="🧪 Test Suite",
        border_style="bold blue"
    ))
    
    # Initialize agent with MCP servers
    console.print("\n[cyan]Initializing agent...[/]")
    
    mcp_manager = MCPClientManager()
    enabled_servers = [s.name for s in mcp_manager.list_servers() if s.enabled]
    
    console.print(f"[dim]MCP servers: {', '.join(enabled_servers)}[/]")
    
    agent = ResearchAgent(mcp_servers=enabled_servers)
    
    results = []
    
    # CRITICAL: Enter agent context ONCE for all tests
    console.print("\n[bold green]>>> ENTERING AGENT CONTEXT (MCP sessions established) <<<[/]")
    
    async with agent:
        console.print("[green]✓ MCP sessions established and ready[/]\n")
        
        try:
            # Test all three methods
            results.append(await test_method_1_basic_chat(agent))
            results.append(await test_method_2_streaming(agent))
            results.append(await test_method_3_detailed(agent))
            
        except Exception as e:
            console.print(f"\n[red]✗ Error during tests: {e}[/]")
            raise
    
    console.print("\n[bold green]>>> EXITING AGENT CONTEXT (MCP sessions closed) <<<[/]")
    
    # Summary table
    console.print("\n" + "="*70)
    summary = Table(title="📊 Summary Comparison", border_style="bold blue")
    summary.add_column("Method", style="cyan", no_wrap=True)
    summary.add_column("Duration", justify="right", style="yellow")
    summary.add_column("Response Length", justify="right", style="magenta")
    summary.add_column("Special Features", style="white")
    
    for result in results:
        special = ""
        if result["method"] == "chat()":
            special = f"Cache: {result['cached_duration_ms']:.0f}ms"
        elif result["method"] == "chat_stream()":
            special = f"{result['chunk_count']} chunks"
        elif result["method"] == "chat_with_details()":
            special = f"Metadata: {result['token_usage'].total_tokens if result.get('token_usage') else 0} tokens"
        
        summary.add_row(
            result["method"],
            f"{result['duration_ms']:.0f}ms",
            f"{result['response_length']} chars",
            special
        )
    
    console.print()
    console.print(summary)
    console.print()
    
    # Key insights
    console.print(Panel(
        "[bold white]Key Insights:[/]\n\n"
        "1. [cyan]chat()[/] - Best for APIs, has caching (see speed boost!)\n"
        "2. [magenta]chat_stream()[/] - Best for CLI/UI, smooth typing effect\n"
        "3. [yellow]chat_with_details()[/] - Best for monitoring, full metadata\n\n"
        "[dim]All three methods shared the SAME MCP session (established once)[/]",
        title="💡 Conclusion",
        border_style="bold green"
    ))


if __name__ == "__main__":
    asyncio.run(main())
