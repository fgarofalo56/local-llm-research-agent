#!/bin/bash
# =============================================================================
# check-ports.sh
# Pre-flight port conflict detection for Local LLM Research Agent
#
# Checks all configured host ports against:
#   1. Running Docker containers (via docker ps --filter publish=PORT)
#   2. Host processes listening on those ports
#
# Usage:
#   ./docker/check-ports.sh          # Check with defaults / .env values
#   ./docker/check-ports.sh --fix    # Auto-suggest and write free ports to .env
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"
FIX_MODE=false

if [ "$1" = "--fix" ]; then
    FIX_MODE=true
fi

# ---------------------------------------------------------------------------
# Load .env if it exists (simple parser — handles KEY=VALUE, skips comments)
# ---------------------------------------------------------------------------
if [ -f "$ENV_FILE" ]; then
    while IFS='=' read -r key value; do
        # Skip comments and blank lines
        [[ "$key" =~ ^[[:space:]]*# ]] && continue
        [[ -z "$key" ]] && continue
        # Remove surrounding quotes from value
        value="${value%\"}"
        value="${value#\"}"
        value="${value%\'}"
        value="${value#\'}"
        # Remove inline comments
        value="${value%%#*}"
        # Trim whitespace
        value="$(echo "$value" | xargs)"
        key="$(echo "$key" | xargs)"
        # Only export if not already set in environment
        if [ -n "$key" ] && [ -z "${!key}" ]; then
            export "$key=$value" 2>/dev/null || true
        fi
    done < "$ENV_FILE"
fi

# ---------------------------------------------------------------------------
# Port definitions: VAR_NAME|DEFAULT_PORT|SERVICE_DESCRIPTION
# ---------------------------------------------------------------------------
declare -a PORT_DEFS=(
    "MSSQL_PORT|1433|SQL Server 2022 (Sample DB)"
    "BACKEND_DB_PORT|1434|SQL Server 2025 (Backend)"
    "API_PORT|8000|FastAPI Backend"
    "STREAMLIT_PORT|8501|Streamlit UI"
    "FRONTEND_PORT|5173|React Frontend"
    "REDIS_PORT|6379|Redis Stack"
    "REDIS_INSIGHT_PORT|8001|RedisInsight GUI"
    "SUPERSET_PORT|8088|Apache Superset"
)

# ---------------------------------------------------------------------------
# Helpers — use docker ps --filter publish=PORT (reliable, no string parsing)
# ---------------------------------------------------------------------------

# Check if a port is used by a running Docker container (excluding our own)
# Returns the conflicting container name, or empty string
check_docker_port() {
    local port=$1
    local containers
    containers=$(docker ps --filter "publish=${port}" --format "{{.Names}}" 2>/dev/null)

    # Filter out our own project containers
    while IFS= read -r name; do
        [ -z "$name" ] && continue
        case "$name" in
            local-agent-*) continue ;;  # Skip our own containers
            *) echo "$name"; return 0 ;;
        esac
    done <<< "$containers"

    return 1
}

# Check if a port is used by one of OUR OWN Docker containers
is_own_container_port() {
    local port=$1
    local containers
    containers=$(docker ps --filter "publish=${port}" --format "{{.Names}}" 2>/dev/null)

    while IFS= read -r name; do
        [ -z "$name" ] && continue
        case "$name" in
            local-agent-*) return 0 ;;  # Yes, it's ours
        esac
    done <<< "$containers"

    return 1
}

# Check if a port is in use on the host (non-Docker process)
check_host_port() {
    local port=$1
    if command -v ss &>/dev/null; then
        ss -tlnH 2>/dev/null | grep -qE ":${port}\b" && return 0
    elif command -v netstat &>/dev/null; then
        netstat -tln 2>/dev/null | grep -qE ":${port}\b" && return 0
        # Windows netstat via Git Bash
        netstat -an 2>/dev/null | grep -i "listening" | grep -qE ":${port} " && return 0
    fi
    return 1
}

# Check if a port is in use by ANYTHING (Docker or host process)
is_port_in_use() {
    local port=$1

    # Check ALL Docker containers (including our own) for free port search
    local containers
    containers=$(docker ps --filter "publish=${port}" --format "{{.Names}}" 2>/dev/null)
    if [ -n "$containers" ]; then
        return 0  # in use
    fi

    # Check host processes
    if check_host_port "$port"; then
        return 0  # in use
    fi

    return 1  # free
}

# Find the next available port starting AFTER the given port
find_free_port() {
    local start_port=$1
    local port=$((start_port + 1))
    local max_port=$((start_port + 100))

    while [ "$port" -le "$max_port" ]; do
        if ! is_port_in_use "$port"; then
            echo "$port"
            return 0
        fi
        port=$((port + 1))
    done

    echo ""
    return 1
}

# ---------------------------------------------------------------------------
# Main check
# ---------------------------------------------------------------------------

echo ""
echo "============================================================"
echo "  Port Conflict Check - Local LLM Research Agent"
echo "============================================================"
echo ""

if [ -f "$ENV_FILE" ]; then
    echo "  Using .env: $ENV_FILE"
else
    echo "  No .env found, using defaults from docker-compose.yml"
fi
echo ""

HAS_CONFLICTS=false
declare -a FIXES=()

printf "  %-22s %-6s %-10s %s\n" "SERVICE" "PORT" "STATUS" "DETAILS"
printf "  %-22s %-6s %-10s %s\n" "----------------------" "------" "----------" "----------------------------"

for def in "${PORT_DEFS[@]}"; do
    IFS='|' read -r var_name default_port desc <<< "$def"
    configured_port="${!var_name:-$default_port}"

    # Check Docker containers (excluding our own)
    conflicting_container=$(check_docker_port "$configured_port")

    if [ -n "$conflicting_container" ]; then
        HAS_CONFLICTS=true
        printf "  %-22s %-6s %-10s %s\n" "$desc" "$configured_port" "CONFLICT" "Container: $conflicting_container"

        if $FIX_MODE; then
            free_port=$(find_free_port "$configured_port")
            if [ -n "$free_port" ]; then
                FIXES+=("$var_name=$free_port  # was $configured_port, conflict: $conflicting_container")
                printf "  %-22s %-6s %-10s %s\n" "" "" "-> FIX" "Will use port $free_port"
            fi
        fi
    elif check_host_port "$configured_port"; then
        # Netstat detected the port, but it might be our own Docker container
        # (Docker maps ports to the host, so netstat sees them as LISTENING)
        if is_own_container_port "$configured_port"; then
            printf "  %-22s %-6s %-10s %s\n" "$desc" "$configured_port" "OK" "(our own container)"
            continue
        fi
        HAS_CONFLICTS=true
        printf "  %-22s %-6s %-10s %s\n" "$desc" "$configured_port" "CONFLICT" "Port in use by host process"

        if $FIX_MODE; then
            free_port=$(find_free_port "$configured_port")
            if [ -n "$free_port" ]; then
                FIXES+=("$var_name=$free_port  # was $configured_port, conflict: host-process")
                printf "  %-22s %-6s %-10s %s\n" "" "" "-> FIX" "Will use port $free_port"
            fi
        fi
    else
        printf "  %-22s %-6s %-10s %s\n" "$desc" "$configured_port" "OK" ""
    fi
done

echo ""

# ---------------------------------------------------------------------------
# Apply fixes to .env if in fix mode
# ---------------------------------------------------------------------------
if $FIX_MODE && [ ${#FIXES[@]} -gt 0 ]; then
    echo "------------------------------------------------------------"
    echo "  Applying port fixes to .env..."
    echo "------------------------------------------------------------"

    # Create .env from .env.example if it doesn't exist
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f "$PROJECT_ROOT/.env.example" ]; then
            cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
            echo "  Created .env from .env.example"
        else
            touch "$ENV_FILE"
            echo "  Created empty .env"
        fi
    fi

    for fix in "${FIXES[@]}"; do
        var_name="${fix%%=*}"
        full_line="$fix"

        # Check if the variable already exists in .env
        if grep -q "^${var_name}=" "$ENV_FILE" 2>/dev/null; then
            # Update existing line
            sed -i "s|^${var_name}=.*|${full_line}|" "$ENV_FILE"
            echo "  Updated: $full_line"
        else
            # Append new line
            echo "$full_line" >> "$ENV_FILE"
            echo "  Added:   $full_line"
        fi
    done

    echo ""
    echo "  .env updated. You can now start containers without conflicts."
    echo ""
elif $HAS_CONFLICTS; then
    echo "------------------------------------------------------------"
    echo "  CONFLICTS DETECTED!"
    echo "------------------------------------------------------------"
    echo ""
    echo "  Options to resolve:"
    echo ""
    echo "  1. Auto-fix: Run with --fix flag to auto-assign free ports:"
    echo "       ./docker/check-ports.sh --fix"
    echo ""
    echo "  2. Manual: Edit .env and change the conflicting port variables:"
    echo "       Example: API_PORT=8200  (instead of 8000)"
    echo ""
    echo "  3. Stop conflicting containers first:"
    echo "       docker stop <container-name>"
    echo ""
    exit 1
else
    echo "  All ports are available. Safe to start containers."
    echo ""
fi
