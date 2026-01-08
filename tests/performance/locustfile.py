"""
Performance tests using Locust for load testing the API.

Run with: locust -f tests/performance/locustfile.py --host=http://localhost:8000

For headless mode:
locust -f tests/performance/locustfile.py --host=http://localhost:8000 --headless -u 10 -r 2 -t 60s

Test scenarios:
- AuthUser: Authentication flow (register, login, logout, token refresh)
- ResearchAgentUser: Main agent interactions with auth
- DashboardUser: Dashboard viewing with auth
- AnonymousUser: Public endpoints (health, docs)
"""

import random
import string

from locust import HttpUser, TaskSet, between, events, task


def generate_random_email():
    """Generate a unique random email for testing."""
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{suffix}@locust.test"


def generate_random_password():
    """Generate a password meeting strength requirements."""
    return f"Test@{random.randint(1000, 9999)}Pass!"


class AuthenticatedTaskSet(TaskSet):
    """Base class for authenticated task sets."""

    access_token: str | None = None
    refresh_token: str | None = None

    def on_start(self):
        """Login before starting tasks."""
        # Try to login with existing test user first
        response = self.client.post(
            "/api/auth/login",
            json={
                "email": "locust@test.com",
                "password": "LocustTest@2024!",
            },
        )

        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
        elif response.status_code == 401:
            # User doesn't exist, register new user
            response = self.client.post(
                "/api/auth/register",
                json={
                    "email": "locust@test.com",
                    "username": "locustuser",
                    "password": "LocustTest@2024!",
                    "display_name": "Locust Test User",
                },
            )
            if response.status_code == 201:
                data = response.json()
                self.access_token = data["access_token"]
                self.refresh_token = data["refresh_token"]

    def get_auth_headers(self):
        """Get authorization headers."""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}


class AuthFlowTasks(TaskSet):
    """Test authentication flow scenarios."""

    @task(3)
    def test_login_success(self):
        """Test successful login."""
        self.client.post(
            "/api/auth/login",
            json={
                "email": "locust@test.com",
                "password": "LocustTest@2024!",
            },
            name="/api/auth/login (success)",
        )

    @task(1)
    def test_login_failure(self):
        """Test failed login (wrong password)."""
        self.client.post(
            "/api/auth/login",
            json={
                "email": "locust@test.com",
                "password": "WrongPassword123!",
            },
            name="/api/auth/login (failure)",
        )

    @task(1)
    def test_register_duplicate(self):
        """Test registering with existing email."""
        self.client.post(
            "/api/auth/register",
            json={
                "email": "locust@test.com",
                "username": f"user_{random.randint(1000, 9999)}",
                "password": "TestPass@2024!",
            },
            name="/api/auth/register (duplicate)",
        )

    @task(2)
    def test_token_refresh(self):
        """Test token refresh flow."""
        # First login to get tokens
        login_resp = self.client.post(
            "/api/auth/login",
            json={
                "email": "locust@test.com",
                "password": "LocustTest@2024!",
            },
            name="/api/auth/login (for refresh)",
        )

        if login_resp.status_code == 200:
            data = login_resp.json()
            # Try to refresh the token
            self.client.post(
                "/api/auth/refresh",
                json={"refresh_token": data["refresh_token"]},
                name="/api/auth/refresh",
            )

    @task(1)
    def test_get_profile(self):
        """Test getting user profile."""
        # Login first
        login_resp = self.client.post(
            "/api/auth/login",
            json={
                "email": "locust@test.com",
                "password": "LocustTest@2024!",
            },
        )

        if login_resp.status_code == 200:
            token = login_resp.json()["access_token"]
            self.client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {token}"},
                name="/api/auth/me",
            )


class ResearchAgentTasks(AuthenticatedTaskSet):
    """Agent interaction tasks with authentication."""

    @task(3)
    def health_check(self):
        """Most common: health endpoint (public)."""
        self.client.get("/api/health")

    @task(2)
    def list_conversations(self):
        """List conversations."""
        self.client.get("/api/conversations", headers=self.get_auth_headers())

    @task(2)
    def list_documents(self):
        """List documents."""
        self.client.get("/api/documents", headers=self.get_auth_headers())

    @task(1)
    def chat_request(self):
        """Send a chat message (expensive operation)."""
        self.client.post(
            "/api/agent/chat",
            json={"message": "What tables are in the database?"},
            headers={**self.get_auth_headers(), "Content-Type": "application/json"},
            timeout=60,  # Chat can take longer
            name="/api/agent/chat",
        )

    @task(1)
    def search_documents(self):
        """Search documents via RAG."""
        self.client.post(
            "/api/documents/search",
            json={"query": "database schema", "top_k": 5},
            headers={**self.get_auth_headers(), "Content-Type": "application/json"},
            name="/api/documents/search",
        )

    @task(1)
    def list_query_history(self):
        """Get query history."""
        self.client.get("/api/queries/history", headers=self.get_auth_headers())

    @task(1)
    def list_saved_queries(self):
        """Get saved queries."""
        self.client.get("/api/queries/saved", headers=self.get_auth_headers())


class DashboardTasks(AuthenticatedTaskSet):
    """Dashboard interaction tasks."""

    @task(5)
    def list_dashboards(self):
        """List dashboards."""
        self.client.get("/api/dashboards", headers=self.get_auth_headers())

    @task(2)
    def get_settings(self):
        """Get settings."""
        self.client.get("/api/settings", headers=self.get_auth_headers())

    @task(2)
    def get_themes(self):
        """Get available themes."""
        self.client.get("/api/settings/themes", headers=self.get_auth_headers())

    @task(1)
    def list_providers(self):
        """List LLM providers."""
        self.client.get("/api/settings/providers", headers=self.get_auth_headers())


class DatabaseConnectionTasks(AuthenticatedTaskSet):
    """Database connection management tasks."""

    @task(3)
    def list_connections(self):
        """List database connections."""
        self.client.get("/api/database-connections", headers=self.get_auth_headers())

    @task(1)
    def get_active_connection(self):
        """Get active database connection."""
        self.client.get("/api/database-connections/active", headers=self.get_auth_headers())


class MCPServerTasks(AuthenticatedTaskSet):
    """MCP server management tasks."""

    @task(3)
    def list_mcp_servers(self):
        """List MCP servers."""
        self.client.get("/api/mcp", headers=self.get_auth_headers())

    @task(1)
    def get_mcp_tools(self):
        """Get available MCP tools."""
        self.client.get("/api/mcp/tools", headers=self.get_auth_headers())


# User classes that combine task sets


class AuthUser(HttpUser):
    """User focused on authentication flow testing."""

    wait_time = between(1, 3)
    tasks = {AuthFlowTasks: 1}

    def on_start(self):
        """Ensure test user exists."""
        # Try to register the test user (will fail if exists, that's ok)
        self.client.post(
            "/api/auth/register",
            json={
                "email": "locust@test.com",
                "username": "locustuser",
                "password": "LocustTest@2024!",
                "display_name": "Locust Test User",
            },
        )


class ResearchAgentUser(HttpUser):
    """Simulates a user interacting with the research agent."""

    wait_time = between(1, 5)
    tasks = {ResearchAgentTasks: 1}


class DashboardUser(HttpUser):
    """Simulates dashboard viewing."""

    wait_time = between(2, 8)
    tasks = {DashboardTasks: 1}


class DatabaseAdminUser(HttpUser):
    """Simulates a database administrator."""

    wait_time = between(2, 5)
    tasks = {DatabaseConnectionTasks: 2, MCPServerTasks: 1}


class AnonymousUser(HttpUser):
    """Unauthenticated user hitting public endpoints."""

    wait_time = between(1, 3)

    @task(5)
    def health_check(self):
        """Health check endpoint."""
        self.client.get("/api/health")

    @task(2)
    def detailed_health(self):
        """Detailed health check."""
        self.client.get("/api/health/detailed")

    @task(1)
    def api_docs(self):
        """OpenAPI docs."""
        self.client.get("/docs")


class MixedLoadUser(HttpUser):
    """Simulates realistic mixed load from various user types."""

    wait_time = between(1, 5)

    def on_start(self):
        """Login before starting tasks."""
        # Register/login test user
        self.client.post(
            "/api/auth/register",
            json={
                "email": "mixed@test.com",
                "username": "mixeduser",
                "password": "MixedTest@2024!",
            },
        )
        response = self.client.post(
            "/api/auth/login",
            json={
                "email": "mixed@test.com",
                "password": "MixedTest@2024!",
            },
        )
        if response.status_code == 200:
            self.access_token = response.json()["access_token"]
        else:
            self.access_token = None

    def get_auth_headers(self):
        """Get authorization headers."""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}

    @task(10)
    def health_check(self):
        """Health endpoint (most common)."""
        self.client.get("/api/health")

    @task(5)
    def list_conversations(self):
        """List conversations."""
        self.client.get("/api/conversations", headers=self.get_auth_headers())

    @task(5)
    def list_documents(self):
        """List documents."""
        self.client.get("/api/documents", headers=self.get_auth_headers())

    @task(3)
    def list_dashboards(self):
        """List dashboards."""
        self.client.get("/api/dashboards", headers=self.get_auth_headers())

    @task(2)
    def get_settings(self):
        """Get settings."""
        self.client.get("/api/settings", headers=self.get_auth_headers())

    @task(1)
    def search_documents(self):
        """Search documents."""
        self.client.post(
            "/api/documents/search",
            json={"query": "test query", "top_k": 3},
            headers={**self.get_auth_headers(), "Content-Type": "application/json"},
        )


# Event listeners for reporting


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    print("=" * 60)
    print("Starting Locust performance test")
    print(f"Target: {environment.host}")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops."""
    print("=" * 60)
    print("Locust test completed")
    stats = environment.stats
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Failures: {stats.total.num_failures}")
    print(f"Avg response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Requests/sec: {stats.total.total_rps:.2f}")
    print("=" * 60)
