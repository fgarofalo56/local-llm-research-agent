"""
Basic Chat Example

Demonstrates how to create and use the research agent with Ollama and MCP.
This example shows the fundamental pattern used throughout the application.

Prerequisites:
1. Ollama running locally with qwen2.5:7b-instruct model
2. MSSQL MCP Server setup and configured
3. Environment variables set in .env file
"""

import asyncio
from dataclasses import dataclass

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.mcp import MCPServerStdio


@dataclass
class ChatConfig:
    """Configuration for the chat agent."""
    
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b-instruct"
    mssql_mcp_path: str = ""  # Set this to your MSSQL MCP path
    sql_server: str = "localhost"
    sql_database: str = "your_database"


SYSTEM_PROMPT = """You are a helpful SQL data analyst assistant. You have access to a SQL Server 
database through MCP tools. Use these tools to answer questions about the data.

When the user asks about data:
1. First use list_tables to see what tables are available
2. Use describe_table to understand the schema
3. Use read_data to query the actual data
4. Present the results in a clear, helpful format

Always explain what you're doing and provide context for your answers."""


async def create_agent(config: ChatConfig) -> Agent:
    """Create and configure the research agent."""
    
    # Configure Ollama as OpenAI-compatible model
    model = OpenAIModel(
        model_name=config.ollama_model,
        base_url=f"{config.ollama_host}/v1",
        api_key="ollama"  # Ollama doesn't validate API keys
    )
    
    # Configure MSSQL MCP Server
    mssql_server = MCPServerStdio(
        command="node",
        args=[config.mssql_mcp_path],
        env={
            "SERVER_NAME": config.sql_server,
            "DATABASE_NAME": config.sql_database,
            "TRUST_SERVER_CERTIFICATE": "true",
            "READONLY": "true"  # Safe mode for examples
        },
        timeout=30
    )
    
    # Create agent with MCP tools
    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        toolsets=[mssql_server]
    )
    
    return agent


async def chat_loop(agent: Agent):
    """Run an interactive chat loop."""
    
    print("\n🔍 Local LLM Research Agent")
    print("=" * 40)
    print("Chat with your SQL Server data.")
    print("Type 'quit' to exit.\n")
    
    async with agent:  # Manage MCP server lifecycle
        while True:
            try:
                # Get user input
                user_input = input("\nYou: ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ("quit", "exit", "q"):
                    print("\nGoodbye!")
                    break
                
                # Run the agent
                print("\nAgent: ", end="", flush=True)
                result = await agent.run(user_input)
                print(result.output)
                
            except KeyboardInterrupt:
                print("\n\nInterrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")


async def main():
    """Main entry point."""
    
    # Configuration - in practice, load from environment
    config = ChatConfig(
        ollama_host="http://localhost:11434",
        ollama_model="qwen2.5:7b-instruct",
        mssql_mcp_path="/path/to/SQL-AI-samples/MssqlMcp/Node/dist/index.js",
        sql_server="localhost",
        sql_database="your_database"
    )
    
    # Create agent
    agent = await create_agent(config)
    
    # Run chat loop
    await chat_loop(agent)


if __name__ == "__main__":
    asyncio.run(main())
