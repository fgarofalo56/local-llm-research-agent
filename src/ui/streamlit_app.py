"""
Streamlit Web UI

Web-based chat interface for the research agent using Streamlit.
Provides a user-friendly way to interact with SQL Server data.
"""

import asyncio
from typing import Any

import httpx
import streamlit as st

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="Local LLM Research Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.agent.research_agent import ResearchAgent, ResearchAgentError  # noqa: E402
from src.utils.config import settings  # noqa: E402


def run_async(coro: Any) -> Any:
    """
    Run async code in Streamlit's sync context.

    Args:
        coro: Coroutine to execute

    Returns:
        Result of the coroutine
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def check_ollama_status() -> tuple[bool, list[str]]:
    """
    Check Ollama connection and available models.

    Returns:
        Tuple of (is_connected, model_list)
    """
    try:
        response = httpx.get(f"{settings.ollama_host}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return True, [m.get("name", "") for m in models]
    except Exception:
        pass
    return False, []


@st.cache_resource
def get_agent(readonly: bool = False) -> ResearchAgent:
    """
    Get or create the research agent.

    Uses Streamlit's caching to persist the agent across reruns.

    Args:
        readonly: Enable read-only mode

    Returns:
        ResearchAgent instance
    """
    return ResearchAgent(readonly=readonly)


def render_sidebar() -> dict[str, Any]:
    """
    Render the sidebar with configuration options.

    Returns:
        Dictionary of configuration options
    """
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Connection status
        st.subheader("Status")
        ollama_ok, models = check_ollama_status()

        if ollama_ok:
            st.success("Ollama: Connected")
            if settings.ollama_model in " ".join(models):
                st.success(f"Model: {settings.ollama_model}")
            else:
                st.warning(f"Model '{settings.ollama_model}' may not be available")
        else:
            st.error("Ollama: Not connected")
            st.info("Start Ollama with: `ollama serve`")

        if settings.mcp_mssql_path:
            st.success("MCP: Configured")
        else:
            st.warning("MCP: Not configured")
            st.info("Set MCP_MSSQL_PATH in .env")

        st.divider()

        # Options
        st.subheader("Options")
        readonly = st.checkbox(
            "Read-only mode",
            value=settings.mcp_mssql_readonly,
            help="Prevent data modifications",
        )

        st.divider()

        # Actions
        st.subheader("Actions")
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            if "agent" in st.session_state:
                st.session_state.agent.clear_history()
            st.rerun()

        st.divider()

        # Info
        st.subheader("Info")
        st.caption(f"Database: {settings.sql_database_name}")
        st.caption(f"Server: {settings.sql_server_host}")

        return {"readonly": readonly}


def render_chat_interface(config: dict[str, Any]) -> None:
    """
    Render the main chat interface.

    Args:
        config: Configuration from sidebar
    """
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about your data..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            try:
                agent = get_agent(readonly=config["readonly"])

                with st.spinner("Thinking..."):
                    response = run_async(agent.chat(prompt))

                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

            except ResearchAgentError as e:
                error_msg = f"**Error:** {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

            except Exception as e:
                error_msg = f"**Unexpected error:** {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})


def render_welcome() -> None:
    """Render welcome message when chat is empty."""
    st.markdown(
        """
        ## 👋 Welcome to the Local LLM Research Agent!

        I can help you explore and analyze your SQL Server data using natural language.

        ### Try asking:
        - "What tables are in the database?"
        - "Describe the structure of the Users table"
        - "Show me the top 10 orders"
        - "How many customers do we have?"

        ### Features:
        - 🔒 **100% Local** - All processing happens on your machine
        - 💬 **Natural Language** - No SQL knowledge required
        - 🔍 **Smart Analysis** - AI-powered data exploration
        - ⚡ **Fast** - Direct database connection via MCP

        Type a question below to get started!
        """
    )


def main() -> None:
    """Main application entry point."""
    # Header
    st.title("🔍 Local LLM Research Agent")
    st.caption("Chat with your SQL Server data using natural language")

    # Render sidebar and get config
    config = render_sidebar()

    # Check prerequisites
    ollama_ok, _ = check_ollama_status()
    if not ollama_ok:
        st.error(
            "⚠️ **Ollama is not running**\n\n"
            "Please start Ollama to use this application:\n"
            "```bash\n"
            "ollama serve\n"
            "```"
        )
        return

    if not settings.mcp_mssql_path:
        st.warning(
            "⚠️ **MCP not configured**\n\n"
            "SQL Server tools are not available. "
            "Set `MCP_MSSQL_PATH` in your `.env` file to enable database access."
        )

    # Show welcome or chat
    if not st.session_state.get("messages"):
        render_welcome()

    # Render chat interface
    render_chat_interface(config)


if __name__ == "__main__":
    main()
