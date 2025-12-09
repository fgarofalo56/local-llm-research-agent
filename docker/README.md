# Docker Setup for Local LLM Research Agent

This directory contains Docker configuration for running SQL Server 2022 with sample data for testing the Local LLM Research Agent.

## Quick Start

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

# Wait for healthy status
docker compose ps

# Initialize database with sample data
docker compose --profile init up mssql-tools
```

## Connection Details

| Setting | Value |
|---------|-------|
| Server | `localhost,1433` |
| Database | `ResearchAnalytics` |
| Username | `sa` |
| Password | `LocalLLM@2024!` |

## Sample Database Schema

### Tables

| Table | Description |
|-------|-------------|
| `Departments` | 8 research departments (AI, ML, NLP, CV, etc.) |
| `Researchers` | 23 team members with titles, salaries, specializations |
| `Projects` | 15 research projects with budgets, status, priorities |
| `ProjectAssignments` | Many-to-many researcher-project assignments |
| `Publications` | 10 academic papers with citations, DOIs |
| `PublicationAuthors` | Many-to-many publication-researcher linking |
| `Datasets` | 10 research datasets with size, format metadata |
| `Experiments` | 11 ML experiments with hypotheses and results |
| `Funding` | 12 grants from various funding sources |
| `Equipment` | 10 pieces of lab equipment |

### Views

| View | Description |
|------|-------------|
| `vw_ActiveProjects` | Active projects with lead researcher info |
| `vw_ResearcherPublications` | Publication counts and citations per researcher |
| `vw_ProjectFunding` | Funding summary per project |

## Files

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

## Common Commands

```bash
# Start SQL Server
docker compose up -d mssql

# View logs
docker compose logs -f mssql

# Stop (preserve data)
docker compose down

# Stop and delete all data
docker compose down -v

# Reinitialize database
docker compose --profile init up mssql-tools

# Connect via Docker exec
docker exec -it local-llm-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "LocalLLM@2024!" -No -d ResearchAnalytics
```

## Customizing Password

Set `MSSQL_SA_PASSWORD` environment variable or add to `.env`:

```bash
# In shell
export MSSQL_SA_PASSWORD=YourSecurePassword123!
docker compose up -d

# Or in .env file
MSSQL_SA_PASSWORD=YourSecurePassword123!
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker compose logs mssql

# Common issue: not enough memory (SQL Server needs 2GB+)
# Increase Docker Desktop memory allocation
```

### Database not initialized
```bash
# Re-run init scripts
docker compose --profile init up mssql-tools
```

### Permission denied on Linux
```bash
chmod +x setup-database.sh
```

### Port 1433 already in use
```bash
# Check what's using the port
netstat -an | grep 1433

# Or use a different port in docker-compose.yml
ports:
  - "1434:1433"  # Use 1434 externally
```

## Sample Queries

Once connected, try these queries:

```sql
-- List all tables
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE';

-- Count researchers by department
SELECT d.DepartmentName, COUNT(*) as ResearcherCount
FROM Researchers r
JOIN Departments d ON r.DepartmentId = d.DepartmentId
GROUP BY d.DepartmentName
ORDER BY ResearcherCount DESC;

-- Active projects with budgets
SELECT * FROM vw_ActiveProjects;

-- Top cited publications
SELECT TOP 5 Title, CitationCount, Journal
FROM Publications
ORDER BY CitationCount DESC;
```
