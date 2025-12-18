"""
Settings Page - Streamlit Multi-Page App
Phase 2.1+ Application Settings UI

Features:
- LLM Provider selection (Ollama/Foundry Local)
- Model selection (dynamic from available models)
- Model parameters (temperature, top_p, max_tokens)
- Theme management
- Configuration testing
- System prompt customization
"""

import asyncio

import httpx
import streamlit as st

from src.providers import ProviderType, create_provider
from src.utils.config import settings

# Page configuration
st.set_page_config(
    page_title="Settings - Local LLM Research Agent",
    page_icon="⚙️",
    layout="wide",
)

# API base URL - try container name first (Docker), fall back to localhost
# Note: API_HOST=0.0.0.0 is for server binding, not client connections
import os
_api_host = os.environ.get("API_HOST", "localhost")
if _api_host == "0.0.0.0":
    _api_host = "localhost"  # 0.0.0.0 is bind address, use localhost for client
API_BASE_URL = f"http://{_api_host}:{settings.api_port}"


def run_async(coro):
    """Run async code in Streamlit's sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def check_provider(provider_type: str) -> dict:
    """Check provider connection status."""
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


async def test_provider_connection(provider_type: str, model: str) -> dict:
    """Test provider connection with a simple request."""
    try:
        ptype = ProviderType(provider_type)
        provider = create_provider(provider_type=ptype, model_name=model)

        import time

        start_time = time.time()

        # Simple test - just check connection
        status = await provider.check_connection()

        elapsed_ms = (time.time() - start_time) * 1000

        if status.available:
            return {
                "success": True,
                "message": f"Connected successfully to {status.model_name}",
                "response_time_ms": elapsed_ms,
                "version": status.version,
            }
        else:
            return {
                "success": False,
                "error": status.error or "Connection failed",
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def fetch_themes() -> dict:
    """Fetch themes from API."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{API_BASE_URL}/api/settings/themes",
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {"themes": [], "active_theme": None, "error": str(e)}


async def activate_theme(theme_name: str) -> dict:
    """Activate a theme via API."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/api/settings/themes/{theme_name}/activate",
                timeout=10.0,
            )
            response.raise_for_status()
            return {"success": True}
        except httpx.HTTPError as e:
            return {"success": False, "error": str(e)}


def render_provider_settings():
    """Render LLM provider settings section."""
    st.subheader("LLM Provider")

    # Initialize session state
    if "settings_provider" not in st.session_state:
        st.session_state.settings_provider = settings.llm_provider
    if "settings_model" not in st.session_state:
        st.session_state.settings_model = (
            settings.ollama_model if settings.llm_provider == "ollama" else settings.foundry_model
        )

    # Provider selection
    provider_options = ["ollama", "foundry_local"]
    provider_labels = {
        "ollama": "🦙 Ollama",
        "foundry_local": "🔧 Foundry Local",
    }

    col1, col2 = st.columns([2, 3])

    with col1:
        selected_provider = st.selectbox(
            "Provider",
            options=provider_options,
            format_func=lambda x: provider_labels.get(x, x),
            index=provider_options.index(st.session_state.settings_provider),
            help="Select the LLM inference provider",
            key="provider_select",
        )

    # Check provider status
    with st.spinner(f"Checking {provider_labels[selected_provider]}..."):
        status = run_async(check_provider(selected_provider))

    with col2:
        if status["available"]:
            st.success(f"✅ Connected (v{status.get('version', 'unknown')})")
        else:
            st.error("❌ Not available")
            if status.get("error"):
                st.caption(f"Error: {status['error'][:100]}")

    # Model selection
    st.markdown("#### Model Selection")

    if status["available"] and status.get("models"):
        available_models = status["models"]

        # Determine current model index
        current_model = st.session_state.settings_model
        model_index = 0
        if current_model in available_models:
            model_index = available_models.index(current_model)
        else:
            # Try partial match
            for i, m in enumerate(available_models):
                if current_model in m or m in current_model:
                    model_index = i
                    break

        selected_model = st.selectbox(
            "Model",
            options=available_models,
            index=model_index,
            help="Select the model to use for chat",
            key="model_select",
        )

        # Show model info
        st.caption(f"Selected: `{selected_model}`")
    else:
        selected_model = st.text_input(
            "Model",
            value=st.session_state.settings_model,
            help="Enter model name",
            key="model_input",
        )

        if selected_provider == "ollama":
            st.info("Start Ollama with: `ollama serve`")
        else:
            st.info(
                "**Foundry Local Setup:**\n"
                "1. Install: [Download from Microsoft](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/get-started)\n"
                "2. Start a model: `foundry model run phi-4`\n"
                "3. Or enable auto-start: Set `FOUNDRY_AUTO_START=true` in .env"
            )

    # Test connection button
    if st.button("🧪 Test Connection", type="secondary"):
        with st.spinner("Testing connection..."):
            result = run_async(test_provider_connection(selected_provider, selected_model))

        if result["success"]:
            st.success(f"✅ {result['message']}")
            st.caption(f"Response time: {result.get('response_time_ms', 0):.0f}ms")
        else:
            st.error(f"❌ Test failed: {result.get('error', 'Unknown error')}")

    # Update session state
    if selected_provider != st.session_state.settings_provider:
        st.session_state.settings_provider = selected_provider
    if selected_model != st.session_state.settings_model:
        st.session_state.settings_model = selected_model

    return selected_provider, selected_model


def render_model_parameters():
    """Render model parameters section."""
    st.subheader("Model Parameters")

    # Initialize session state for parameters
    if "model_temperature" not in st.session_state:
        st.session_state.model_temperature = 0.7
    if "model_top_p" not in st.session_state:
        st.session_state.model_top_p = 0.9
    if "model_max_tokens" not in st.session_state:
        st.session_state.model_max_tokens = 2048

    col1, col2, col3 = st.columns(3)

    with col1:
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=st.session_state.model_temperature,
            step=0.1,
            help="Higher = more creative, Lower = more focused",
            key="temp_slider",
        )
        st.session_state.model_temperature = temperature

    with col2:
        top_p = st.slider(
            "Top P",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.model_top_p,
            step=0.05,
            help="Nucleus sampling threshold",
            key="top_p_slider",
        )
        st.session_state.model_top_p = top_p

    with col3:
        max_tokens = st.number_input(
            "Max Tokens",
            min_value=1,
            max_value=32768,
            value=st.session_state.model_max_tokens,
            step=256,
            help="Maximum response length",
            key="max_tokens_input",
        )
        st.session_state.model_max_tokens = max_tokens

    # Show current settings
    st.caption(f"Current: temp={temperature}, top_p={top_p}, max_tokens={max_tokens}")

    return {"temperature": temperature, "top_p": top_p, "max_tokens": max_tokens}


def render_system_prompt():
    """Render system prompt configuration section."""
    st.subheader("System Prompt")

    # Default system prompt
    default_prompt = """You are a helpful research assistant with access to SQL Server databases.
You can query data, analyze results, and provide insights.
Always explain your reasoning and the SQL queries you generate."""

    # Initialize session state
    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = default_prompt

    system_prompt = st.text_area(
        "Custom System Prompt",
        value=st.session_state.system_prompt,
        height=150,
        help="Customize the agent's behavior and personality",
        key="system_prompt_input",
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Reset to Default", type="secondary"):
            st.session_state.system_prompt = default_prompt
            st.rerun()

    with col2:
        if system_prompt != st.session_state.system_prompt and st.button(
            "Save Changes", type="primary"
        ):
            st.session_state.system_prompt = system_prompt
            st.toast("System prompt saved", icon="✅")

    return system_prompt


def render_theme_settings():
    """Render theme settings section."""
    st.subheader("Theme")

    # Fetch themes
    result = run_async(fetch_themes())

    if "error" in result:
        st.warning(f"Could not load themes: {result['error']}")
        st.caption("Theme management requires the API server to be running")
        return

    themes = result.get("themes", [])
    active_theme = result.get("active_theme")

    if not themes:
        st.info("No themes configured. Using default Streamlit theme.")
        st.caption("Note: Streamlit themes are configured in `.streamlit/config.toml`")
        return

    # Theme selector
    theme_options = [t["name"] for t in themes]
    theme_labels = {t["name"]: t["display_name"] for t in themes}

    current_index = 0
    if active_theme and active_theme in theme_options:
        current_index = theme_options.index(active_theme)

    selected_theme = st.selectbox(
        "Select Theme",
        options=theme_options,
        format_func=lambda x: theme_labels.get(x, x),
        index=current_index,
        help="Choose the application theme",
        key="theme_select",
    )

    # Activate button
    if selected_theme != active_theme and st.button("Apply Theme", type="primary"):
        result = run_async(activate_theme(selected_theme))
        if result.get("success"):
            st.success(f"Theme '{selected_theme}' activated!")
            st.rerun()
        else:
            st.error(f"Failed: {result.get('error', 'Unknown error')}")


def render_current_config():
    """Render current configuration display."""
    st.subheader("Current Configuration")

    with st.expander("View Configuration", expanded=False):
        config_data = {
            "LLM Provider": settings.llm_provider,
            "Ollama Host": settings.ollama_host,
            "Ollama Model": settings.ollama_model,
            "Foundry Endpoint": settings.foundry_endpoint,
            "Foundry Model": settings.foundry_model,
            "SQL Server": f"{settings.sql_server_host}:{settings.sql_server_port}",
            "Database": settings.sql_database_name,
            "Auth Type": settings.sql_auth_type.value,
            "MCP Path": settings.mcp_mssql_path or "(not set)",
            "MCP Readonly": settings.mcp_mssql_readonly,
            "Redis URL": settings.redis_url,
            "Embedding Model": settings.embedding_model,
            "Chunk Size": settings.chunk_size,
            "Chunk Overlap": settings.chunk_overlap,
            "RAG Top K": settings.rag_top_k,
            "Upload Dir": settings.upload_dir,
            "Max Upload MB": settings.max_upload_size_mb,
            "Cache Enabled": settings.cache_enabled,
            "Debug": settings.debug,
        }

        for key, value in config_data.items():
            st.text(f"{key}: {value}")

        st.caption("Configuration is loaded from environment variables and .env file")


def main():
    """Main page entry point."""
    st.title("⚙️ Settings")
    st.caption("Configure LLM providers, models, and application settings")

    # Create tabs for different settings sections
    tab1, tab2, tab3, tab4 = st.tabs(["Provider", "Parameters", "System Prompt", "Config"])

    with tab1:
        render_provider_settings()
        st.divider()
        render_theme_settings()

    with tab2:
        render_model_parameters()

    with tab3:
        render_system_prompt()

    with tab4:
        render_current_config()


if __name__ == "__main__":
    main()
