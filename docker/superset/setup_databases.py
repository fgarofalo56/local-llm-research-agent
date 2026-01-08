#!/usr/bin/env python3
"""
Superset Database Setup Script
Automatically configures SQL Server databases in Superset.
"""

import os
import sys
import time
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def wait_for_superset():
    """Wait for Superset to be ready."""
    import requests
    
    max_retries = 30
    retry_delay = 2
    superset_url = "http://localhost:8088/health"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(superset_url, timeout=5)
            if response.status_code == 200:
                logger.info("Superset is ready!")
                return True
        except Exception as e:
            logger.debug(f"Attempt {attempt + 1}/{max_retries}: {e}")
        
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
    
    logger.error("Superset failed to become ready")
    return False


def get_superset_session():
    """Get authenticated Superset session."""
    import requests
    
    admin_user = os.environ.get("SUPERSET_ADMIN_USER", "admin")
    admin_password = os.environ.get("SUPERSET_ADMIN_PASSWORD", "LocalLLM@2024!")
    base_url = "http://localhost:8088"
    
    session = requests.Session()
    
    # Get CSRF token from login page
    response = session.get(f"{base_url}/login/")
    
    # Login to get JWT token
    login_data = {
        "username": admin_user,
        "password": admin_password,
        "provider": "db"
    }
    
    response = session.post(f"{base_url}/api/v1/security/login", json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        access_token = data.get("access_token")
        
        # Get CSRF token after authentication
        csrf_response = session.get(f"{base_url}/api/v1/security/csrf_token/")
        if csrf_response.status_code == 200:
            csrf_token = csrf_response.json().get("result")
            
            # Set headers with both JWT and CSRF token
            session.headers.update({
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-CSRFToken": csrf_token,
                "Referer": base_url
            })
            
            logger.info("Successfully authenticated with Superset")
            return session
        else:
            logger.error(f"Failed to get CSRF token: {csrf_response.status_code}")
            return None
    else:
        logger.error(f"Failed to authenticate: {response.status_code} - {response.text}")
        return None


def check_database_exists(session, database_name: str) -> Optional[int]:
    """Check if database already exists in Superset."""
    base_url = "http://localhost:8088"
    
    response = session.get(f"{base_url}/api/v1/database/")
    
    if response.status_code == 200:
        databases = response.json().get("result", [])
        for db in databases:
            if db.get("database_name") == database_name:
                logger.info(f"Database '{database_name}' already exists (ID: {db.get('id')})")
                return db.get("id")
    
    return None


def add_sql_server_database(session, database_name: str, host: str, port: str, db_name: str, password: str) -> bool:
    """Add SQL Server database to Superset using ODBC-style connection."""
    import urllib.parse
    base_url = "http://localhost:8088"
    
    # Check if database already exists
    existing_id = check_database_exists(session, database_name)
    if existing_id:
        logger.info(f"Database '{database_name}' already configured, skipping")
        return True
    
    # Standard pymssql connection string
    # NOTE: Password should be alphanumeric only to avoid encoding issues
    # URL-encode password for safety
    encoded_password = urllib.parse.quote_plus(password)
    
    # Build SQLAlchemy URI
    sqlalchemy_uri = f"mssql+pymssql://sa:{encoded_password}@{host}:{port}/{db_name}?charset=utf8"
    
    database_config = {
        "database_name": database_name,
        "sqlalchemy_uri": sqlalchemy_uri,
        "expose_in_sqllab": True,
        "allow_run_async": True,
        "allow_ctas": False,  # Don't allow creating tables in sample DB
        "allow_cvas": False,  # Don't allow creating views in sample DB
        "allow_dml": False,   # Don't allow DML in sample DB (read-only)
        "extra": '{"engine_params": {"connect_args": {"timeout": 30}}}',
        "server_cert": "",
        "configuration_method": "sqlalchemy_form"
    }
    
    response = session.post(f"{base_url}/api/v1/database/", json=database_config)
    
    if response.status_code in (200, 201):
        logger.info(f"Successfully added database '{database_name}'")
        return True
    else:
        logger.error(f"Failed to add database '{database_name}': {response.status_code}")
        logger.error(f"Response: {response.text}")
        return False


def setup_databases():
    """Setup all SQL Server databases in Superset."""
    
    # Wait for Superset to be ready
    if not wait_for_superset():
        logger.error("Superset is not ready, aborting database setup")
        return False
    
    # Get authenticated session
    session = get_superset_session()
    if not session:
        logger.error("Failed to authenticate with Superset")
        return False
    
    # Database configurations from environment
    databases = [
        {
            "name": "ResearchAnalytics (Sample DB)",
            "host": os.environ.get("MSSQL_HOST", "mssql"),
            "port": os.environ.get("MSSQL_PORT", "1433"),
            "database": os.environ.get("MSSQL_DATABASE", "ResearchAnalytics"),
            "password": os.environ.get("MSSQL_SA_PASSWORD", "LocalLLM@2024!")
        },
        {
            "name": "LLM_BackEnd (Application DB)",
            "host": "mssql-backend",
            "port": "1433",
            "database": "LLM_BackEnd",
            "password": os.environ.get("MSSQL_SA_PASSWORD", "LocalLLM@2024!")
        }
    ]
    
    success_count = 0
    for db_config in databases:
        logger.info(f"Setting up database: {db_config['name']}")
        
        success = add_sql_server_database(
            session=session,
            database_name=db_config["name"],
            host=db_config["host"],
            port=db_config["port"],
            db_name=db_config["database"],
            password=db_config["password"]
        )
        
        if success:
            success_count += 1
    
    logger.info(f"Database setup complete: {success_count}/{len(databases)} databases configured")
    return success_count == len(databases)


if __name__ == "__main__":
    try:
        success = setup_databases()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.exception(f"Fatal error during database setup: {e}")
        sys.exit(1)
