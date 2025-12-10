# Ollama Management Guide

> **Complete guide to installing, configuring, and managing Ollama for the Local LLM Research Agent**

---

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Model Management](#model-management)
- [Configuration](#configuration)
- [Performance Optimization](#performance-optimization)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

---

## Overview

Ollama is a local LLM inference engine that runs models on your machine. It provides an OpenAI-compatible API that the Research Agent uses for natural language processing.

### Key Features

| Feature | Description |
|---------|-------------|
| Local Inference | All processing on your machine |
| OpenAI Compatible | Works with standard OpenAI clients |
| GPU Acceleration | CUDA (NVIDIA) and Metal (Apple) support |
| Model Library | 100+ pre-built models available |
| Tool Calling | Supported by select models |

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 8GB | 16GB+ |
| VRAM (GPU) | 6GB | 8GB+ |
| Storage | 10GB | 50GB+ (for multiple models) |
| CPU | 4 cores | 8+ cores |

---

## Installation

### Windows

1. Download from [ollama.com/download](https://ollama.com/download)
2. Run the installer
3. Ollama starts automatically in system tray

**Verify installation:**
```powershell
ollama --version
```

### macOS

**Using Homebrew:**
```bash
brew install ollama
```

**Or download from:**
[ollama.com/download](https://ollama.com/download)

**Start Ollama:**
```bash
ollama serve
```

### Linux

**Quick install:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Start as service:**
```bash
sudo systemctl start ollama
sudo systemctl enable ollama  # Auto-start on boot
```

**Manual start:**
```bash
ollama serve
```

---

## Model Management

### Recommended Models for Tool Calling

The Research Agent requires models that support **tool calling** (function calling). These models are tested and recommended:

| Model | Size | VRAM | Tool Support | Best For |
|-------|------|------|--------------|----------|
| `qwen2.5:7b-instruct` | 4.4GB | ~8GB | Excellent | SQL queries, general reasoning |
| `qwen2.5:14b-instruct` | 8.9GB | ~12GB | Excellent | Complex analysis |
| `llama3.1:8b` | 4.7GB | ~8GB | Good | General purpose |
| `llama3.2:3b` | 2.0GB | ~4GB | Good | Lightweight option |
| `mistral:7b-instruct` | 4.1GB | ~6GB | Good | Fast inference |
| `mixtral:8x7b` | 26GB | ~48GB | Excellent | High capability |

### Pulling Models

```bash
# Pull recommended model
ollama pull qwen2.5:7b-instruct

# Pull alternative models
ollama pull llama3.1:8b
ollama pull mistral:7b-instruct

# Pull quantized version (smaller, faster)
ollama pull qwen2.5:7b-instruct-q4_K_M
```

### Listing Models

```bash
# List installed models
ollama list

# Example output:
# NAME                      ID           SIZE    MODIFIED
# qwen2.5:7b-instruct       abc123...    4.4 GB  2 days ago
# llama3.1:8b               def456...    4.7 GB  1 week ago
```

### Removing Models

```bash
# Remove a model
ollama rm mistral:7b-instruct

# Remove all unused models
ollama rm $(ollama list | grep -v NAME | awk '{print $1}')
```

### Model Information

```bash
# Show model details
ollama show qwen2.5:7b-instruct

# Show model parameters
ollama show qwen2.5:7b-instruct --parameters
```

---

## Configuration

### Environment Variables

Configure Ollama in your `.env` file:

```bash
# Ollama server URL
OLLAMA_HOST=http://localhost:11434

# Model to use (must support tool calling)
OLLAMA_MODEL=qwen2.5:7b-instruct
```

### Server Configuration

Ollama uses environment variables for server configuration:

```bash
# Set custom host (default: 127.0.0.1)
export OLLAMA_HOST=0.0.0.0

# Set custom port (default: 11434)
export OLLAMA_PORT=11434

# Set models directory
export OLLAMA_MODELS=/path/to/models

# Set GPU layers (for partial GPU offload)
export OLLAMA_NUM_GPU=35

# Disable GPU (CPU only)
export OLLAMA_NUM_GPU=0
```

### Configuring for Research Agent

The agent uses these settings from `.env`:

```bash
# Provider selection
LLM_PROVIDER=ollama

# Ollama configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
```

### Verifying Configuration

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Check specific model
curl http://localhost:11434/api/show -d '{"name": "qwen2.5:7b-instruct"}'

# Test model inference
ollama run qwen2.5:7b-instruct "Hello, what can you help me with?"
```

---

## Performance Optimization

### GPU Acceleration

**Check GPU detection:**
```bash
ollama ps
# Shows GPU info if detected
```

**NVIDIA CUDA:**
```bash
# Verify CUDA
nvidia-smi

# Ollama auto-detects CUDA GPUs
```

**Apple Metal (M1/M2/M3):**
- Automatically enabled on Apple Silicon
- No configuration needed

**AMD ROCm (Linux):**
```bash
# Install ROCm first
# Then Ollama auto-detects
```

### Memory Management

**Reduce memory usage:**
```bash
# Use quantized models
ollama pull qwen2.5:7b-instruct-q4_K_M  # 4-bit quantization
ollama pull qwen2.5:7b-instruct-q5_K_M  # 5-bit quantization

# Smaller context window (custom modelfile)
```

**Increase context window:**
Create a Modelfile:
```dockerfile
FROM qwen2.5:7b-instruct
PARAMETER num_ctx 16384
```

Apply it:
```bash
ollama create qwen-16k -f Modelfile
```

### Pre-loading Models

Pre-load models for faster first response:

```bash
# Keep model loaded in memory
ollama run qwen2.5:7b-instruct ""

# Or use the keep_alive parameter in API calls
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:7b-instruct",
  "keep_alive": "24h"
}'
```

### Batch Processing Tips

- **Sequential queries**: Model stays loaded between requests
- **Concurrent queries**: May cause memory issues with large models
- **Rate limiting**: Use agent's rate limiting for controlled throughput

---

## Monitoring

### Running Models

```bash
# Show running models
ollama ps

# Example output:
# NAME                      ID           SIZE    PROCESSOR   UNTIL
# qwen2.5:7b-instruct       abc123...    5.3 GB  100% GPU    4 minutes from now
```

### Server Logs

**Linux (systemd):**
```bash
journalctl -u ollama -f
```

**macOS/Windows:**
Check Ollama app logs in:
- macOS: `~/.ollama/logs/`
- Windows: `%USERPROFILE%\.ollama\logs\`

### API Health Check

```bash
# Check server status
curl http://localhost:11434/api/tags

# Check model availability
curl http://localhost:11434/api/show -d '{"name": "qwen2.5:7b-instruct"}'
```

### Resource Monitoring

```bash
# GPU usage (NVIDIA)
watch -n 1 nvidia-smi

# Memory usage
watch -n 1 free -h

# CPU usage
htop
```

---

## Troubleshooting

### Common Issues

#### Ollama Not Running

**Symptoms:** Connection refused errors

**Solutions:**
```bash
# Start Ollama
ollama serve

# Or restart service (Linux)
sudo systemctl restart ollama

# Check status
systemctl status ollama
```

#### Model Not Found

**Symptoms:** "model not found" error

**Solutions:**
```bash
# List available models
ollama list

# Pull the model
ollama pull qwen2.5:7b-instruct

# Update .env with correct model name
OLLAMA_MODEL=qwen2.5:7b-instruct
```

#### Out of Memory

**Symptoms:** Crashes, slow performance

**Solutions:**
```bash
# Use smaller model
ollama pull qwen2.5:3b-instruct

# Use quantized model
ollama pull qwen2.5:7b-instruct-q4_K_M

# Reduce context size (create custom modelfile)
```

#### GPU Not Detected

**Symptoms:** Running on CPU, slow inference

**Solutions:**
```bash
# Check GPU
nvidia-smi  # NVIDIA
rocm-smi    # AMD

# Reinstall Ollama
# Ensure GPU drivers are installed
```

#### Slow Responses

**Symptoms:** Long wait times

**Solutions:**
```bash
# Pre-load model
ollama run qwen2.5:7b-instruct ""

# Check if GPU is being used
ollama ps

# Use faster model
ollama pull mistral:7b-instruct
```

### Debug Mode

Enable verbose logging:
```bash
# Set debug environment
OLLAMA_DEBUG=1 ollama serve
```

### Reset Ollama

If all else fails:
```bash
# Stop Ollama
pkill ollama

# Clear cache (optional)
rm -rf ~/.ollama/models/*

# Restart
ollama serve

# Re-pull models
ollama pull qwen2.5:7b-instruct
```

---

## Advanced Usage

### Custom Models

Create a custom model with specific parameters:

```dockerfile
# Modelfile
FROM qwen2.5:7b-instruct

# Set parameters
PARAMETER temperature 0.7
PARAMETER num_ctx 8192
PARAMETER num_predict 2048
PARAMETER top_p 0.9

# Custom system prompt (optional)
SYSTEM """You are a helpful SQL data analyst assistant."""
```

```bash
# Create the model
ollama create sql-analyst -f Modelfile

# Use it
OLLAMA_MODEL=sql-analyst
```

### Remote Ollama Server

Run Ollama on a different machine:

**On the server:**
```bash
# Allow external connections
OLLAMA_HOST=0.0.0.0 ollama serve
```

**On the client (.env):**
```bash
OLLAMA_HOST=http://192.168.1.100:11434
```

### Docker Deployment

```yaml
# docker-compose.yml
services:
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

volumes:
  ollama-data:
```

### API Reference

**List models:**
```bash
curl http://localhost:11434/api/tags
```

**Generate completion:**
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:7b-instruct",
  "prompt": "Hello"
}'
```

**Chat completion (OpenAI compatible):**
```bash
curl http://localhost:11434/v1/chat/completions -d '{
  "model": "qwen2.5:7b-instruct",
  "messages": [{"role": "user", "content": "Hello"}]
}'
```

---

## Quick Reference

### Essential Commands

| Command | Description |
|---------|-------------|
| `ollama serve` | Start Ollama server |
| `ollama list` | List installed models |
| `ollama pull <model>` | Download a model |
| `ollama rm <model>` | Remove a model |
| `ollama run <model>` | Interactive chat |
| `ollama ps` | Show running models |
| `ollama show <model>` | Model information |

### Recommended .env Settings

```bash
LLM_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
```

---

*See also: [Configuration Guide](configuration.md), [Troubleshooting](troubleshooting.md), [Foundry Local Guide](foundry-local.md)*
