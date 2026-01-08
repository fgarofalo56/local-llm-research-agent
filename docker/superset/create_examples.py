#!/usr/bin/env python3
"""
Superset Example Content Creator
Creates example dashboards, charts, and datasets for ResearchAnalytics database.
"""

import os
import sys
import time
import logging
from typing import Optional, Dict, Any, List

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
    """Get authenticated Superset session with CSRF token."""
    import requests
    
    admin_user = os.environ.get("SUPERSET_ADMIN_USER", "admin")
    admin_password = os.environ.get("SUPERSET_ADMIN_PASSWORD", "LocalLLM@2024!")
    base_url = "http://localhost:8088"
    
    session = requests.Session()
    
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
        
        # Get CSRF token
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
        logger.error(f"Failed to authenticate: {response.status_code}")
        return None


def get_database_id(session, database_name: str) -> Optional[int]:
    """Get database ID by name."""
    base_url = "http://localhost:8088"
    
    response = session.get(f"{base_url}/api/v1/database/")
    
    if response.status_code == 200:
        databases = response.json().get("result", [])
        for db in databases:
            if db.get("database_name") == database_name:
                return db.get("id")
    
    logger.error(f"Database '{database_name}' not found")
    return None


def create_dataset(session, database_id: int, table_name: str, schema: str = "dbo") -> Optional[int]:
    """Create a dataset (table/view) in Superset."""
    base_url = "http://localhost:8088"
    
    # Check if dataset already exists
    response = session.get(f"{base_url}/api/v1/dataset/")
    if response.status_code == 200:
        datasets = response.json().get("result", [])
        for ds in datasets:
            if ds.get("table_name") == table_name and ds.get("database", {}).get("id") == database_id:
                logger.info(f"Dataset '{table_name}' already exists (ID: {ds.get('id')})")
                return ds.get("id")
    
    # Create new dataset
    dataset_config = {
        "database": database_id,
        "schema": schema,
        "table_name": table_name
    }
    
    response = session.post(f"{base_url}/api/v1/dataset/", json=dataset_config)
    
    if response.status_code in (200, 201):
        dataset_id = response.json().get("id")
        logger.info(f"Successfully created dataset '{table_name}' (ID: {dataset_id})")
        return dataset_id
    else:
        logger.error(f"Failed to create dataset '{table_name}': {response.status_code}")
        logger.error(f"Response: {response.text}")
        return None


def create_chart(session, dataset_id: int, chart_config: Dict[str, Any]) -> Optional[int]:
    """Create a chart in Superset."""
    base_url = "http://localhost:8088"
    
    # Check if chart already exists
    chart_name = chart_config.get("slice_name")
    response = session.get(f"{base_url}/api/v1/chart/")
    if response.status_code == 200:
        charts = response.json().get("result", [])
        for chart in charts:
            if chart.get("slice_name") == chart_name:
                logger.info(f"Chart '{chart_name}' already exists (ID: {chart.get('id')})")
                return chart.get("id")
    
    # Add dataset_id to config
    chart_config["datasource_id"] = dataset_id
    chart_config["datasource_type"] = "table"
    
    response = session.post(f"{base_url}/api/v1/chart/", json=chart_config)
    
    if response.status_code in (200, 201):
        chart_id = response.json().get("id")
        logger.info(f"Successfully created chart '{chart_name}' (ID: {chart_id})")
        return chart_id
    else:
        logger.error(f"Failed to create chart '{chart_name}': {response.status_code}")
        logger.error(f"Response: {response.text}")
        return None


def create_dashboard(session, dashboard_name: str, chart_ids: List[int]) -> Optional[int]:
    """Create a dashboard with charts."""
    base_url = "http://localhost:8088"
    
    # Check if dashboard already exists
    response = session.get(f"{base_url}/api/v1/dashboard/")
    if response.status_code == 200:
        dashboards = response.json().get("result", [])
        for dash in dashboards:
            if dash.get("dashboard_title") == dashboard_name:
                logger.info(f"Dashboard '{dashboard_name}' already exists (ID: {dash.get('id')})")
                return dash.get("id")
    
    # Create dashboard layout
    position_json = {}
    row = 0
    col = 0
    
    for i, chart_id in enumerate(chart_ids):
        chart_key = f"CHART-{chart_id}"
        position_json[chart_key] = {
            "type": "CHART",
            "id": chart_id,
            "children": [],
            "meta": {
                "width": 6,
                "height": 50,
                "chartId": chart_id
            }
        }
        
        # Arrange in 2 columns
        if i % 2 == 0:
            position_json[chart_key]["meta"]["x"] = 0
            position_json[chart_key]["meta"]["y"] = row
        else:
            position_json[chart_key]["meta"]["x"] = 6
            position_json[chart_key]["meta"]["y"] = row
            row += 50
    
    dashboard_config = {
        "dashboard_title": dashboard_name,
        "slug": dashboard_name.lower().replace(" ", "-"),
        "published": True,
        "position_json": position_json
    }
    
    response = session.post(f"{base_url}/api/v1/dashboard/", json=dashboard_config)
    
    if response.status_code in (200, 201):
        dashboard_id = response.json().get("id")
        logger.info(f"Successfully created dashboard '{dashboard_name}' (ID: {dashboard_id})")
        return dashboard_id
    else:
        logger.error(f"Failed to create dashboard '{dashboard_name}': {response.status_code}")
        logger.error(f"Response: {response.text}")
        return None


def setup_example_content():
    """Setup example dashboards and charts."""
    
    # Wait for Superset
    if not wait_for_superset():
        return False
    
    # Get authenticated session
    session = get_superset_session()
    if not session:
        return False
    
    # Get database ID
    database_id = get_database_id(session, "ResearchAnalytics (Sample DB)")
    if not database_id:
        logger.error("ResearchAnalytics database not found. Run setup_databases.py first.")
        return False
    
    # Create datasets
    logger.info("Creating datasets...")
    datasets = {}
    tables = ["Researchers", "Projects", "Publications", "Departments", "Funding", "Experiments"]
    
    for table in tables:
        dataset_id = create_dataset(session, database_id, table)
        if dataset_id:
            datasets[table] = dataset_id
    
    if not datasets:
        logger.error("Failed to create any datasets")
        return False
    
    # Create charts
    logger.info("Creating charts...")
    chart_ids = []
    
    # Chart 1: Researchers by Department (Bar Chart)
    if "Researchers" in datasets:
        chart_config = {
            "slice_name": "Researchers by Department",
            "viz_type": "dist_bar",
            "params": {
                "metrics": ["count"],
                "groupby": ["DepartmentID"],
                "columns": [],
                "row_limit": 10,
                "color_scheme": "supersetColors"
            }
        }
        chart_id = create_chart(session, datasets["Researchers"], chart_config)
        if chart_id:
            chart_ids.append(chart_id)
    
    # Chart 2: Project Status Distribution (Pie Chart)
    if "Projects" in datasets:
        chart_config = {
            "slice_name": "Project Status Distribution",
            "viz_type": "pie",
            "params": {
                "metric": "count",
                "groupby": ["Status"],
                "color_scheme": "supersetColors",
                "donut": False,
                "show_labels": True,
                "show_legend": True
            }
        }
        chart_id = create_chart(session, datasets["Projects"], chart_config)
        if chart_id:
            chart_ids.append(chart_id)
    
    # Chart 3: Total Budget by Project (Bar Chart)
    if "Projects" in datasets:
        chart_config = {
            "slice_name": "Project Budgets",
            "viz_type": "dist_bar",
            "params": {
                "metrics": [{
                    "expressionType": "SIMPLE",
                    "column": {"column_name": "Budget"},
                    "aggregate": "SUM",
                    "label": "Total Budget"
                }],
                "groupby": ["ProjectName"],
                "columns": [],
                "row_limit": 10,
                "color_scheme": "supersetColors"
            }
        }
        chart_id = create_chart(session, datasets["Projects"], chart_config)
        if chart_id:
            chart_ids.append(chart_id)
    
    # Chart 4: Publications Over Time (Line Chart)
    if "Publications" in datasets:
        chart_config = {
            "slice_name": "Publications Timeline",
            "viz_type": "line",
            "params": {
                "metrics": ["count"],
                "groupby": ["PublicationDate"],
                "time_grain_sqla": "P1M",
                "color_scheme": "supersetColors",
                "show_legend": True,
                "markerEnabled": True
            }
        }
        chart_id = create_chart(session, datasets["Publications"], chart_config)
        if chart_id:
            chart_ids.append(chart_id)
    
    # Chart 5: Funding by Source (Pie Chart)
    if "Funding" in datasets:
        chart_config = {
            "slice_name": "Funding Sources",
            "viz_type": "pie",
            "params": {
                "metric": {
                    "expressionType": "SIMPLE",
                    "column": {"column_name": "Amount"},
                    "aggregate": "SUM",
                    "label": "Total Funding"
                },
                "groupby": ["FundingSource"],
                "color_scheme": "supersetColors",
                "donut": True,
                "show_labels": True,
                "show_legend": True
            }
        }
        chart_id = create_chart(session, datasets["Funding"], chart_config)
        if chart_id:
            chart_ids.append(chart_id)
    
    # Chart 6: Experiment Status (Table)
    if "Experiments" in datasets:
        chart_config = {
            "slice_name": "Experiments Overview",
            "viz_type": "table",
            "params": {
                "metrics": ["count"],
                "groupby": ["ExperimentName", "Status"],
                "columns": [],
                "row_limit": 20,
                "color_scheme": "supersetColors",
                "table_timestamp_format": "%Y-%m-%d"
            }
        }
        chart_id = create_chart(session, datasets["Experiments"], chart_config)
        if chart_id:
            chart_ids.append(chart_id)
    
    if not chart_ids:
        logger.error("Failed to create any charts")
        return False
    
    # Create dashboard
    logger.info("Creating dashboard...")
    dashboard_id = create_dashboard(session, "Research Analytics Overview", chart_ids)
    
    if dashboard_id:
        logger.info(f"✅ Successfully created example content!")
        logger.info(f"   Dashboard: http://localhost:8088/superset/dashboard/{dashboard_id}/")
        logger.info(f"   Charts created: {len(chart_ids)}")
        return True
    else:
        logger.error("Failed to create dashboard")
        return False


if __name__ == "__main__":
    try:
        success = setup_example_content()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.exception(f"Fatal error during example content setup: {e}")
        sys.exit(1)
