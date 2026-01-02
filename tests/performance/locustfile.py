"""
Performance tests using Locust for load testing the API.

Run with: locust -f tests/performance/locustfile.py --host=http://localhost:8000
"""
from locust import HttpUser, task, between
import json


class ResearchAgentUser(HttpUser):
    """Simulates a user interacting with the research agent."""

    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks

    @task(3)
    def health_check(self):
        """Most common: health endpoint."""
        self.client.get("/api/health")

    @task(2)
    def list_conversations(self):
        """List conversations."""
        self.client.get("/api/conversations")

    @task(2)
    def list_documents(self):
        """List documents."""
        self.client.get("/api/documents")

    @task(1)
    def chat_request(self):
        """Send a chat message (expensive operation)."""
        self.client.post(
            "/api/agent/chat",
            json={"message": "What tables are in the database?"},
            headers={"Content-Type": "application/json"},
        )

    @task(1)
    def search_documents(self):
        """Search documents via RAG."""
        self.client.post(
            "/api/documents/search",
            json={"query": "database schema", "top_k": 5},
            headers={"Content-Type": "application/json"},
        )


class DashboardUser(HttpUser):
    """Simulates dashboard viewing."""

    wait_time = between(2, 8)

    @task(5)
    def list_dashboards(self):
        """List dashboards."""
        self.client.get("/api/dashboards")

    @task(2)
    def get_settings(self):
        """Get settings."""
        self.client.get("/api/settings")
