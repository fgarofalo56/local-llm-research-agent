"""
Streamlit Web UI

Web-based chat interface for the research agent using Streamlit.
Provides a user-friendly way to interact with SQL Server data.
Supports both Ollama and Foundry Local as LLM providers.
"""

import asyncio
from typing import Any

import streamlit as st

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="Local LLM Research Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.agent.research_agent import ResearchAgent, ResearchAgentError  # noqa: E402
from src.providers import ProviderType, create_provider, get_available_providers  # noqa: E402
from src.utils.config import settings  # noqa: E402
from src.utils.database_manager import get_database_manager  # noqa: E402
from src.utils.export import (  # noqa: E402
    export_conversation_to_csv,
    export_response_data,
    export_to_json,
    export_to_markdown,
    generate_export_filename,
)
from src.utils.health import (  # noqa: E402
    HealthStatus,
    run_health_checks,
)


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


def check_provider_status(provider_type: str) -> dict:
    """
    Check provider connection status.

    Args:
        provider_type: 'ollama' or 'foundry_local'

    Returns:
        Dict with status info
    """
    async def _check():
        try:
            ptype = ProviderType(provider_type)
            provider = create_provider(provider_type=ptype)
            status = await provider.check_connection()
            models = await provider.list_models()
            return {
                "available": status.available,
                "model": status.model_name,
                "endpoint": status.endpoint,
                "error": status.error,
                "version": status.version,
                "models": models,
            }
        except Exception as e:
            return {"available": False, "error": str(e), "models": []}

    return run_async(_check())


def get_all_provider_statuses() -> list[dict]:
    """Get status for all providers."""
    return run_async(get_available_providers())


@st.cache_resource
def get_agent(
    provider_type: str = "ollama",
    model_name: str | None = None,
    readonly: bool = False,
    cache_enabled: bool = True,
    explain_mode: bool = False,
) -> ResearchAgent:
    """
    Get or create the research agent.

    Uses Streamlit's caching to persist the agent across reruns.

    Args:
        provider_type: LLM provider to use
        model_name: Model name/alias
        readonly: Enable read-only mode
        cache_enabled: Enable response caching
        explain_mode: Enable SQL explanation mode

    Returns:
        ResearchAgent instance
    """
    return ResearchAgent(
        provider_type=provider_type,
        model_name=model_name,
        readonly=readonly,
        cache_enabled=cache_enabled,
        explain_mode=explain_mode,
    )


def render_sidebar() -> dict[str, Any]:
    """
    Render the sidebar with configuration options.

    Returns:
        Dictionary of configuration options
    """
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Provider selection
        st.subheader("LLM Provider")
        provider_options = ["ollama", "foundry_local"]
        provider_labels = {"ollama": "Ollama", "foundry_local": "Foundry Local"}

        provider_type = st.selectbox(
            "Provider",
            options=provider_options,
            format_func=lambda x: provider_labels.get(x, x),
            index=provider_options.index(settings.llm_provider)
            if settings.llm_provider in provider_options
            else 0,
            help="Select the LLM inference provider",
        )

        # Check provider status
        status = check_provider_status(provider_type)

        if status["available"]:
            st.success(f"✅ {provider_labels[provider_type]}: Connected")
            if status.get("version"):
                st.caption(f"Version: {status['version']}")

            # Model selection from available models
            available_models = status.get("models", [])
            default_model = (
                settings.ollama_model
                if provider_type == "ollama"
                else settings.foundry_model
            )

            if available_models:
                model_name = st.selectbox(
                    "Model",
                    options=available_models,
                    index=next(
                        (i for i, m in enumerate(available_models) if default_model in m),
                        0,
                    ),
                    help="Select the model to use",
                )
            else:
                model_name = st.text_input(
                    "Model",
                    value=default_model,
                    help="Enter model name",
                )
        else:
            st.error(f"❌ {provider_labels[provider_type]}: Not available")
            if status.get("error"):
                st.caption(f"Error: {status['error'][:100]}")

            if provider_type == "ollama":
                st.info("Start Ollama: `ollama serve`")
            else:
                st.info("Install: `pip install foundry-local-sdk`")

            model_name = (
                settings.ollama_model
                if provider_type == "ollama"
                else settings.foundry_model
            )

        st.divider()

        # Database selection
        st.subheader("Database")
        db_manager = get_database_manager()
        databases = db_manager.list_databases()

        # Create database options
        db_options = [db["name"] for db in databases]
        db_labels = {
            db["name"]: f"{db['name']} ({db['database']})"
            for db in databases
        }

        # Find current active database index
        active_db = db_manager.active_name or "default"
        active_idx = db_options.index(active_db) if active_db in db_options else 0

        selected_db = st.selectbox(
            "Database",
            options=db_options,
            format_func=lambda x: db_labels.get(x, x),
            index=active_idx,
            help="Select database to query",
        )

        # Show database details
        db_config = db_manager.get_database(selected_db)
        if db_config:
            st.caption(f"Host: {db_config.host}")
            st.caption(f"Database: {db_config.database}")
            if db_config.readonly:
                st.caption("Mode: 🔒 Read-only")

        # Update active database if changed
        if selected_db != active_db:
            db_manager.set_active(selected_db)
            get_agent.clear()  # Clear cached agent to use new database
            st.rerun()

        # MCP status
        if settings.mcp_mssql_path:
            st.success("MCP: Configured", icon="✅")
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

        streaming = st.checkbox(
            "Streaming responses",
            value=True,
            help="Show responses as they are generated",
        )

        cache_enabled = st.checkbox(
            "Response caching",
            value=settings.cache_enabled,
            help="Cache responses for repeated queries",
        )

        explain_mode = st.checkbox(
            "SQL Explanation mode",
            value=False,
            help="Agent explains SQL queries step by step (educational)",
        )

        st.divider()

        # Actions
        st.subheader("Actions")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.messages = []
                # Clear cached agent to pick up new settings
                get_agent.clear()
                st.rerun()
        with col2:
            if st.button("🔄 Clear Cache", use_container_width=True):
                try:
                    agent = get_agent(
                        provider_type=provider_type,
                        model_name=model_name,
                        readonly=readonly,
                        cache_enabled=cache_enabled,
                    )
                    count = agent.clear_cache()
                    st.toast(f"Cache cleared ({count} entries)", icon="✅")
                except Exception:
                    st.toast("No cache to clear", icon="ℹ️")

        # Show cache stats if enabled
        if cache_enabled:
            try:
                agent = get_agent(
                    provider_type=provider_type,
                    model_name=model_name,
                    readonly=readonly,
                    cache_enabled=cache_enabled,
                )
                stats = agent.get_cache_stats()
                st.caption(
                    f"Cache: {stats.size}/{stats.max_size} entries | "
                    f"Hit rate: {stats.to_dict()['hit_rate']}"
                )
            except Exception:
                pass

        st.divider()

        # Export section
        st.subheader("Export")

        # Check if we have messages to export
        has_messages = bool(st.session_state.get("messages"))

        if has_messages:
            try:
                agent = get_agent(
                    provider_type=provider_type,
                    model_name=model_name,
                    readonly=readonly,
                    cache_enabled=cache_enabled,
                )

                col1, col2, col3 = st.columns(3)

                # JSON export
                with col1:
                    json_data = export_to_json(agent.conversation)
                    st.download_button(
                        label="JSON",
                        data=json_data,
                        file_name=generate_export_filename("chat", "json"),
                        mime="application/json",
                        use_container_width=True,
                    )

                # CSV export
                with col2:
                    csv_data = export_conversation_to_csv(agent.conversation)
                    st.download_button(
                        label="CSV",
                        data=csv_data,
                        file_name=generate_export_filename("chat", "csv"),
                        mime="text/csv",
                        use_container_width=True,
                    )

                # Markdown export
                with col3:
                    md_data = export_to_markdown(agent.conversation)
                    st.download_button(
                        label="MD",
                        data=md_data,
                        file_name=generate_export_filename("chat", "md"),
                        mime="text/markdown",
                        use_container_width=True,
                    )
            except Exception:
                st.caption("Export not available")
        else:
            st.caption("Start chatting to enable export")

        st.divider()

        # Info
        st.subheader("Info")
        active_db_config = db_manager.active
        if active_db_config:
            st.caption(f"Database: {active_db_config.database}")
            st.caption(f"Server: {active_db_config.host}")
        else:
            st.caption(f"Database: {settings.sql_database_name}")
            st.caption(f"Server: {settings.sql_server_host}")

        st.divider()

        # Health Check
        with st.expander("System Health", expanded=False):
            if st.button("Run Health Check", use_container_width=True):
                with st.spinner("Checking system health..."):
                    try:
                        health = run_async(run_health_checks(include_database=False))

                        # Overall status with color
                        status_colors = {
                            HealthStatus.HEALTHY: "green",
                            HealthStatus.UNHEALTHY: "red",
                            HealthStatus.DEGRADED: "orange",
                            HealthStatus.UNKNOWN: "gray",
                        }
                        status_icons = {
                            HealthStatus.HEALTHY: ":white_check_mark:",
                            HealthStatus.UNHEALTHY: ":x:",
                            HealthStatus.DEGRADED: ":warning:",
                            HealthStatus.UNKNOWN: ":grey_question:",
                        }

                        icon = status_icons.get(health.status, ":grey_question:")
                        color = status_colors.get(health.status, "gray")
                        st.markdown(
                            f"**Overall:** {icon} :{color}[{health.status.value.upper()}]"
                        )

                        # Component statuses
                        for comp in health.components:
                            comp_icon = status_icons.get(comp.status, ":grey_question:")
                            latency = f" ({comp.latency_ms:.0f}ms)" if comp.latency_ms else ""
                            st.caption(f"{comp_icon} **{comp.name}**: {comp.message}{latency}")

                    except Exception as e:
                        st.error(f"Health check failed: {e}")

        return {
            "provider_type": provider_type,
            "model_name": model_name,
            "readonly": readonly,
            "streaming": streaming,
            "cache_enabled": cache_enabled,
            "explain_mode": explain_mode,
            "provider_available": status["available"],
            "database": selected_db,
        }


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
                agent = get_agent(
                    provider_type=config["provider_type"],
                    model_name=config["model_name"],
                    readonly=config["readonly"],
                    cache_enabled=config.get("cache_enabled", True),
                    explain_mode=config.get("explain_mode", False),
                )

                if config.get("streaming", True):
                    # Streaming mode - display tokens as they arrive
                    response_placeholder = st.empty()
                    full_response = ""

                    async def stream_response():
                        nonlocal full_response
                        async for chunk in agent.chat_stream(prompt):
                            full_response += chunk
                            response_placeholder.markdown(full_response + "▌")

                    run_async(stream_response())
                    response_placeholder.markdown(full_response)
                    response = full_response
                else:
                    # Non-streaming mode - show spinner
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
    if not config["provider_available"]:
        provider_name = (
            "Ollama" if config["provider_type"] == "ollama" else "Foundry Local"
        )
        if config["provider_type"] == "ollama":
            st.error(
                f"⚠️ **{provider_name} is not running**\n\n"
                "Please start Ollama to use this application:\n"
                "```bash\n"
                "ollama serve\n"
                "```"
            )
        else:
            st.error(
                f"⚠️ **{provider_name} is not running**\n\n"
                "Install and start Foundry Local:\n"
                "```bash\n"
                "pip install foundry-local-sdk\n"
                "```\n"
                "Then use `FoundryLocalManager` in Python to start a model."
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
