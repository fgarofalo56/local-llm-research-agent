# 🐳 Docker Setup for Local LLM Research Agent

> **SQL Server 2022 with sample research analytics data for testing the agent**

---

## 📑 Table of Contents

- [Quick Start](#-quick-start)
- [Connection Details](#-connection-details)
- [Sample Database](#-sample-database)
- [Files](#-files)
- [Common Commands](#-common-commands)
- [Customization](#-customization)
- [Troubleshooting](#-troubleshooting)
- [Sample Queries](#-sample-queries)

---

## 🚀 Quick Start

### Windows

```bash
setup-database.bat
```

### Linux/Mac

```bash
chmod +x setup-database.sh
./setup-database.sh
```

### Manual Setup

```bash
# Start SQL Server
docker compose up -d mssql

# Wait for healthy status (about 30 seconds)
docker compose ps

# Initialize database with sample data
docker compose --profile init up mssql-tools
```

---

## 🔌 Connection Details

| Setting | Value |
|---------|-------|
| Server | `localhost,1433` |
| Database | `ResearchAnalytics` |
| Username | `sa` |
| Password | `LocalLLM@2024!` |

> ⚠️ **Warning:** Change the default password for production use!

---

## 🗄️ Sample Database

### Database Schema

The `ResearchAnalytics` database contains sample data for a fictional research organization.

### Tables

| Table | Records | Description |
|-------|---------|-------------|
| `Departments` | 8 | Research departments (AI, ML, NLP, etc.) |
| `Researchers` | 23 | Team members with titles, salaries |
| `Projects` | 15 | Research projects with budgets, status |
| `ProjectAssignments` | - | Researcher-project assignments |
| `Publications` | 10 | Academic papers with citations |
| `PublicationAuthors` | - | Publication-researcher linking |
| `Datasets` | 10 | Research datasets with metadata |
| `Experiments` | 11 | ML experiments with results |
| `Funding` | 12 | Grants from funding sources |
| `Equipment` | 10 | Lab equipment inventory |

### Views

| View | Description |
|------|-------------|
| `vw_ActiveProjects` | Active projects with lead researcher info |
| `vw_ResearcherPublications` | Publication counts and citations per researcher |
| `vw_ProjectFunding` | Funding summary per project |

---

## 📁 Files

```
docker/
├── docker-compose.yml      # Main compose file
├── setup-database.bat      # Windows setup script
├── setup-database.sh       # Linux/Mac setup script
├── README.md               # This file
└── init/
    ├── 01-create-database.sql   # Creates ResearchAnalytics DB
    ├── 02-create-schema.sql     # Creates all tables and views
    └── 03-seed-data.sql         # Populates sample data
```

---

## 💻 Common Commands

### Container Management

| Command | Description |
|---------|-------------|
| `docker compose up -d mssql` | Start SQL Server |
| `docker compose logs -f mssql` | View logs |
| `docker compose down` | Stop (preserve data) |
| `docker compose down -v` | Stop and delete data |
| `docker compose ps` | Check status |

### Database Operations

```bash
# Reinitialize database (re-run all init scripts)
docker compose --profile init up mssql-tools

# Connect via Docker exec
docker exec -it local-llm-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -No -d ResearchAnalytics

# Quick test query
docker exec -it local-llm-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -No \
  -Q "SELECT COUNT(*) FROM ResearchAnalytics.dbo.Researchers"
```

---

## ⚙️ Customization

### Custom SA Password

Set `MSSQL_SA_PASSWORD` before starting:

```bash
# Option 1: Environment variable
export MSSQL_SA_PASSWORD=YourSecurePassword123!
docker compose up -d

# Option 2: In .env file
echo "MSSQL_SA_PASSWORD=YourSecurePassword123!" >> .env
docker compose up -d
```

### Custom Port

Edit `docker-compose.yml`:

```yaml
ports:
  - "1434:1433"  # Use external port 1434
```

---

## 🔧 Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Container won't start | Not enough memory | Increase Docker Desktop memory to 2GB+ |
| Database not initialized | Scripts didn't run | Run `docker compose --profile init up mssql-tools` |
| Permission denied (Linux) | Script not executable | `chmod +x setup-database.sh` |
| Port 1433 in use | Another SQL Server | Stop other instance or change port |

### Debugging Commands

```bash
# Check container logs
docker compose logs mssql

# Check container health
docker inspect local-llm-mssql --format='{{.State.Health.Status}}'

# Check what's using port 1433
netstat -an | grep 1433

# Interactive container shell
docker exec -it local-llm-mssql /bin/bash
```

### Reset Everything

```bash
# Stop and remove all data
docker compose down -v

# Remove image (optional, for full reset)
docker rmi mcr.microsoft.com/mssql/server:2022-latest

# Start fresh
docker compose up -d mssql
docker compose --profile init up mssql-tools
```

---

## 📊 Sample Queries

Once connected, try these queries to test the database:

### Schema Discovery

```sql
-- List all tables
SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE';

-- Describe a table
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Researchers';
```

### Basic Queries

```sql
-- Count researchers by department
SELECT d.DepartmentName, COUNT(*) as ResearcherCount
FROM Researchers r
JOIN Departments d ON r.DepartmentId = d.DepartmentId
GROUP BY d.DepartmentName
ORDER BY ResearcherCount DESC;

-- Top 5 highest paid researchers
SELECT TOP 5 FirstName, LastName, Title, Salary
FROM Researchers
ORDER BY Salary DESC;
```

### Using Views

```sql
-- Active projects with lead researcher
SELECT * FROM vw_ActiveProjects;

-- Researcher publication summary
SELECT * FROM vw_ResearcherPublications
ORDER BY TotalCitations DESC;

-- Project funding overview
SELECT * FROM vw_ProjectFunding;
```

### Analytical Queries

```sql
-- Department budget utilization
SELECT
    d.DepartmentName,
    d.Budget,
    SUM(p.ActualSpend) as TotalSpend,
    d.Budget - SUM(p.ActualSpend) as Remaining
FROM Departments d
JOIN Projects p ON d.DepartmentId = p.DepartmentId
GROUP BY d.DepartmentName, d.Budget;

-- Most cited publications
SELECT TOP 5
    Title,
    CitationCount,
    Journal,
    PublicationDate
FROM Publications
ORDER BY CitationCount DESC;
```

---

*Last Updated: December 2024*
