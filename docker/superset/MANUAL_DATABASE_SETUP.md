# Manual Database Setup Guide for Superset

**Note**: With the simplified password (`LocalLLM2024`), automated database setup should work on container startup. This guide is provided as a fallback or for customizing database configurations.

## Prerequisites

- Superset running at http://localhost:8088
- SQL Server containers running (ports 1433 and 1434)
- Admin credentials: `admin` / `LocalLLM2024`

## Automated Setup (Default)

Databases are automatically configured on container startup. Wait ~60 seconds after starting Superset, then:

1. Login at http://localhost:8088 (admin/LocalLLM2024)
2. Navigate to **Settings** → **Database Connections**
3. Verify both databases appear:
   - `ResearchAnalytics (Sample DB)`
   - `LLM_BackEnd (Application DB)`

If databases are already configured, you're done! Otherwise, follow the manual steps below.

## Manual Database Configuration

### 1. Login to Superset

1. Navigate to http://localhost:8088
2. Login with username `admin` and password `LocalLLM2024`

### 2. Add ResearchAnalytics Database (Sample DB)

1. Click **Settings** → **Database Connections** in the top menu
2. Click **+ Database** button (top right)
3. Select **Microsoft SQL Server** from the list
4. Fill in the form:

**SUPPORTED DATABASE**
- Select: `Microsoft SQL Server`

**BASIC** Tab:
- **Display Name**: `ResearchAnalytics (Sample DB)`
- **SQLAlchemy URI**: 
  ```
  mssql+pymssql://sa:LocalLLM2024@mssql:1433/ResearchAnalytics?charset=utf8
  ```
- **Expose database in SQL Lab**: ✅ (checked)
- **Allow CREATE TABLE AS**: ✅ (checked)
- **Allow CREATE VIEW AS**: ✅ (checked)
- **Allow DML**: ✅ (checked) *Only if you want INSERT/UPDATE/DELETE operations*

**ADVANCED** Tab (Optional):
- Leave defaults or customize as needed

**SECURITY** Tab:
- Leave defaults

5. Click **Test Connection** button
   - Should show "Connection looks good!"
   - If it fails, verify:
     - SQL Server container `local-agent-mssql` is running: `docker ps | grep mssql`
     - Port 1433 is accessible
     - Password encoding is correct: `%40` = `@`, `%21` = `!`

6. Click **Connect** button to save

### 3. Add LLM_BackEnd Database (Application DB)

Repeat the same process:

1. Click **+ Database** button
2. Select **Microsoft SQL Server**
3. Fill in the form:

**BASIC** Tab:
- **Display Name**: `LLM_BackEnd (Application DB)`
- **SQLAlchemy URI**:
  ```
  mssql+pymssql://sa:LocalLLM2024@mssql-backend:1434/LLM_BackEnd?charset=utf8
  ```
- **Expose database in SQL Lab**: ✅ (checked)
- **Allow CREATE TABLE AS**: ✅ (checked)
- **Allow CREATE VIEW AS**: ✅ (checked)
- **Allow DML**: ✅ (checked) *Only if needed*

4. Click **Test Connection**
5. Click **Connect** to save

## Verify Connections

### Test in SQL Lab

1. Click **SQL Lab** → **SQL Editor** in top menu
2. Select database from dropdown (top left)
3. Run a test query:

**For ResearchAnalytics:**
```sql
SELECT TOP 5 
    r.FirstName, 
    r.LastName, 
    d.DepartmentName,
    r.Title
FROM Researchers r
JOIN Departments d ON r.DepartmentID = d.DepartmentID
ORDER BY r.LastName;
```

**For LLM_BackEnd:**
```sql
-- Check app schema tables
SELECT name 
FROM sys.tables 
WHERE schema_name(schema_id) = 'app'
ORDER BY name;
```

### Expected Results

- Query should execute without errors
- Results should display in the Results pane
- You can now create datasets, charts, and dashboards

## Troubleshooting

### Connection Test Fails

**Error: "Unable to connect"**
- Verify container is running: `docker ps | grep mssql`
- Check container logs: `docker logs local-agent-mssql` or `docker logs local-agent-mssql-backend`
- Ensure containers are on same Docker network: `local-agent-network`

**Error: "Invalid credentials"**
- Verify password is correct: `LocalLLM2024` (no special characters)
- Check environment variable in container: `docker exec local-agent-mssql env | grep MSSQL_SA_PASSWORD`

**Error: "Database does not exist"**
- Run initialization script:
  ```bash
  docker-compose -f docker/docker-compose.yml --env-file .env --profile init up mssql-tools
  ```

### Query Execution Fails

**Error: "Table does not exist"**
- Verify database was initialized with sample data
- Check table names are case-sensitive
- Schema prefix may be required: `dbo.Researchers`

**Error: "Permission denied"**
- SA account should have full permissions
- Try reconnecting to database
- Restart Superset container if needed

## Next Steps

Once databases are configured:

1. **Create Datasets**: Settings → Datasets → + Dataset
2. **Build Charts**: Charts → + Chart
3. **Create Dashboards**: Dashboards → + Dashboard
4. **Explore SQL Lab**: SQL Lab → SQL Editor for ad-hoc queries

## Password Requirements for Automation

**Important**: Automated database setup requires alphanumeric passwords only. The password has been changed to `LocalLLM2024` (no special characters) to enable automation.

**If you need special characters**:
- Use manual setup through Superset UI (this guide)
- Superset UI handles password encoding internally
- Manual setup works with any password characters

## Resources

- Superset Documentation: https://superset.apache.org/docs/intro
- SQL Lab Guide: https://superset.apache.org/docs/using-superset/sql-lab
- Creating Charts: https://superset.apache.org/docs/using-superset/creating-your-first-dashboard
- Sample Queries: See `docker/superset/README.md`
