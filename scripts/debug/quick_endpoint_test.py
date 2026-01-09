import asyncio
import httpx

async def test():
    print("Testing MCP endpoints...")
    
    # Test Microsoft Docs
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(
                'https://learn.microsoft.com/api/mcp',
                json={'method': 'initialize', 'params': {}}
            )
            print(f'MS Docs POST: {r.status_code}')
    except Exception as e:
        print(f'MS Docs error: {e}')
    
    # Test Archon SSE
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(
                'http://localhost:8051/sse',
                headers={'Accept': 'text/event-stream'}
            )
            print(f'Archon SSE GET: {r.status_code}')
            if r.status_code == 200:
                print(f'Content-Type: {r.headers.get("content-type")}')
    except Exception as e:
        print(f'Archon error: {e}')

if __name__ == "__main__":
    asyncio.run(test())
