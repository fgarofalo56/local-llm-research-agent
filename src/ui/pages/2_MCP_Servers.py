"""
MCP Servers Page - Streamlit Multi-Page App
Phase 2.1+ MCP Server Management UI

Features:
- List configured MCP servers
- Enable/disable servers
- Add new MCP servers (stdio/http)
- View available tools per server
- Delete custom servers
"""

import asyncio
import json

import httpx
import streamlit as st

from src.utils.config import settings

# Page configuration
st.set_page_config(
    page_title="MCP Servers - Local LLM Research Agent",
    page_icon="🔌",
    layout="wide",
)

# API base URL
API_BASE_URL = f"http://localhost:{settings.api_port}"


def run_async(coro):
    """Run async code in Streamlit's sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def fetch_mcp_servers() -> dict:
    """Fetch MCP servers from API."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{API_BASE_URL}/api/mcp",
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {"servers": [], "total": 0, "error": str(e)}


async def toggle_server(server_id: str, enable: bool) -> dict:
    """Enable or disable an MCP server."""
    endpoint = "enable" if enable else "disable"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/api/mcp/{server_id}/{endpoint}",
                timeout=10.0,
            )
            response.raise_for_status()
            return {"success": True}
        except httpx.HTTPError as e:
            return {"success": False, "error": str(e)}


async def create_mcp_server(data: dict) -> dict:
    """Create a new MCP server configuration."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/api/mcp",
                json=data,
                timeout=10.0,
            )
            response.raise_for_status()
            return {"success": True, "server": response.json()}
        except httpx.HTTPError as e:
            error_detail = str(e)
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_detail = e.response.json().get("detail", str(e))
                except Exception:
                    # Ignore JSON parsing errors - error_detail retains the str(e) fallback
                    pass
            return {"success": False, "error": error_detail}


async def delete_mcp_server(server_id: str) -> dict:
    """Delete an MCP server configuration."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"{API_BASE_URL}/api/mcp/{server_id}",
                timeout=10.0,
            )
            response.raise_for_status()
            return {"success": True}
        except httpx.HTTPError as e:
            error_detail = str(e)
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_detail = e.response.json().get("detail", str(e))
                except Exception:
                    # Ignore JSON parsing errors - error_detail retains the str(e) fallback
                    pass
            return {"success": False, "error": error_detail}


def get_status_indicator(status: str, enabled: bool) -> str:
    """Get status indicator for MCP server."""
    if not enabled:
        return "⚫ Disabled"
    if status == "connected":
        return "🟢 Connected"
    elif status == "error":
        return "🔴 Error"
    else:
        return "🟡 Disconnected"


def render_server_card(server: dict):
    """Render a single MCP server card."""
    with st.container():
        col1, col2, col3 = st.columns([3, 2, 1])

        with col1:
            st.markdown(f"### {server['name']}")
            st.caption(f"ID: `{server['id']}` | Type: `{server['type']}`")
            if server.get('description'):
                st.caption(server['description'])

        with col2:
            st.markdown(get_status_indicator(server.get('status', 'unknown'), server['enabled']))
            if server['type'] == 'stdio':
                if server.get('command'):
                    st.caption(f"Command: `{server['command']}`")
            elif server['type'] == 'http':
                if server.get('url'):
                    st.caption(f"URL: `{server['url']}`")

        with col3:
            # Enable/Disable toggle
            new_state = st.toggle(
                "Enabled",
                value=server['enabled'],
                key=f"toggle_{server['id']}",
                help="Enable or disable this MCP server",
            )

            # Handle toggle change
            if new_state != server['enabled']:
                result = run_async(toggle_server(server['id'], new_state))
                if result['success']:
                    st.toast(f"Server {'enabled' if new_state else 'disabled'}", icon="✅")
                    st.rerun()
                else:
                    st.error(f"Failed: {result.get('error', 'Unknown error')}")

            # Delete button (only for non-built-in servers)
            if not server.get('built_in', False):
                if st.button("🗑️ Delete", key=f"delete_{server['id']}", help="Delete this server"):
                    st.session_state[f"confirm_delete_server_{server['id']}"] = True

        # Show tools if available
        if server.get('tools') and server['enabled']:
            with st.expander(f"Available Tools ({len(server['tools'])})"):
                for tool in server['tools']:
                    st.markdown(f"- `{tool}`")

        # Deletion confirmation
        if st.session_state.get(f"confirm_delete_server_{server['id']}"):
            st.warning(f"Are you sure you want to delete '{server['name']}'?")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("Yes, delete", key=f"confirm_yes_server_{server['id']}", type="primary"):
                    result = run_async(delete_mcp_server(server['id']))
                    if result['success']:
                        st.toast("Server deleted", icon="✅")
                        del st.session_state[f"confirm_delete_server_{server['id']}"]
                        st.rerun()
                    else:
                        st.error(f"Failed: {result.get('error', 'Unknown error')}")
            with col_no:
                if st.button("Cancel", key=f"confirm_no_server_{server['id']}"):
                    del st.session_state[f"confirm_delete_server_{server['id']}"]
                    st.rerun()

        st.divider()


def render_add_server_form():
    """Render the form to add a new MCP server."""
    with st.expander("➕ Add New MCP Server", expanded=False), st.form("add_server_form"):
        st.markdown("### Configure New MCP Server")

        # Basic info
        col1, col2 = st.columns(2)
        with col1:
            server_id = st.text_input(
                "Server ID",
                placeholder="my-server",
                help="Unique identifier (lowercase, no spaces)",
            )
        with col2:
            server_name = st.text_input(
                "Display Name",
                placeholder="My Server",
                help="Human-readable name",
            )

        description = st.text_area(
            "Description",
            placeholder="Optional description of what this server provides",
            height=80,
        )

        # Server type
        server_type = st.selectbox(
            "Server Type",
            options=["stdio", "http"],
            help="stdio: Run a local command | http: Connect to HTTP endpoint",
        )

        # Type-specific fields
        if server_type == "stdio":
            command = st.text_input(
                "Command",
                placeholder="node",
                help="Command to execute (e.g., 'node', 'python')",
            )
            args = st.text_input(
                "Arguments",
                placeholder="/path/to/server.js",
                help="Space-separated arguments for the command",
            )
            env_vars = st.text_area(
                "Environment Variables (JSON)",
                placeholder='{"KEY": "value"}',
                help="Optional environment variables as JSON object",
                height=80,
            )
            url = None
        else:
            command = None
            args = ""
            env_vars = ""
            url = st.text_input(
                "Server URL",
                placeholder="http://localhost:8080",
                help="HTTP endpoint URL for the MCP server",
            )

        enabled = st.checkbox("Enable immediately", value=True)

        submitted = st.form_submit_button("Add Server", type="primary")

        if submitted:
            # Validate
            if not server_id or not server_name:
                st.error("Server ID and Name are required")
            elif server_type == "stdio" and not command:
                st.error("Command is required for stdio servers")
            elif server_type == "http" and not url:
                st.error("URL is required for HTTP servers")
            else:
                # Parse environment variables
                env = {}
                if env_vars:
                    try:
                        env = json.loads(env_vars)
                    except json.JSONDecodeError:
                        st.error("Invalid JSON in environment variables")
                        return

                # Parse args
                args_list = args.split() if args else []

                # Build data
                data = {
                    "id": server_id,
                    "name": server_name,
                    "description": description,
                    "type": server_type,
                    "enabled": enabled,
                }

                if server_type == "stdio":
                    data["command"] = command
                    data["args"] = args_list
                    data["env"] = env
                else:
                    data["url"] = url

                # Create server
                result = run_async(create_mcp_server(data))
                if result['success']:
                    st.success("Server added successfully!")
                    st.rerun()
                else:
                    st.error(f"Failed: {result.get('error', 'Unknown error')}")


def render_server_list():
    """Render the list of MCP servers."""
    # Fetch servers
    with st.spinner("Loading MCP servers..."):
        result = run_async(fetch_mcp_servers())

    if "error" in result:
        st.error(f"Failed to load MCP servers: {result['error']}")
        st.info("Make sure the API server is running at " + API_BASE_URL)
        return

    servers = result.get("servers", [])

    if not servers:
        st.info("No MCP servers configured. Add a server using the form above.")
        return

    # Separate built-in and custom servers
    builtin_servers = [s for s in servers if s.get('built_in', False)]
    custom_servers = [s for s in servers if not s.get('built_in', False)]

    # Built-in servers
    if builtin_servers:
        st.subheader("Built-in Servers")
        for server in builtin_servers:
            render_server_card(server)

    # Custom servers
    if custom_servers:
        st.subheader("Custom Servers")
        for server in custom_servers:
            render_server_card(server)


def main():
    """Main page entry point."""
    st.title("🔌 MCP Server Management")
    st.caption("Configure and manage Model Context Protocol (MCP) servers")

    # Add server form
    render_add_server_form()

    st.divider()

    # Server list with refresh
    col1, col2 = st.columns([4, 1])
    with col1:
        st.subheader("Configured Servers")
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    render_server_list()

    # Help section
    with st.expander("ℹ️ About MCP Servers"):
        st.markdown("""
        **Model Context Protocol (MCP)** servers provide tools and capabilities to the AI agent.

        ### Server Types
        - **stdio**: Runs a local command (e.g., Node.js or Python script)
        - **http**: Connects to an HTTP endpoint

        ### Built-in Servers
        The MSSQL server is built-in and provides SQL Server database tools like:
        - `list_tables` - List all tables
        - `describe_table` - Get table schema
        - `read_data` - Query data
        - And more...

        ### Adding Custom Servers
        You can add custom MCP servers to extend the agent's capabilities.
        For example, a web search server or a custom API integration.
        """)


if __name__ == "__main__":
    main()
