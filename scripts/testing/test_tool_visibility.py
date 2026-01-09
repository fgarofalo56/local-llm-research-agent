import asyncio
from src.agent.core import ResearchAgent
from src.mcp.client import MCPClientManager

async def test():
    print("Initializing agent with all enabled MCP servers...\n")
    
    m = MCPClientManager()
    servers = [s.name for s in m.list_servers() if s.enabled]
    
    agent = ResearchAgent(
        provider_type='ollama',
        model_name='qwen3:30b',
        readonly=True,
        mcp_servers=servers,
        cache_enabled=False  # Disable cache to get fresh responses
    )
    
    print(f"Loaded {len(agent._active_toolsets)} toolsets\n")
    print("=" * 70)
    
    # Test different question phrasings
    questions = [
        "What functions or tools do you have? List them all.",
        "Can you run correlation_analysis?",
        "Can you perform time series analysis?",
        "List every function you can call."
    ]
    
    for i, q in enumerate(questions, 1):
        print(f"\nQuestion {i}: {q}")
        print("-" * 70)
        response = await agent.chat(q)
        print(response)
        print()

asyncio.run(test())
