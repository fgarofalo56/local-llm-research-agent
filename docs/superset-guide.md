# Apache Superset User Guide

## Overview

Apache Superset provides enterprise-grade business intelligence capabilities alongside the AI-powered Research Analytics application. While the React UI handles natural language queries with AI assistance, Superset offers traditional BI features for formal reporting.

**Key Benefits:**
- Full SQL editor with syntax highlighting (SQL Lab)
- 40+ visualization types
- Scheduled email reports
- Role-based access control
- Embeddable dashboards

## Getting Started

### Starting Superset

From the project root directory:

```bash
# Start Superset (includes SQL Server and Redis dependencies)
docker-compose -f docker/docker-compose.yml --env-file .env --profile superset up -d

# View logs
docker logs -f local-agent-superset

# Run setup script to configure database connection
python scripts/setup_superset.py
```

### Accessing Superset

- **URL**: http://localhost:8088
- **Default Username**: `admin`
- **Default Password**: Value of `SUPERSET_ADMIN_PASSWORD` in `.env` (default: `LocalLLM@2024!`)

## Features

### SQL Lab

SQL Lab is a full-featured SQL IDE for data exploration:

1. Navigate to **SQL Lab** → **SQL Editor**
2. Select "Research Analytics" database
3. Browse tables in the left panel
4. Write and execute SQL queries
5. Save queries for later use
6. Export results to CSV

**Sample Queries:**

```sql
-- Funding by Department
SELECT
    d.Name AS Department,
    SUM(f.Amount) AS TotalFunding,
    COUNT(f.Id) AS GrantCount
FROM Funding f
JOIN Projects p ON f.ProjectId = p.Id
JOIN Departments d ON p.DepartmentId = d.Id
GROUP BY d.Name
ORDER BY TotalFunding DESC;

-- Research Output Over Time
SELECT
    FORMAT(PublicationDate, 'yyyy-MM') AS Month,
    COUNT(*) AS Publications
FROM Publications
WHERE PublicationDate >= DATEADD(year, -2, GETDATE())
GROUP BY FORMAT(PublicationDate, 'yyyy-MM')
ORDER BY Month;

-- Active Projects by Status
SELECT
    Status,
    COUNT(*) AS ProjectCount,
    SUM(Budget) AS TotalBudget
FROM Projects
GROUP BY Status;
```

### Creating Charts

1. Navigate to **Charts** → **+ Chart**
2. Select a dataset (saved query or table)
3. Choose visualization type:
   - **Bar Chart**: Comparisons, categories
   - **Line Chart**: Time series, trends
   - **Pie Chart**: Proportions, distributions
   - **Big Number**: Key metrics
   - **Table**: Detailed data views
4. Configure chart options
5. Save the chart

### Building Dashboards

1. Navigate to **Dashboards** → **+ Dashboard**
2. Give your dashboard a name
3. Click **Edit** to enter edit mode
4. Drag charts from the left panel onto the canvas
5. Resize and arrange charts
6. Add filters for interactivity
7. Save and publish

### Scheduled Reports

Superset supports scheduled email reports:

1. Open a dashboard
2. Click the **...** menu → **Set up an email report**
3. Configure:
   - Recipients
   - Schedule (daily, weekly, monthly)
   - Format (PDF, PNG, CSV)
4. Save the report

**Note**: Email requires SMTP configuration in `superset_config.py`.

## Integration with React App

### Embedded Dashboards

Superset dashboards can be viewed within the React application:

1. Create and publish a dashboard in Superset
2. In the React app, go to **Superset Reports**
3. Click on any dashboard to view it embedded
4. Use the external link button to open in Superset

### API Access

The FastAPI backend provides endpoints for Superset integration:

| Endpoint | Description |
|----------|-------------|
| `GET /api/superset/health` | Check Superset status |
| `GET /api/superset/dashboards` | List all dashboards |
| `GET /api/superset/embed/{id}` | Get embed URL with guest token |
| `GET /api/superset/charts` | List all charts |
| `GET /api/superset/databases` | List database connections |

## Best Practices

### Dashboard Design

- Use meaningful chart titles and descriptions
- Group related charts together
- Add dashboard-level filters for interactivity
- Keep dashboards focused on a single topic
- Use consistent color schemes

### SQL Lab

- Save frequently used queries
- Use meaningful query names
- Add comments to complex queries
- Use LIMIT for large datasets during exploration

### Performance

- Create indexes on frequently filtered columns
- Use materialized views for complex aggregations
- Set appropriate refresh intervals for dashboards
- Limit row counts in charts

## Troubleshooting

### "Superset Not Available"

**Symptoms:** Cannot connect to Superset at localhost:8088

**Solutions:**
1. Check if the container is running:
   ```bash
   docker ps | grep superset
   ```
2. View container logs:
   ```bash
   docker logs local-agent-superset
   ```
3. Restart the container:
   ```bash
   docker-compose -f docker/docker-compose.yml --profile superset restart superset
   ```

### "Database Connection Failed"

**Symptoms:** Cannot query SQL Server from Superset

**Solutions:**
1. Verify SQL Server is running:
   ```bash
   docker ps | grep mssql
   ```
2. Check network connectivity:
   ```bash
   docker exec local-agent-superset ping mssql
   ```
3. Verify credentials in database settings
4. Re-run the setup script:
   ```bash
   python scripts/setup_superset.py
   ```

### "Guest Token Creation Failed"

**Symptoms:** Embedded dashboards don't load in React app

**Solutions:**
1. Ensure dashboard is published
2. Check FEATURE_FLAGS in `superset_config.py`:
   - `EMBEDDED_SUPERSET: True`
   - `EMBEDDABLE_CHARTS: True`
3. Verify PUBLIC_ROLE_LIKE is set to "Gamma"

### "Iframe Not Loading"

**Symptoms:** White/blank iframe in React app

**Solutions:**
1. Check browser console for errors
2. Verify CORS settings in `superset_config.py`
3. Ensure `TALISMAN_ENABLED = False`
4. Check `X-Frame-Options` header is set to "ALLOWALL"

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SUPERSET_URL` | http://localhost:8088 | Superset base URL |
| `SUPERSET_SECRET_KEY` | (generated) | Session encryption key |
| `SUPERSET_ADMIN_PASSWORD` | LocalLLM@2024! | Admin user password |
| `SUPERSET_PORT` | 8088 | Web UI port |

### Config File Options

Key settings in `docker/superset/superset_config.py`:

```python
# Row limit for queries
ROW_LIMIT = 5000

# SQL Lab timeout (seconds)
SQLLAB_TIMEOUT = 300

# Enable/disable features
FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
    "DASHBOARD_NATIVE_FILTERS": True,
    "EMBEDDED_SUPERSET": True,
}
```

## Additional Resources

- [Apache Superset Documentation](https://superset.apache.org/docs/intro)
- [Superset API Reference](https://superset.apache.org/docs/api)
- [Chart Gallery](https://superset.apache.org/docs/creating-charts-dashboards/creating-your-first-dashboard)
