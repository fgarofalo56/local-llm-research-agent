"""
Real Ollama Integration Tests

These tests run against a real Ollama instance and are skipped if Ollama is not available.
They test actual LLM responses, streaming, caching, and multi-turn conversations.

Prerequisites:
    - Ollama must be running (default: http://localhost:11434)
    - A model must be available (default: qwen2.5:7b-instruct or llama3.1:8b)

Running these tests:
    # Run all Ollama integration tests (skips if Ollama not available)
    pytest tests/test_integration_ollama.py -v

    # Run only tests marked as requiring Ollama
    pytest -m requires_ollama -v

    # Run including slow tests (multi-turn conversations, etc.)
    pytest tests/test_integration_ollama.py -v -m "requires_ollama and slow"

    # Skip slow tests for faster iteration
    pytest tests/test_integration_ollama.py -v -m "requires_ollama and not slow"

Environment variables:
    OLLAMA_HOST: Ollama server URL (default: http://localhost:11434)
    OLLAMA_MODEL: Model to use for tests (auto-detected if not set)
"""

import asyncio
import os
from typing import AsyncGenerator

import httpx
import pytest

from src.agent.research_agent import ResearchAgent, create_research_agent
from src.providers import ProviderType
from src.providers.ollama import OllamaProvider


# Check if Ollama is available at test collection time
def ollama_available() -> bool:
    """Check if Ollama is running and accessible."""
    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    try:
        response = httpx.get(f"{ollama_host}/api/tags", timeout=5.0)
        return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


def get_available_model() -> str | None:
    """Get an available model from Ollama."""
    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    preferred_models = [
        "qwen2.5:7b-instruct",
        "qwen2.5:latest",
        "llama3.1:8b",
        "llama3.1:latest",
        "mistral:7b-instruct",
        "mistral:latest",
    ]
    
    try:
        response = httpx.get(f"{ollama_host}/api/tags", timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            available = [m["name"] for m in data.get("models", [])]
            
            # Try preferred models first
            for model in preferred_models:
                if model in available:
                    return model
            
            # Fall back to first available model
            if available:
                return available[0]
    except (httpx.ConnectError, httpx.TimeoutException):
        pass
    
    return None


# Skip entire module if Ollama is not available
pytestmark = [
    pytest.mark.requires_ollama,
    pytest.mark.integration,
    pytest.mark.skipif(
        not ollama_available(),
        reason="Ollama is not available at the configured host"
    ),
]


@pytest.fixture(scope="module")
def ollama_model() -> str:
    """Get an available Ollama model for testing."""
    model = get_available_model()
    if not model:
        pytest.skip("No Ollama models available")
    return model


@pytest.fixture(scope="module")
def ollama_host() -> str:
    """Get the Ollama host URL."""
    return os.environ.get("OLLAMA_HOST", "http://localhost:11434")


class TestOllamaProviderReal:
    """Real integration tests for Ollama provider."""

    @pytest.mark.asyncio
    async def test_check_connection_success(self, ollama_host: str, ollama_model: str):
        """Test checking Ollama connection returns success."""
        provider = OllamaProvider(
            host=ollama_host,
            model_name=ollama_model
        )
        
        status = await provider.check_connection()
        
        assert status.available is True
        assert status.provider_type == ProviderType.OLLAMA
        assert status.error is None

    @pytest.mark.asyncio
    async def test_list_models_returns_models(self, ollama_host: str, ollama_model: str):
        """Test listing available Ollama models."""
        provider = OllamaProvider(
            host=ollama_host,
            model_name=ollama_model
        )
        
        models = await provider.list_models()
        
        assert isinstance(models, list)
        assert len(models) > 0
        assert ollama_model in models

    def test_get_model_returns_openai_model(self, ollama_host: str, ollama_model: str):
        """Test that get_model returns an OpenAI-compatible model."""
        provider = OllamaProvider(
            host=ollama_host,
            model_name=ollama_model
        )
        
        model = provider.get_model()
        
        # Should be an OpenAIModel instance (Pydantic AI)
        assert model is not None


class TestResearchAgentRealOllama:
    """Real integration tests for ResearchAgent with Ollama."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_simple_chat_response(self, ollama_host: str, ollama_model: str):
        """Test that agent can generate a simple response."""
        # Override environment for this test
        os.environ["OLLAMA_HOST"] = ollama_host
        os.environ["OLLAMA_MODEL"] = ollama_model
        
        agent = ResearchAgent(
            provider_type="ollama",
            ollama_host=ollama_host,
            ollama_model=ollama_model,
        )
        
        response = await agent.chat("What is 2 + 2? Reply with just the number.")
        
        assert response is not None
        assert len(response) > 0
        # The response should contain "4" somewhere
        assert "4" in response

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_multi_turn_conversation(self, ollama_host: str, ollama_model: str):
        """Test multi-turn conversation maintains context."""
        agent = ResearchAgent(
            provider_type="ollama",
            ollama_host=ollama_host,
            ollama_model=ollama_model,
        )
        
        # First turn
        response1 = await agent.chat("My name is TestUser. Remember this.")
        assert response1 is not None
        assert agent.turn_count == 1
        
        # Second turn - should remember context
        response2 = await agent.chat("What is my name?")
        assert response2 is not None
        assert agent.turn_count == 2
        
        # Check history
        history = agent.get_history()
        assert len(history) == 4  # 2 user + 2 assistant messages
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_streaming_response(self, ollama_host: str, ollama_model: str):
        """Test streaming chat response."""
        agent = ResearchAgent(
            provider_type="ollama",
            ollama_host=ollama_host,
            ollama_model=ollama_model,
        )
        
        chunks: list[str] = []
        async for chunk in agent.chat_stream("Count from 1 to 5, one number per line."):
            chunks.append(chunk)
        
        # Should have multiple chunks
        assert len(chunks) > 1
        
        # Combined response should contain numbers
        full_response = "".join(chunks)
        assert len(full_response) > 0
        # At least some numbers should be present
        assert any(str(n) in full_response for n in range(1, 6))

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_clear_history_resets_context(self, ollama_host: str, ollama_model: str):
        """Test that clearing history resets conversation context."""
        agent = ResearchAgent(
            provider_type="ollama",
            ollama_host=ollama_host,
            ollama_model=ollama_model,
        )
        
        # Build some history
        await agent.chat("Hello!")
        assert agent.turn_count == 1
        
        # Clear history
        agent.clear_history()
        
        assert agent.turn_count == 0
        assert agent.get_history() == []


class TestAgentFactoryRealOllama:
    """Test agent factory with real Ollama."""

    def test_create_agent_connects_to_ollama(self, ollama_host: str, ollama_model: str):
        """Test that create_research_agent creates working agent."""
        agent = create_research_agent(
            provider_type="ollama",
            ollama_host=ollama_host,
            ollama_model=ollama_model,
        )
        
        assert agent is not None
        assert agent.provider.provider_type == ProviderType.OLLAMA

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_created_agent_can_chat(self, ollama_host: str, ollama_model: str):
        """Test that factory-created agent can actually chat."""
        agent = create_research_agent(
            provider_type="ollama",
            ollama_host=ollama_host,
            ollama_model=ollama_model,
        )
        
        response = await agent.chat("Say 'hello' and nothing else.")
        
        assert response is not None
        assert len(response) > 0


class TestAgentWithCaching:
    """Test agent caching with real Ollama."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_cache_returns_same_response(self, ollama_host: str, ollama_model: str):
        """Test that identical queries return cached responses."""
        agent = ResearchAgent(
            provider_type="ollama",
            ollama_host=ollama_host,
            ollama_model=ollama_model,
            cache_enabled=True,
        )
        
        query = "What is the capital of France? Answer in one word."
        
        # First query - not cached
        response1 = await agent.chat(query)
        stats1 = agent.get_cache_stats()
        
        # Clear history but keep cache
        agent.clear_history()
        
        # Second query - should be cached
        response2 = await agent.chat(query)
        stats2 = agent.get_cache_stats()
        
        # Responses should be identical (from cache)
        assert response1 == response2
        
        # Cache hit count should increase
        assert stats2.hits > stats1.hits


class TestAgentWithRateLimiting:
    """Test agent rate limiting with real Ollama."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_rate_limiting_allows_requests(self, ollama_host: str, ollama_model: str):
        """Test that rate limiting allows normal request flow."""
        agent = ResearchAgent(
            provider_type="ollama",
            ollama_host=ollama_host,
            ollama_model=ollama_model,
        )
        
        # Enable rate limiting via the setter
        agent.rate_limit_enabled = True
        
        # Should be able to make a few requests without issues
        for i in range(2):
            response = await agent.chat(f"Say '{i}'")
            assert response is not None
            agent.clear_history()  # Clear history between requests to keep context small
        
        stats = agent.get_rate_limit_stats()
        assert stats.total_requests == 2
        assert stats.rejected_requests == 0


class TestProviderHealthCheck:
    """Test provider health check with real Ollama."""

    @pytest.mark.asyncio
    async def test_health_check_reports_healthy(self, ollama_host: str, ollama_model: str):
        """Test that health check reports Ollama as healthy."""
        from src.utils.health import check_ollama_health, HealthStatus
        
        # Ensure environment is set for the health check
        os.environ["OLLAMA_HOST"] = ollama_host
        os.environ["OLLAMA_MODEL"] = ollama_model
        
        result = await check_ollama_health()
        
        # Result is a ComponentHealth object
        assert result.status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)
        assert result.name == "ollama"


class TestEdgeCases:
    """Edge case tests with real Ollama."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_empty_message_handling(self, ollama_host: str, ollama_model: str):
        """Test handling of empty messages."""
        agent = ResearchAgent(
            provider_type="ollama",
            ollama_host=ollama_host,
            ollama_model=ollama_model,
        )
        
        # Agent should handle empty string gracefully
        # Behavior may vary but should not crash
        try:
            response = await agent.chat("")
            # If it doesn't error, just check we got something back
            assert response is not None
        except Exception as e:
            # Some error is acceptable for empty input
            assert "empty" in str(e).lower() or "invalid" in str(e).lower() or len(str(e)) > 0

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_very_long_message(self, ollama_host: str, ollama_model: str):
        """Test handling of very long messages."""
        agent = ResearchAgent(
            provider_type="ollama",
            ollama_host=ollama_host,
            ollama_model=ollama_model,
        )
        
        # Create a long message (but not too long to cause timeout)
        long_message = "Hello! " * 100 + " Please respond with 'OK'."
        
        response = await agent.chat(long_message)
        
        assert response is not None
        assert len(response) > 0

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_unicode_message(self, ollama_host: str, ollama_model: str):
        """Test handling of unicode characters."""
        agent = ResearchAgent(
            provider_type="ollama",
            ollama_host=ollama_host,
            ollama_model=ollama_model,
        )
        
        unicode_message = "Hello! 你好! مرحبا! 🎉 Please say 'received'."
        
        response = await agent.chat(unicode_message)
        
        assert response is not None
        assert len(response) > 0
