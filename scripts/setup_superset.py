#!/usr/bin/env python3
"""
Superset Setup Script
Phase 3: Enterprise BI Platform Integration

Automates the setup of Apache Superset:
- Authenticates with Superset API
- Adds SQL Server database connection
- Creates sample dashboard (optional)

Usage:
    python scripts/setup_superset.py

Environment Variables:
    SUPERSET_URL - Superset base URL (default: http://localhost:8088)
    SUPERSET_ADMIN_PASSWORD - Admin password (default: LocalLLM@2024!)
    MSSQL_SA_PASSWORD - SQL Server SA password (default: LocalLLM@2024!)
"""

import os
import sys
import time

import requests

# Configuration from environment
SUPERSET_URL = os.environ.get("SUPERSET_URL", "http://localhost:8088")
ADMIN_USER = os.environ.get("SUPERSET_ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("SUPERSET_ADMIN_PASSWORD", "LocalLLM@2024!")
MSSQL_PASSWORD = os.environ.get("MSSQL_SA_PASSWORD", "LocalLLM@2024!")


def wait_for_superset(max_attempts: int = 30, delay: int = 5) -> bool:
    """Wait for Superset to become available."""
    print(f"Waiting for Superset at {SUPERSET_URL}...")
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{SUPERSET_URL}/health", timeout=5)
            if response.status_code == 200:
                print("Superset is ready!")
                return True
        except requests.RequestException:
            pass
        print(f"  Attempt {attempt + 1}/{max_attempts} - waiting {delay}s...")
        time.sleep(delay)
    return False


def create_session() -> tuple[requests.Session, str, str]:
    """Create an authenticated session with CSRF token."""
    session = requests.Session()

    print("Authenticating with Superset...")
    response = session.post(
        f"{SUPERSET_URL}/api/v1/security/login",
        json={
            "username": ADMIN_USER,
            "password": ADMIN_PASS,
            "provider": "db",
            "refresh": True,
        },
        timeout=10,
    )
    if response.status_code != 200:
        print(f"Authentication failed: {response.status_code}")
        print(response.text)
        sys.exit(1)

    access_token = response.json()["access_token"]
    print("Authentication successful!")

    # Get CSRF token
    csrf_response = session.get(
        f"{SUPERSET_URL}/api/v1/security/csrf_token/",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    csrf_token = ""
    if csrf_response.status_code == 200:
        csrf_token = csrf_response.json().get("result", "")

    return session, access_token, csrf_token


def get_access_token() -> str:
    """Login and get access token (legacy function)."""
    _, token, _ = create_session()
    return token


def get_csrf_token(token: str) -> str:
    """Get CSRF token for API calls (legacy function)."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{SUPERSET_URL}/api/v1/security/csrf_token/",
        headers=headers,
        timeout=10,
    )
    if response.status_code == 200:
        return response.json().get("result", "")
    return ""


def check_database_exists(token: str, db_name: str) -> int | None:
    """Check if a database with the given name already exists."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{SUPERSET_URL}/api/v1/database/",
        headers=headers,
        timeout=10,
    )
    if response.status_code == 200:
        databases = response.json().get("result", [])
        for db in databases:
            if db.get("database_name") == db_name:
                return db.get("id")
    return None


def add_database(session: requests.Session, token: str, csrf_token: str) -> dict:
    """Add SQL Server database connection."""
    db_name = "Research Analytics"

    # Check if already exists
    existing_id = check_database_exists(token, db_name)
    if existing_id:
        print(f"Database '{db_name}' already exists with ID {existing_id}")
        return {"id": existing_id, "database_name": db_name}

    print("Adding SQL Server database connection...")

    # URL encode special characters in password
    encoded_password = MSSQL_PASSWORD.replace("@", "%40").replace("!", "%21")

    # Use the Docker internal hostname 'mssql' for the connection
    sqlalchemy_uri = f"mssql+pymssql://sa:{encoded_password}@mssql:1433/ResearchAnalytics"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-CSRFToken": csrf_token,
        "Referer": SUPERSET_URL,
    }

    response = session.post(
        f"{SUPERSET_URL}/api/v1/database/",
        headers=headers,
        json={
            "database_name": db_name,
            "engine": "mssql+pymssql",
            "sqlalchemy_uri": sqlalchemy_uri,
            "expose_in_sqllab": True,
            "allow_run_async": True,
            "allow_ctas": False,
            "allow_cvas": False,
            "allow_dml": False,
            "extra": '{"metadata_params": {}, "engine_params": {}}',
        },
        timeout=30,
    )

    if response.status_code in (200, 201):
        result = response.json()
        print(f"Database added successfully! ID: {result.get('id')}")
        return result
    else:
        print(f"Failed to add database: {response.status_code}")
        print(response.text)
        return {}


def test_database_connection(token: str, database_id: int) -> bool:
    """Test the database connection."""
    print(f"Testing database connection (ID: {database_id})...")

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{SUPERSET_URL}/api/v1/database/{database_id}/connection",
        headers=headers,
        timeout=30,
    )

    if response.status_code == 200:
        print("Database connection test successful!")
        return True
    else:
        print(f"Database connection test failed: {response.status_code}")
        print(response.text)
        return False


def list_tables(token: str, database_id: int) -> list:
    """List tables in the database."""
    print("Fetching available tables...")

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{SUPERSET_URL}/api/v1/database/{database_id}/tables/?q=(schema:dbo)",
        headers=headers,
        timeout=30,
    )

    if response.status_code == 200:
        tables = response.json().get("result", [])
        print(f"Found {len(tables)} tables:")
        for table in tables[:10]:  # Show first 10
            print(f"  - {table.get('value', table)}")
        return tables
    else:
        print(f"Failed to list tables: {response.status_code}")
        return []


def main():
    """Main setup script."""
    print("=" * 60)
    print("Apache Superset Setup Script")
    print("Phase 3: Enterprise BI Platform Integration")
    print("=" * 60)
    print()

    # Wait for Superset to be ready
    if not wait_for_superset():
        print("ERROR: Superset is not available. Please start it first:")
        print(
            "  docker-compose -f docker/docker-compose.yml --env-file .env --profile superset up -d"
        )
        sys.exit(1)

    # Create authenticated session
    session, token, csrf_token = create_session()

    # Add database
    db_result = add_database(session, token, csrf_token)

    if db_result and db_result.get("id"):
        database_id = db_result["id"]

        # Test connection
        test_database_connection(token, database_id)

        # List tables
        list_tables(token, database_id)

    print()
    print("=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print(f"1. Open Superset at {SUPERSET_URL}")
    print(f"2. Login with username '{ADMIN_USER}' and your password")
    print("3. Go to SQL Lab to explore the data")
    print("4. Create charts and dashboards")
    print()


if __name__ == "__main__":
    main()
