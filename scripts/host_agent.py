#!/usr/bin/env python3
"""
Host Agent Sidecar for Docker Service Management

A lightweight FastAPI service that runs on the host machine to start
Ollama and Foundry Local services when the main API runs in Docker.

The Docker container cannot start services on the host directly, so
it calls this agent instead.

Usage:
    python scripts/host_agent.py
    # Or with custom port:
    HOST_AGENT_PORT=5280 python scripts/host_agent.py

Endpoints:
    GET  /health         - Health check and service status
    GET  /status         - Simple status check
    POST /start/ollama   - Start Ollama service
    POST /start/foundry  - Start Foundry with model
"""

import asyncio
import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime
from typing import Any

try:
    import uvicorn
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, field_validator
except ImportError:
    print("Error: Required packages not installed.")
    print("Install with: pip install fastapi uvicorn pydantic")
    sys.exit(1)


# Configuration
HOST_AGENT_PORT = int(os.getenv("HOST_AGENT_PORT", "5280"))
HOST_AGENT_HOST = os.getenv("HOST_AGENT_HOST", "0.0.0.0")
FOUNDRY_DEFAULT_MODEL = os.getenv("FOUNDRY_MODEL", "phi-4")
FOUNDRY_PORT = int(os.getenv("FOUNDRY_PORT", "5272"))
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Track startup time
START_TIME = datetime.utcnow()

app = FastAPI(
    title="Host Agent Sidecar",
    description="Manages Ollama and Foundry Local services for Docker containers",
    version="1.0.0",
)

# Allow CORS from Docker containers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models
class StartResponse(BaseModel):
    """Response model for service start operations."""

    success: bool
    message: str
    service: str
    endpoint: str | None = None
    error: str | None = None


class FoundryStartRequest(BaseModel):
    """Request model for starting Foundry."""

    model: str | None = None

    @field_validator("model")
    @classmethod
    def validate_model_name(cls, v: str | None) -> str | None:
        """Validate model name to prevent command injection."""
        if v is None:
            return v
        # Only allow alphanumeric, hyphens, underscores, colons, and dots
        if not re.match(r"^[a-zA-Z0-9_\-:.]+$", v):
            raise ValueError("Invalid model name format")
        return v


class ServiceStatus(BaseModel):
    """Status of a single service."""

    name: str
    running: bool
    endpoint: str | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    uptime_seconds: float
    platform: str
    services: dict[str, ServiceStatus]


class StatusResponse(BaseModel):
    """Simple status response."""

    status: str
    agent: str
    port: int


# Helper functions
def is_windows() -> bool:
    """Check if running on Windows."""
    return platform.system() == "Windows"


async def check_ollama_running() -> tuple[bool, str | None]:
    """Check if Ollama is running."""
    try:
        import httpx

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_HOST}/api/version")
            if response.status_code == 200:
                return True, None
            return False, f"Unexpected status: {response.status_code}"
    except Exception as e:
        return False, str(e)


async def check_foundry_running() -> tuple[bool, str | None]:
    """Check if Foundry Local is running."""
    try:
        import httpx

        endpoint = f"http://127.0.0.1:{FOUNDRY_PORT}"
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{endpoint}/v1/models")
            if response.status_code == 200:
                return True, None
            return False, f"Unexpected status: {response.status_code}"
    except Exception as e:
        return False, str(e)


async def start_ollama_service() -> StartResponse:
    """Start Ollama service."""
    # Check if already running
    running, _ = await check_ollama_running()
    if running:
        return StartResponse(
            success=True,
            message="Ollama is already running",
            service="ollama",
            endpoint=OLLAMA_HOST,
        )

    # Check if ollama CLI is available
    ollama_path = shutil.which("ollama")
    if not ollama_path:
        return StartResponse(
            success=False,
            message="Ollama CLI not found in PATH",
            service="ollama",
            error="Please install Ollama from https://ollama.ai",
        )

    try:
        # Start ollama serve as background process
        if is_windows():
            # On Windows, use CREATE_NEW_PROCESS_GROUP and DETACHED_PROCESS
            creation_flags = (
                subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            )
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags,
            )
        else:
            # On Unix, use nohup and redirect to /dev/null
            subprocess.Popen(
                ["nohup", "ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

        # Wait for startup
        for _ in range(10):  # Wait up to 5 seconds
            await asyncio.sleep(0.5)
            running, _ = await check_ollama_running()
            if running:
                return StartResponse(
                    success=True,
                    message="Ollama started successfully",
                    service="ollama",
                    endpoint=OLLAMA_HOST,
                )

        return StartResponse(
            success=False,
            message="Ollama started but not responding yet",
            service="ollama",
            error="Service may still be initializing. Try again in a few seconds.",
        )

    except Exception as e:
        return StartResponse(
            success=False,
            message="Failed to start Ollama",
            service="ollama",
            error=str(e),
        )


async def start_foundry_service(model: str | None = None) -> StartResponse:
    """Start Foundry Local service."""
    model = model or FOUNDRY_DEFAULT_MODEL

    # Check if already running
    running, _ = await check_foundry_running()
    if running:
        return StartResponse(
            success=True,
            message=f"Foundry Local is already running",
            service="foundry",
            endpoint=f"http://127.0.0.1:{FOUNDRY_PORT}",
        )

    # Check if foundry CLI is available
    foundry_path = shutil.which("foundry")
    if not foundry_path:
        return StartResponse(
            success=False,
            message="Foundry CLI not found in PATH",
            service="foundry",
            error="Please install Foundry Local from Microsoft",
        )

    try:
        # Start foundry model run as background process
        cmd = ["foundry", "model", "run", model]

        if is_windows():
            creation_flags = (
                subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            )
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags,
            )
        else:
            subprocess.Popen(
                ["nohup"] + cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

        # Wait for startup (Foundry takes longer)
        for _ in range(20):  # Wait up to 10 seconds
            await asyncio.sleep(0.5)
            running, _ = await check_foundry_running()
            if running:
                return StartResponse(
                    success=True,
                    message=f"Foundry Local started with model: {model}",
                    service="foundry",
                    endpoint=f"http://127.0.0.1:{FOUNDRY_PORT}",
                )

        return StartResponse(
            success=False,
            message="Foundry started but not responding yet",
            service="foundry",
            error="Service may still be loading the model. Try again in a few seconds.",
        )

    except Exception as e:
        return StartResponse(
            success=False,
            message="Failed to start Foundry Local",
            service="foundry",
            error=str(e),
        )


# Routes
@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Simple status check to verify agent is running."""
    return StatusResponse(
        status="ok",
        agent="host-agent",
        port=HOST_AGENT_PORT,
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check with service status."""
    uptime = (datetime.utcnow() - START_TIME).total_seconds()

    # Check Ollama
    ollama_running, ollama_error = await check_ollama_running()
    ollama_status = ServiceStatus(
        name="ollama",
        running=ollama_running,
        endpoint=OLLAMA_HOST if ollama_running else None,
        error=ollama_error if not ollama_running else None,
    )

    # Check Foundry
    foundry_running, foundry_error = await check_foundry_running()
    foundry_status = ServiceStatus(
        name="foundry",
        running=foundry_running,
        endpoint=f"http://127.0.0.1:{FOUNDRY_PORT}" if foundry_running else None,
        error=foundry_error if not foundry_running else None,
    )

    overall_status = "healthy" if (ollama_running or foundry_running) else "degraded"

    return HealthResponse(
        status=overall_status,
        uptime_seconds=round(uptime, 2),
        platform=platform.system(),
        services={
            "ollama": ollama_status,
            "foundry": foundry_status,
        },
    )


@app.post("/start/ollama", response_model=StartResponse)
async def start_ollama():
    """Start Ollama service on the host."""
    return await start_ollama_service()


@app.post("/start/foundry", response_model=StartResponse)
async def start_foundry(request: FoundryStartRequest | None = None):
    """Start Foundry Local service on the host."""
    model = request.model if request else None
    return await start_foundry_service(model)


def main():
    """Run the host agent server."""
    print(f"Starting Host Agent Sidecar on {HOST_AGENT_HOST}:{HOST_AGENT_PORT}")
    print(f"Platform: {platform.system()}")
    print(f"Foundry Port: {FOUNDRY_PORT}")
    print(f"Ollama Host: {OLLAMA_HOST}")
    print()
    print("Endpoints:")
    print(f"  GET  http://localhost:{HOST_AGENT_PORT}/status")
    print(f"  GET  http://localhost:{HOST_AGENT_PORT}/health")
    print(f"  POST http://localhost:{HOST_AGENT_PORT}/start/ollama")
    print(f"  POST http://localhost:{HOST_AGENT_PORT}/start/foundry")
    print()
    print("Press Ctrl+C to stop")
    print("-" * 50)

    uvicorn.run(
        app,
        host=HOST_AGENT_HOST,
        port=HOST_AGENT_PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
