# Foundry Local Management Guide

> **Complete guide to installing, configuring, and managing Microsoft Foundry Local for the Local LLM Research Agent**

---

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Model Management](#model-management)
- [Configuration](#configuration)
- [SDK Usage](#sdk-usage)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)
- [Comparison with Ollama](#comparison-with-ollama)

---

## Overview

Microsoft Foundry Local is a local AI inference runtime that allows you to run language models on your machine. It provides an OpenAI-compatible API and integrates with the Azure AI ecosystem.

### Key Features

| Feature | Description |
|---------|-------------|
| OpenAI Compatible | Standard API interface |
| Azure Integration | Works with Azure AI Foundry |
| Python SDK | Programmatic control |
| Auto Model Download | Downloads models on first use |
| Tool Calling | Supported by Phi-4 and other models |

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10/11, macOS, Linux | Windows 11, macOS 14+ |
| RAM | 8GB | 16GB+ |
| Storage | 10GB | 30GB+ |
| Python | 3.10+ | 3.11+ |

### Supported Models

| Model Alias | Full Name | Size | Best For |
|-------------|-----------|------|----------|
| `phi-4` | Microsoft Phi-4 | ~8GB | General reasoning, tool calling |
| `phi-3-mini` | Phi-3 Mini | ~2GB | Lightweight tasks |
| `phi-3-small` | Phi-3 Small | ~4GB | Balanced performance |
| `mistral-7b` | Mistral 7B | ~4GB | General purpose |
| `qwen2.5-0.5b` | Qwen 2.5 0.5B | ~1GB | Very lightweight |

---

## Installation

### Prerequisites

```bash
# Ensure Python 3.10+
python --version

# Ensure pip is up to date
pip install --upgrade pip
```

### Install SDK

```bash
# Install Foundry Local SDK
pip install foundry-local-sdk

# Or with the research agent
pip install -e ".[foundry]"
```

### Verify Installation

```python
from foundry_local import FoundryLocalManager

# This will download the model on first run
manager = FoundryLocalManager("phi-4")
print(f"Endpoint: {manager.endpoint}")
print(f"API Key: {manager.api_key}")
```

---

## Model Management

### Starting a Model

**Using SDK (Recommended):**
```python
from foundry_local import FoundryLocalManager

# Start with specific model
manager = FoundryLocalManager("phi-4")

# Access endpoint info
print(manager.endpoint)  # http://127.0.0.1:53760
```

**Using CLI (if available):**
```bash
# Check foundry-local-sdk documentation for CLI options
python -m foundry_local --model phi-4
```

### Available Models

```python
from foundry_local import FoundryLocalManager

# List available model aliases
# Common aliases: phi-4, phi-3-mini, phi-3-small, mistral-7b, qwen2.5-0.5b
```

### Model Download

Models are downloaded automatically on first use:

```python
# First run downloads ~8GB for phi-4
manager = FoundryLocalManager("phi-4")

# Download location varies by OS:
# Windows: %LOCALAPPDATA%\FoundryLocal\models
# macOS: ~/Library/Application Support/FoundryLocal/models
# Linux: ~/.local/share/FoundryLocal/models
```

### Switching Models

```python
# Stop current model and start another
manager1 = FoundryLocalManager("phi-4")
# ... use phi-4 ...
del manager1  # Stops the model

manager2 = FoundryLocalManager("mistral-7b")
# ... use mistral-7b ...
```

---

## Configuration

### Environment Variables

Configure Foundry Local in `.env`:

```bash
# Select Foundry Local as provider
LLM_PROVIDER=foundry_local

# Foundry Local endpoint (default)
FOUNDRY_ENDPOINT=http://127.0.0.1:53760

# Model alias to use
FOUNDRY_MODEL=phi-4

# Auto-start model when agent initializes
FOUNDRY_AUTO_START=false
```

### Agent Configuration

```python
from src.agent.research_agent import create_research_agent

# Use Foundry Local with default settings
agent = create_research_agent(provider_type="foundry_local")

# Specify model
agent = create_research_agent(
    provider_type="foundry_local",
    model_name="phi-4",
)
```

### Provider Configuration

```python
from src.providers.foundry import FoundryLocalProvider

# Manual configuration
provider = FoundryLocalProvider(
    model_name="phi-4",
    endpoint="http://127.0.0.1:53760",
)

# Using SDK auto-start
provider = FoundryLocalProvider.start_with_sdk("phi-4")
```

---

## SDK Usage

### Basic Usage

```python
from foundry_local import FoundryLocalManager

# Initialize and start model
manager = FoundryLocalManager("phi-4")

# Get connection info
endpoint = manager.endpoint  # http://127.0.0.1:53760
api_key = manager.api_key    # Generated API key

# Use with OpenAI client
from openai import OpenAI

client = OpenAI(
    base_url=f"{endpoint}/v1",
    api_key=api_key,
)

response = client.chat.completions.create(
    model="phi-4",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

### With Research Agent

```python
from src.providers.foundry import FoundryLocalProvider
from src.agent.research_agent import ResearchAgent

# Start Foundry Local with SDK
provider = FoundryLocalProvider.start_with_sdk("phi-4")

# Create agent with the provider
agent = ResearchAgent(provider=provider)

# Use the agent
response = await agent.chat("What tables are in the database?")
```

### Auto-Start Configuration

```bash
# In .env
FOUNDRY_AUTO_START=true
FOUNDRY_MODEL=phi-4
```

When `FOUNDRY_AUTO_START=true`, the agent will automatically start Foundry Local on initialization.

---

## Performance Optimization

### Model Selection

| Model | Speed | Quality | Memory |
|-------|-------|---------|--------|
| `qwen2.5-0.5b` | Fastest | Basic | ~2GB |
| `phi-3-mini` | Fast | Good | ~4GB |
| `phi-4` | Medium | Best | ~8GB |
| `mistral-7b` | Medium | Good | ~8GB |

### Memory Management

```python
# Use lightweight model for simple tasks
manager = FoundryLocalManager("qwen2.5-0.5b")

# Use phi-4 for complex reasoning
manager = FoundryLocalManager("phi-4")
```

### GPU Acceleration

Foundry Local automatically uses available GPU acceleration:
- **NVIDIA CUDA**: Automatically detected
- **Apple Metal**: Automatically detected on Apple Silicon
- **CPU Fallback**: Used when no GPU available

### Concurrent Usage

```python
# Single model instance recommended
# Multiple concurrent requests are supported
# But multiple model instances will compete for resources
```

---

## Troubleshooting

### Common Issues

#### SDK Import Error

**Symptoms:** `ModuleNotFoundError: No module named 'foundry_local'`

**Solution:**
```bash
pip install foundry-local-sdk
```

#### Connection Refused

**Symptoms:** Cannot connect to Foundry Local endpoint

**Solutions:**
```python
# Ensure model is started
from foundry_local import FoundryLocalManager
manager = FoundryLocalManager("phi-4")

# Check endpoint
print(manager.endpoint)

# Verify with curl
# curl http://127.0.0.1:53760/v1/models
```

#### Model Download Failed

**Symptoms:** Download errors or timeouts

**Solutions:**
```bash
# Check internet connection
ping huggingface.co

# Clear cache and retry
# Windows: del %LOCALAPPDATA%\FoundryLocal\models\*
# Linux/Mac: rm -rf ~/.local/share/FoundryLocal/models/*

# Retry
python -c "from foundry_local import FoundryLocalManager; FoundryLocalManager('phi-4')"
```

#### Out of Memory

**Symptoms:** Crashes or slow performance

**Solutions:**
```python
# Use smaller model
manager = FoundryLocalManager("qwen2.5-0.5b")

# Or phi-3-mini
manager = FoundryLocalManager("phi-3-mini")
```

#### Port Already in Use

**Symptoms:** "Address already in use" error

**Solutions:**
```bash
# Find process using port 53760
# Windows
netstat -ano | findstr 53760

# Linux/Mac
lsof -i :53760

# Kill the process or use different port
```

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from foundry_local import FoundryLocalManager
manager = FoundryLocalManager("phi-4")
```

### Checking Status

```python
from src.providers.foundry import FoundryLocalProvider

provider = FoundryLocalProvider()
status = await provider.check_connection()

print(f"Available: {status.available}")
print(f"Model: {status.model_name}")
print(f"Error: {status.error}")
```

---

## Comparison with Ollama

| Feature | Foundry Local | Ollama |
|---------|--------------|--------|
| Installation | pip install | Standalone app |
| Model Library | Limited (~10) | Extensive (100+) |
| SDK Integration | Native Python | HTTP API only |
| Azure Integration | Yes | No |
| Custom Models | Limited | Full support |
| Memory Usage | Slightly lower | Standard |
| GPU Support | CUDA, Metal | CUDA, Metal, ROCm |
| Tool Calling | Phi-4, Mistral | Many models |

### When to Use Foundry Local

- Azure ecosystem integration needed
- Prefer Python SDK control
- Using Phi-4 model specifically
- Simpler deployment requirements

### When to Use Ollama

- Need wide model selection
- Want custom model configurations
- Require ROCm (AMD GPU) support
- Need extensive community support

---

## Quick Reference

### Essential Commands

```python
# Start model
from foundry_local import FoundryLocalManager
manager = FoundryLocalManager("phi-4")

# Get endpoint
print(manager.endpoint)

# With Research Agent
from src.providers.foundry import FoundryLocalProvider
provider = FoundryLocalProvider.start_with_sdk("phi-4")
```

### Recommended .env Settings

```bash
LLM_PROVIDER=foundry_local
FOUNDRY_ENDPOINT=http://127.0.0.1:53760
FOUNDRY_MODEL=phi-4
FOUNDRY_AUTO_START=true
```

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/v1/models` | List available models |
| `/v1/chat/completions` | Chat API (OpenAI compatible) |
| `/v1/completions` | Text completion API |

---

*See also: [Configuration Guide](configuration.md), [Ollama Guide](ollama.md), [Troubleshooting](troubleshooting.md)*
