import asyncio
from src.agent.core import ResearchAgent
from src.mcp.client import MCPClientManager

async def test():
    m = MCPClientManager()
    servers = [s.name for s in m.list_servers() if s.enabled]
    print(f'Enabled: {servers}')
    
    agent = ResearchAgent(
        provider_type='ollama',
        model_name='qwen3:30b',
        readonly=True,
        mcp_servers=servers
    )
    print(f'Toolsets loaded: {len(agent._active_toolsets)}')
    print(f'MCP servers configured: {agent._enabled_mcp_servers}')
    
    # Quick check agent initialization
    print(f'Agent type: {type(agent.agent).__name__}')
    print('SUCCESS: Agent initialized with all enabled MCP servers')

asyncio.run(test())
