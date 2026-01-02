# Custom MCP Server Development Guide

> **Learn how to build your own MCP servers to extend AI agent capabilities**

---

## Table of Contents

- [Introduction](#introduction)
- [MCP Protocol Basics](#mcp-protocol-basics)
- [Server Implementations](#server-implementations)
- [Python MCP Server](#python-mcp-server)
- [Node.js MCP Server](#nodejs-mcp-server)
- [Tool Development](#tool-development)
- [Testing Your Server](#testing-your-server)
- [Integration with Pydantic AI](#integration-with-pydantic-ai)
- [Best Practices](#best-practices)
- [Example Servers](#example-servers)

---

## Introduction

Custom MCP servers enable you to extend AI agents with domain-specific capabilities. This guide covers building MCP servers in both Python and Node.js.

### When to Build a Custom Server

Build a custom MCP server when you need to:

- **Access proprietary APIs** - Internal services, custom databases
- **Implement business logic** - Domain-specific operations
- **Bridge legacy systems** - Connect to existing infrastructure
- **Create specialized tools** - Industry-specific operations
- **Optimize performance** - Custom caching, batching

### Server Architecture

```
┌─────────────────────────────────────────┐
│         AI Agent (Pydantic AI)          │
└──────────────────┬──────────────────────┘
                   │
                   │ MCP Protocol (JSON-RPC)
                   │
┌──────────────────▼──────────────────────┐
│          Your Custom MCP Server         │
│  ┌──────────────────────────────────┐   │
│  │  Tool 1: list_resources()        │   │
│  │  Tool 2: search_data()           │   │
│  │  Tool 3: process_request()       │   │
│  └──────────────────────────────────┘   │
└──────────────────┬──────────────────────┘
                   │
                   ▼
         Your Service/Database/API
```

---

## MCP Protocol Basics

### Core Concepts

| Concept | Description | Example |
|---------|-------------|---------|
| **Tools** | Functions AI can call | `search_files(query)` |
| **Resources** | Data AI can read | File contents, documents |
| **Prompts** | Pre-defined instructions | Query templates |
| **Sampling** | AI-generated content | Text, code completion |

### Communication Protocol

MCP uses **JSON-RPC 2.0** over stdio or HTTP:

**Request (from client to server):**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

**Response (from server to client):**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "search_files",
        "description": "Search files by name or content",
        "inputSchema": {
          "type": "object",
          "properties": {
            "query": {"type": "string"}
          },
          "required": ["query"]
        }
      }
    ]
  }
}
```

### Required Methods

Every MCP server must implement:

| Method | Purpose | Returns |
|--------|---------|---------|
| `initialize` | Server initialization | Server capabilities |
| `tools/list` | List available tools | Array of tool definitions |
| `tools/call` | Execute a tool | Tool result |

---

## Server Implementations

### Implementation Comparison

| Feature | Python | Node.js |
|---------|--------|---------|
| **Ecosystem** | Rich data science libs | Large package registry |
| **Performance** | Good for CPU-bound | Excellent for I/O |
| **Async Support** | asyncio | Native promises |
| **Type Safety** | Pydantic, type hints | TypeScript |
| **Learning Curve** | Moderate | Moderate |
| **Best For** | ML/data processing | API integration |

---

## Python MCP Server

### Setup

```bash
# Create project directory
mkdir my-mcp-server
cd my-mcp-server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install MCP SDK
pip install mcp anthropic-sdk pydantic
```

### Basic Server Structure

Create `server.py`:

```python
"""
Custom MCP Server Example
Provides file system search capabilities
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
    ListToolsResult,
)
from pydantic import BaseModel, Field


# Tool input schemas
class SearchFilesInput(BaseModel):
    """Input for search_files tool."""
    query: str = Field(..., description="Search query (filename or content)")
    path: str = Field(default=".", description="Directory to search")
    max_results: int = Field(default=10, description="Maximum results")


# Create server instance
app = Server("my-filesystem-server")


@app.list_tools()
async def list_tools() -> ListToolsResult:
    """List available tools."""
    return ListToolsResult(
        tools=[
            Tool(
                name="search_files",
                description="Search for files by name or content",
                inputSchema=SearchFilesInput.model_json_schema(),
            ),
            Tool(
                name="read_file",
                description="Read contents of a file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File path to read"
                        }
                    },
                    "required": ["path"]
                },
            ),
        ]
    )


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
    """Execute a tool."""

    if name == "search_files":
        # Parse and validate input
        input_data = SearchFilesInput(**arguments)

        # Perform search
        results = await search_files_impl(
            query=input_data.query,
            path=input_data.path,
            max_results=input_data.max_results
        )

        # Return results
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(results, indent=2)
                )
            ]
        )

    elif name == "read_file":
        path = Path(arguments["path"])

        if not path.exists():
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: File not found: {path}"
                    )
                ],
                isError=True
            )

        content = path.read_text()
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=content
                )
            ]
        )

    else:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error: Unknown tool: {name}"
                )
            ],
            isError=True
        )


async def search_files_impl(query: str, path: str, max_results: int) -> list[dict]:
    """Implementation of file search."""
    results = []
    search_path = Path(path)

    # Search by filename
    for file_path in search_path.rglob("*"):
        if not file_path.is_file():
            continue

        if query.lower() in file_path.name.lower():
            results.append({
                "path": str(file_path),
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "match_type": "filename"
            })

            if len(results) >= max_results:
                break

    return results


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="my-filesystem-server",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
```

### Running the Python Server

```bash
# Run directly
python server.py

# Or make executable
chmod +x server.py
./server.py
```

---

## Node.js MCP Server

### Setup

```bash
# Create project directory
mkdir my-mcp-server
cd my-mcp-server

# Initialize npm project
npm init -y

# Install dependencies
npm install @modelcontextprotocol/sdk zod

# Install TypeScript (optional but recommended)
npm install -D typescript @types/node
npx tsc --init
```

### Basic Server Structure

Create `server.ts` (or `server.js`):

```typescript
/**
 * Custom MCP Server Example
 * Provides file system search capabilities
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';
import * as fs from 'fs/promises';
import * as path from 'path';

// Input schemas using Zod
const SearchFilesSchema = z.object({
  query: z.string().describe('Search query (filename or content)'),
  path: z.string().default('.').describe('Directory to search'),
  maxResults: z.number().default(10).describe('Maximum results'),
});

const ReadFileSchema = z.object({
  path: z.string().describe('File path to read'),
});

// Create server
const server = new Server(
  {
    name: 'my-filesystem-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List tools handler
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'search_files',
        description: 'Search for files by name or content',
        inputSchema: {
          type: 'object',
          properties: {
            query: { type: 'string', description: 'Search query' },
            path: { type: 'string', description: 'Directory to search' },
            maxResults: { type: 'number', description: 'Maximum results' },
          },
          required: ['query'],
        },
      } as Tool,
      {
        name: 'read_file',
        description: 'Read contents of a file',
        inputSchema: {
          type: 'object',
          properties: {
            path: { type: 'string', description: 'File path to read' },
          },
          required: ['path'],
        },
      } as Tool,
    ],
  };
});

// Call tool handler
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'search_files': {
        const input = SearchFilesSchema.parse(args);
        const results = await searchFiles(
          input.query,
          input.path,
          input.maxResults
        );

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(results, null, 2),
            },
          ],
        };
      }

      case 'read_file': {
        const input = ReadFileSchema.parse(args);
        const content = await fs.readFile(input.path, 'utf-8');

        return {
          content: [
            {
              type: 'text',
              text: content,
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${error instanceof Error ? error.message : String(error)}`,
        },
      ],
      isError: true,
    };
  }
});

// Search implementation
async function searchFiles(
  query: string,
  searchPath: string,
  maxResults: number
): Promise<Array<{ path: string; name: string; size: number; matchType: string }>> {
  const results: Array<{ path: string; name: string; size: number; matchType: string }> = [];

  async function search(dir: string) {
    if (results.length >= maxResults) return;

    const entries = await fs.readdir(dir, { withFileTypes: true });

    for (const entry of entries) {
      if (results.length >= maxResults) break;

      const fullPath = path.join(dir, entry.name);

      if (entry.isDirectory()) {
        await search(fullPath);
      } else if (entry.name.toLowerCase().includes(query.toLowerCase())) {
        const stats = await fs.stat(fullPath);
        results.push({
          path: fullPath,
          name: entry.name,
          size: stats.size,
          matchType: 'filename',
        });
      }
    }
  }

  await search(searchPath);
  return results;
}

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('MCP server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
```

### Compile and Run

```bash
# Compile TypeScript
npx tsc

# Run the server
node dist/server.js
```

---

## Tool Development

### Tool Design Principles

| Principle | Description | Example |
|-----------|-------------|---------|
| **Single purpose** | One tool, one function | `search_files` not `file_operations` |
| **Clear naming** | Descriptive, consistent names | `create_user` not `add` |
| **Validated inputs** | Schema validation | Use Pydantic/Zod |
| **Detailed descriptions** | Help AI understand usage | Include examples |
| **Error handling** | Graceful failure | Return error messages |

### Input Schema Best Practices

```python
# Good: Detailed schema with descriptions
class SearchInput(BaseModel):
    """Search files in a directory."""

    query: str = Field(
        ...,
        description="Search query. Can be filename pattern or content snippet.",
        examples=["*.py", "import pandas", "TODO"]
    )

    case_sensitive: bool = Field(
        default=False,
        description="Whether search should be case-sensitive"
    )

    max_results: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results to return (1-100)"
    )

# Bad: Minimal schema
class SearchInput(BaseModel):
    q: str  # What does 'q' mean?
    max: int = 10  # No validation
```

### Tool Output Guidelines

```python
# Good: Structured, parseable output
return CallToolResult(
    content=[
        TextContent(
            type="text",
            text=json.dumps({
                "results": results,
                "total_found": len(results),
                "search_time_ms": elapsed_time,
                "query": query
            }, indent=2)
        )
    ]
)

# Bad: Unstructured output
return CallToolResult(
    content=[
        TextContent(
            type="text",
            text=f"Found {len(results)} results for {query}"
        )
    ]
)
```

---

## Testing Your Server

### Manual Testing

```bash
# Test with stdio (Python)
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python server.py

# Test with Node.js
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | node dist/server.js
```

### Automated Testing (Python)

Create `test_server.py`:

```python
import asyncio
import json
import subprocess
from typing import Any

async def test_server():
    """Test MCP server functionality."""

    # Start server process
    process = subprocess.Popen(
        ['python', 'server.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        # Test 1: List tools
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }

        process.stdin.write(json.dumps(request) + '\n')
        process.stdin.flush()

        response = process.stdout.readline()
        result = json.loads(response)

        assert 'result' in result
        assert 'tools' in result['result']
        print(f"✅ List tools: Found {len(result['result']['tools'])} tools")

        # Test 2: Call tool
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "search_files",
                "arguments": {
                    "query": "test",
                    "path": ".",
                    "max_results": 5
                }
            }
        }

        process.stdin.write(json.dumps(request) + '\n')
        process.stdin.flush()

        response = process.stdout.readline()
        result = json.loads(response)

        assert 'result' in result
        print("✅ Call tool: Success")

    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_server())
```

Run tests:

```bash
python test_server.py
```

---

## Integration with Pydantic AI

### Configuration

Add your server to `mcp_config.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "python",
      "args": ["E:/path/to/my-mcp-server/server.py"],
      "env": {
        "SEARCH_PATH": "${DEFAULT_SEARCH_PATH:-./data}"
      }
    }
  }
}
```

### Environment Variables

Add to `.env`:

```bash
DEFAULT_SEARCH_PATH=E:/Repos/MyProject/data
```

### Use in Agent

```python
from pydantic_ai import Agent
from src.mcp.client import MCPClientManager

# Load your custom server
mcp_manager = MCPClientManager()
fs_server = mcp_manager.get_server_from_config("filesystem")

# Create agent with custom server
agent = Agent(
    model=model,
    system_prompt="You are a file system assistant.",
    toolsets=[fs_server]
)

# Use it
async with agent:
    result = await agent.run("Search for Python files in the data directory")
    print(result.output)
```

---

## Best Practices

### Security

| Practice | Priority | Implementation |
|----------|----------|----------------|
| **Input validation** | 🔴 Critical | Use Pydantic/Zod schemas |
| **Path sanitization** | 🔴 Critical | Validate file paths |
| **Least privilege** | 🔴 Critical | Minimal permissions |
| **Rate limiting** | 🟡 Medium | Limit requests per minute |
| **Audit logging** | 🟡 Medium | Log all tool calls |

### Error Handling

```python
# Good: Detailed error handling
try:
    result = await perform_operation(args)
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(result))]
    )
except FileNotFoundError as e:
    return CallToolResult(
        content=[TextContent(type="text", text=f"File not found: {e}")],
        isError=True
    )
except PermissionError as e:
    return CallToolResult(
        content=[TextContent(type="text", text=f"Permission denied: {e}")],
        isError=True
    )
except Exception as e:
    # Log unexpected errors
    logger.error(f"Unexpected error: {e}", exc_info=True)
    return CallToolResult(
        content=[TextContent(type="text", text=f"Internal error: {str(e)}")],
        isError=True
    )
```

### Performance

- **Async operations** - Use async/await for I/O
- **Connection pooling** - Reuse database connections
- **Caching** - Cache expensive operations
- **Timeouts** - Set reasonable timeouts
- **Streaming** - Stream large responses

### Documentation

Document your server in code:

```python
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    """
    Execute a tool.

    Available tools:
    - search_files: Search for files by name or content
      Args:
        - query (str): Search query
        - path (str): Directory to search
        - max_results (int): Maximum results

    - read_file: Read file contents
      Args:
        - path (str): File path

    Returns:
        CallToolResult with tool output or error
    """
    # Implementation...
```

---

## Example Servers

### 1. Database Query Server

```python
"""Database query MCP server."""

import asyncpg
from mcp.server import Server
from mcp.types import Tool, CallToolResult, TextContent

app = Server("database-server")

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    if name == "query_database":
        conn = await asyncpg.connect(
            host='localhost',
            database='mydb',
            user='user',
            password='password'
        )

        try:
            results = await conn.fetch(arguments['query'])
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps([dict(r) for r in results], indent=2)
                )]
            )
        finally:
            await conn.close()
```

### 2. API Integration Server

```python
"""REST API integration MCP server."""

import httpx
from mcp.server import Server

app = Server("api-server")

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    if name == "call_api":
        async with httpx.AsyncClient() as client:
            response = await client.get(
                arguments['url'],
                headers=arguments.get('headers', {}),
                params=arguments.get('params', {})
            )

            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=response.text
                )]
            )
```

### 3. Document Processing Server

```python
"""Document processing MCP server."""

from pathlib import Path
from pypdf import PdfReader
from mcp.server import Server

app = Server("document-server")

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    if name == "extract_pdf_text":
        reader = PdfReader(arguments['path'])
        text = "\n\n".join(page.extract_text() for page in reader.pages)

        return CallToolResult(
            content=[TextContent(type="text", text=text)]
        )
```

---

## Resources

### Official Documentation

- [MCP Specification](https://modelcontextprotocol.io/docs)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)

### Project Documentation

- [MCP Overview](README.md)
- [MSSQL Server Setup](mssql-server-setup.md)
- [Pydantic AI MCP Integration](../reference/pydantic_ai_mcp.md)

### Example Servers

- [MSSQL MCP Server](https://github.com/Azure-Samples/SQL-AI-samples/tree/main/MssqlMcp)
- [Filesystem MCP Server](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)
- [GitHub MCP Server](https://github.com/modelcontextprotocol/servers/tree/main/src/github)

---

## Next Steps

1. **Design your tools** - Plan what functionality to expose
2. **Choose implementation** - Python or Node.js
3. **Build and test** - Start with one tool
4. **Integrate with agent** - Add to mcp_config.json
5. **Iterate** - Add more tools based on needs

---

*Last Updated: December 2024*
