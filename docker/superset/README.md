# Superset Database Configuration

This directory contains configuration for Apache Superset BI platform integration.

## Files

- **`superset_config.py`** - Superset configuration (caching, CORS, theming, feature flags)
- **`setup_databases.py`** - Automatic database connection setup script
- **`create_examples.py`** - Example dashboards and charts creator

## Automatic Setup on Container Start

When the Superset container starts, it automatically:

1. **Initializes Superset** - Creates admin user and metadata database
2. **Configures Databases** - Adds both SQL Server databases:
   - **ResearchAnalytics (Sample DB)** - Port 1433, research demo data
   - **LLM_BackEnd (Application DB)** - Port 1434, app state and vectors
3. **Creates Example Content** - Builds sample dashboards and charts:
   - Research Analytics Overview dashboard
   - 6 pre-built charts visualizing research data
   - Datasets for all major tables

## Data Persistence

All Superset data is persisted to a Docker volume:
- **Volume**: `local-llm-superset-data`
- **Mount Point**: `/app/superset_home`
- **Contains**: User-created dashboards, charts, queries, metadata database

**Your work is safe!** When you rebuild or restart the container:
- ✅ Existing dashboards and charts are preserved
- ✅ User-created content remains intact
- ✅ Database connections are maintained
- ✅ Example content only created if not already present

To completely reset Superset:
```bash
docker-compose -f docker/docker-compose.yml down -v
```
⚠️ This will delete ALL Superset data including your custom dashboards.

## Example Dashboard

After container startup, access the pre-built dashboard:
- **URL**: http://localhost:8088/superset/dashboard/1/
- **Login**: admin / (your SUPERSET_ADMIN_PASSWORD)

**Example Charts Included:**
1. **Researchers by Department** - Bar chart showing staff distribution
2. **Project Status Distribution** - Pie chart of active/completed/planning projects
3. **Project Budgets** - Bar chart of total budget per project
4. **Publications Timeline** - Line chart showing publication trends
5. **Funding Sources** - Donut chart of funding by source (NSF, NIH, etc.)
6. **Experiments Overview** - Table view of ongoing experiments

## Manual Database Addition

If you need to add databases manually:

1. Login to Superset: http://localhost:8088
   - Username: `admin`
   - Password: from `SUPERSET_ADMIN_PASSWORD` env var

2. Go to **Settings → Database Connections → + Database**

3. Select **Microsoft SQL Server**

4. Use connection string format:
   ```
   mssql+pymssql://sa:PASSWORD@HOST:PORT/DATABASE?charset=utf8
   ```

### Example Connection Strings

**ResearchAnalytics (Sample DB):**
```
mssql+pymssql://sa:LocalLLM@2024!@mssql:1433/ResearchAnalytics?charset=utf8
```

**LLM_BackEnd (Application DB):**
```
mssql+pymssql://sa:LocalLLM@2024!@mssql-backend:1433/LLM_BackEnd?charset=utf8
```

## Troubleshooting

### Database Connection Fails

Check that SQL Server containers are running:
```bash
docker ps | grep mssql
```

View Superset logs:
```bash
docker logs local-agent-superset
```

### Setup Script Fails

Run the setup script manually inside the container:
```bash
# Setup databases
docker exec -it local-agent-superset python /app/setup_databases.py

# Create example content
docker exec -it local-agent-superset python /app/create_examples.py
```

### Example Dashboard Not Showing

1. Check if databases are configured in **Settings → Database Connections**
2. Verify datasets are created in **Data → Datasets**
3. Check charts exist in **Charts** menu
4. Manually create dashboard if needed

### Query Editor Not Working

1. Verify database is configured in **Settings → Database Connections**
2. Check **SQL Lab** is enabled for the database
3. Test connection using **Test Connection** button
4. Check database permissions (read-only flag)

## SQL Lab Usage

Once databases are configured:

1. Go to **SQL → SQL Lab**
2. Select database from dropdown
3. Write SQL queries
4. Execute with **Run** button
5. Save queries for reuse
6. Create visualizations from results

### Example Queries

**Top 5 Researchers by Publications:**
```sql
SELECT TOP 5 
    r.FirstName + ' ' + r.LastName AS Researcher,
    COUNT(p.PublicationID) AS Publications
FROM Researchers r
LEFT JOIN Publications p ON r.ResearcherID = p.ResearcherID
GROUP BY r.FirstName, r.LastName
ORDER BY Publications DESC
```

**Project Budget Summary:**
```sql
SELECT 
    Status,
    COUNT(*) AS ProjectCount,
    SUM(Budget) AS TotalBudget,
    AVG(Budget) AS AvgBudget
FROM Projects
GROUP BY Status
```

**Funding by Department:**
```sql
SELECT 
    d.DepartmentName,
    SUM(f.Amount) AS TotalFunding,
    COUNT(DISTINCT f.FundingID) AS GrantCount
FROM Departments d
JOIN Projects p ON d.DepartmentID = p.DepartmentID
JOIN Funding f ON p.ProjectID = f.ProjectID
GROUP BY d.DepartmentName
ORDER BY TotalFunding DESC
```

## Features Enabled

- ✅ SQL Lab for ad-hoc queries
- ✅ Dashboard native filters
- ✅ Cross-filtering between charts
- ✅ Alert & reporting
- ✅ Embedded dashboards (iframe)
- ✅ Chart embedding
- ✅ Template processing
- ✅ Example dashboards and charts

## Redis Caching

Superset uses Redis Stack for query result caching:
- Host: `redis-stack:6379`
- Database: 1 (separate from main app cache)
- TTL: 300 seconds (5 minutes)

## Building Custom Dashboards

1. **Create Dataset**: Data → Datasets → + Dataset
2. **Create Chart**: Click on dataset → Create Chart
3. **Choose Visualization**: Select chart type (bar, line, pie, etc.)
4. **Configure Metrics**: Add aggregations and groupings
5. **Save Chart**: Give it a name and save
6. **Add to Dashboard**: Create new dashboard or add to existing

### Chart Types Available

- **Bar Chart** - Compare categories
- **Line Chart** - Show trends over time
- **Pie/Donut Chart** - Show proportions
- **Table** - Display detailed data
- **Big Number** - Show single KPI
- **Area Chart** - Stacked trends
- **Scatter Plot** - Show correlations
- **Heat Map** - Show patterns in matrix
- **Box Plot** - Show statistical distributions
- And 50+ more visualization types!

