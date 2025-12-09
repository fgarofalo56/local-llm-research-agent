#!/bin/bash
# =============================================================================
# Docker Entrypoint for Local LLM Research Agent
# =============================================================================

set -e

# Default values
MODE="${1:-cli}"

case "$MODE" in
    cli|chat)
        echo "Starting CLI chat interface..."
        exec python -m src.cli.chat "${@:2}"
        ;;
    ui|streamlit)
        echo "Starting Streamlit web interface..."
        exec streamlit run src/ui/streamlit_app.py \
            --server.port "${STREAMLIT_SERVER_PORT:-8501}" \
            --server.address "${STREAMLIT_SERVER_ADDRESS:-0.0.0.0}" \
            "${@:2}"
        ;;
    query)
        echo "Running single query..."
        exec python -m src.cli.chat query "${@:2}"
        ;;
    shell)
        echo "Starting shell..."
        exec /bin/bash
        ;;
    *)
        echo "Usage: docker run local-llm-agent [cli|ui|query|shell] [options]"
        echo ""
        echo "Modes:"
        echo "  cli, chat   - Interactive CLI chat (default)"
        echo "  ui          - Streamlit web interface"
        echo "  query       - Run a single query"
        echo "  shell       - Start a bash shell"
        echo ""
        echo "Examples:"
        echo "  docker run -it local-llm-agent cli"
        echo "  docker run -p 8501:8501 local-llm-agent ui"
        echo "  docker run local-llm-agent query 'What tables exist?'"
        exit 1
        ;;
esac
