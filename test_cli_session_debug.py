"""
Debug script to trace MCP session behavior in CLI.
Tests whether sessions are being reused or recreated.
"""
import asyncio
import logging
from src.agent.core import ResearchAgent
from src.mcp.server_manager import MCPServerManager
from rich.console import Console

# Enable DEBUG logging to see all HTTP requests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

console = Console()

async def debug_cli_session():
    """Test CLI-style session management with detailed logging."""
    console.print("\n[bold cyan]🔍 MCP Session Debug Test[/]\n")
    
    # Load MCP servers
    console.print("[yellow]Loading MCP servers...[/]")
    mcp_manager = MCPServerManager()
    await mcp_manager.load_servers()
    enabled_servers = [s for s in mcp_manager.servers if s.is_enabled]
    console.print(f"[green]✓ Loaded {len(enabled_servers)} enabled servers[/]\n")
    
    # Create agent
    console.print("[yellow]Creating agent...[/]")
    agent = ResearchAgent(mcp_manager=mcp_manager)
    console.print("[green]✓ Agent created[/]\n")
    
    # Enter agent context (should establish sessions ONCE)
    console.print("[bold yellow]>>> ENTERING AGENT CONTEXT <<<[/]")
    async with agent:
        console.print("[bold green]✓✓✓ MCP SESSIONS ESTABLISHED ✓✓✓[/]\n")
        
        # Send multiple messages
        messages = [
            "do you have access to tools?",
            "what tables are in the database?",
            "list all projects"
        ]
        
        for i, msg in enumerate(messages, 1):
            console.print(f"\n[bold cyan]{'='*60}[/]")
            console.print(f"[bold cyan]MESSAGE {i}: {msg}[/]")
            console.print(f"[bold cyan]{'='*60}[/]\n")
            
            console.print(f"[yellow]→ Sending message {i}...[/]")
            try:
                result = await agent.run(msg)
                console.print(f"[green]✓ Response received ({len(result)} chars)[/]")
                console.print(f"[dim]{result[:200]}...[/]" if len(result) > 200 else f"[dim]{result}[/]")
            except Exception as e:
                console.print(f"[red]✗ Error: {e}[/]")
        
        console.print(f"\n[bold yellow]>>> EXITING AGENT CONTEXT <<<[/]")
    
    console.print("[bold green]✓✓✓ MCP SESSIONS CLOSED ✓✓✓[/]\n")
    console.print("[bold cyan]Test complete - check logs above for POST requests[/]")
    console.print("[dim]Expected: 1 POST at context entry, then only tool call POSTs[/]")
    console.print("[dim]Bug symptom: POST on every message = new sessions[/]\n")

if __name__ == "__main__":
    asyncio.run(debug_cli_session())
