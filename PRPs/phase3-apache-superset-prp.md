# Phase 3: Apache Superset Integration

## Overview

| Attribute | Value |
|-----------|-------|
| **Phase** | 3 |
| **Focus** | Enterprise BI Platform Integration |
| **Estimated Effort** | 2-3 days |
| **Prerequisites** | Phase 2.5 complete |

## Goal

Add Apache Superset as an enterprise-grade business intelligence platform running alongside the existing React UI. Superset provides formal report creation, advanced SQL editing, scheduled reports, and embeddable dashboards for scenarios requiring dedicated BI tooling.

## Rationale

While Phase 2 delivers a fully functional React UI with dashboards and exports, some enterprise scenarios benefit from a dedicated BI platform:

| Use Case | React UI | Apache Superset |
|----------|----------|-----------------|
| Quick AI-driven queries | ✅ Primary | ⚠️ Manual SQL |
| Drag-drop dashboards | ✅ Built-in | ✅ Advanced |
| Scheduled email reports | ❌ | ✅ Native |
| SQL Lab exploration | ❌ | ✅ Full IDE |
| Role-based access | ❌ Phase 2 | ✅ Native |
| Formal BI governance | ⚠️ Basic | ✅ Enterprise |

**Demo Narrative:** "The AI-powered React interface handles natural language queries, while Superset provides traditional BI capabilities for formal reporting - giving you the best of both worlds, all running 100% locally."

## Success Criteria

- [ ] Superset container running at `localhost:8088`
- [ ] Admin user configured with secure password
- [ ] SQL Server datasource connected and queryable
- [ ] Sample dashboard created from Research Analytics data
- [ ] Superset dashboard embedded in React app via iframe
- [ ] Documentation for Superset usage complete
- [ ] All existing Phase 2 features continue working

## Technology Stack

### Docker Service

```yaml
# docker/docker-compose.yml - Add to existing services
services:
  # ... existing mssql, redis-stack, api services ...

  superset:
    image: apache/superset:3.1.0
    container_name: local-llm-superset
    ports:
      - "8088:8088"
    environment:
      - SUPERSET_SECRET_KEY=${SUPERSET_SECRET_KEY:-$(openssl rand -base64 42)}
      - SQLALCHEMY_DATABASE_URI=sqlite:////app/superset_home/superset.db
      - SUPERSET_LOAD_EXAMPLES=no
    volumes:
      - superset_home:/app/superset_home
      - ./superset/superset_config.py:/app/pythonpath/superset_config.py
    depends_on:
      mssql:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8088/health"]
      interval: 30s
      timeout: 10s
      retries: 5
    command: >
      bash -c "
        superset db upgrade &&
        superset fab create-admin --username admin --firstname Admin --lastname User --email admin@local.llm --password ${SUPERSET_ADMIN_PASSWORD:-LocalLLM@2024!} || true &&
        superset init &&
        superset run -h 0.0.0.0 -p 8088 --with-threads --reload
      "

volumes:
  mssql_data:
  redis_data:
  superset_home:
```

### Superset Configuration

```python
# docker/superset/superset_config.py
import os
from datetime import timedelta

# Basic config
ROW_LIMIT = 5000
SUPERSET_WEBSERVER_PORT = 8088

# Secret key - MUST be set in production
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'localllm_default_secret_key_change_me')

# Database for Superset metadata (NOT the analytics data)
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'SQLALCHEMY_DATABASE_URI',
    'sqlite:////app/superset_home/superset.db'
)

# Flask-WTF flag for CSRF
WTF_CSRF_ENABLED = True
WTF_CSRF_EXEMPT_LIST = []
WTF_CSRF_TIME_LIMIT = 60 * 60 * 24 * 365

# Session configuration
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = False  # Set to True if using HTTPS
SESSION_COOKIE_HTTPONLY = True

# Enable iframe embedding
PUBLIC_ROLE_LIKE = "Gamma"
SESSION_COOKIE_SAMESITE = "Lax"
ENABLE_CORS = True
CORS_OPTIONS = {
    'supports_credentials': True,
    'allow_headers': ['*'],
    'resources': ['*'],
    'origins': ['http://localhost:5173', 'http://localhost:8000']
}

# Allow embedding in iframes
HTTP_HEADERS = {
    'X-Frame-Options': 'ALLOWALL'
}
TALISMAN_ENABLED = False

# Feature flags
FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
    "DASHBOARD_NATIVE_FILTERS": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "DASHBOARD_NATIVE_FILTERS_SET": True,
    "ALERT_REPORTS": True,
    "EMBEDDED_SUPERSET": True,
    "EMBEDDABLE_CHARTS": True,
}

# SQL Lab configuration
SQLLAB_TIMEOUT = 300
SQLLAB_DEFAULT_DBID = 1

# Cache configuration (using Redis)
CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_KEY_PREFIX': 'superset_',
    'CACHE_REDIS_HOST': 'redis-stack',
    'CACHE_REDIS_PORT': 6379,
    'CACHE_REDIS_DB': 1,
}

FILTER_STATE_CACHE_CONFIG = CACHE_CONFIG
EXPLORE_FORM_DATA_CACHE_CONFIG = CACHE_CONFIG

# Logging
LOG_FORMAT = '%(asctime)s:%(levelname)s:%(name)s:%(message)s'
LOG_LEVEL = 'INFO'

# Theming (match our app's look)
THEME_OVERRIDES = {
    "borderRadius": 4,
    "colors": {
        "primary": {
            "base": 'rgb(59, 130, 246)',  # Blue-500
        },
        "secondary": {
            "base": 'rgb(100, 116, 139)',  # Slate-500
        },
    },
}
```

## Implementation Plan

### Step 1: Docker Setup

#### 1.1 Create Superset Directory Structure

```bash
mkdir -p docker/superset
```

#### 1.2 Create Superset Config

Save the `superset_config.py` content above to `docker/superset/superset_config.py`.

#### 1.3 Update docker-compose.yml

Add the Superset service to `docker/docker-compose.yml`.

#### 1.4 Environment Variables

Add to `.env`:

```bash
# Superset configuration
SUPERSET_SECRET_KEY=your_secure_random_key_here
SUPERSET_ADMIN_PASSWORD=LocalLLM@2024!
```

### Step 2: Initial Superset Setup

#### 2.1 Start Services

```bash
cd docker
docker-compose up -d superset
```

#### 2.2 Wait for Initialization

```bash
# Watch logs for completion
docker logs -f local-llm-superset

# Should see:
# "Starting gunicorn..."
# "Listening at: http://0.0.0.0:8088"
```

#### 2.3 Access Superset

- URL: `http://localhost:8088`
- Username: `admin`
- Password: Value of `SUPERSET_ADMIN_PASSWORD`

### Step 3: Configure SQL Server Datasource

#### 3.1 Install MSSQL Driver (One-time)

The Superset image needs the SQL Server driver:

```dockerfile
# docker/Dockerfile.superset (optional custom image)
FROM apache/superset:3.1.0

USER root
RUN apt-get update && \
    apt-get install -y gnupg curl && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev && \
    pip install pymssql

USER superset
```

Alternatively, use the Superset API or UI to configure:

#### 3.2 Add Database via Superset UI

1. Navigate to **Settings** → **Database Connections** → **+ Database**
2. Select **Microsoft SQL Server**
3. Enter connection details:
   - **Host**: `mssql` (Docker network name)
   - **Port**: `1433`
   - **Database**: `ResearchAnalytics`
   - **Username**: `sa`
   - **Password**: Value of `MSSQL_SA_PASSWORD`

4. SQLAlchemy URI format:
```
mssql+pymssql://sa:LocalLLM%402024!@mssql:1433/ResearchAnalytics
```

5. Test connection and save

#### 3.3 Add Database via API (Automation)

```python
# scripts/setup_superset.py
import requests
import os

SUPERSET_URL = "http://localhost:8088"
ADMIN_USER = "admin"
ADMIN_PASS = os.environ.get("SUPERSET_ADMIN_PASSWORD", "LocalLLM@2024!")

def get_access_token():
    """Login and get access token."""
    response = requests.post(
        f"{SUPERSET_URL}/api/v1/security/login",
        json={
            "username": ADMIN_USER,
            "password": ADMIN_PASS,
            "provider": "db",
            "refresh": True
        }
    )
    return response.json()["access_token"]

def add_database(token: str):
    """Add SQL Server database connection."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    mssql_password = os.environ.get("MSSQL_SA_PASSWORD", "LocalLLM@2024!")
    # URL encode special characters
    encoded_password = mssql_password.replace("@", "%40").replace("!", "%21")
    
    response = requests.post(
        f"{SUPERSET_URL}/api/v1/database/",
        headers=headers,
        json={
            "database_name": "Research Analytics",
            "engine": "mssql+pymssql",
            "sqlalchemy_uri": f"mssql+pymssql://sa:{encoded_password}@mssql:1433/ResearchAnalytics",
            "expose_in_sqllab": True,
            "allow_run_async": True,
            "allow_ctas": False,
            "allow_cvas": False,
            "allow_dml": False,
            "extra": '{"metadata_params": {}, "engine_params": {}}'
        }
    )
    return response.json()

def sync_tables(token: str, database_id: int):
    """Sync database tables to Superset."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{SUPERSET_URL}/api/v1/database/{database_id}/schemas/?",
        headers=headers
    )
    return response.json()

if __name__ == "__main__":
    token = get_access_token()
    print("Got access token")
    
    result = add_database(token)
    print(f"Database added: {result}")
    
    if "id" in result:
        sync_result = sync_tables(token, result["id"])
        print(f"Tables synced: {sync_result}")
```

### Step 4: Create Sample Dashboard

#### 4.1 SQL Lab Exploration

1. Navigate to **SQL Lab** → **SQL Editor**
2. Select "Research Analytics" database
3. Run sample queries:

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

4. Save queries for dashboard use

#### 4.2 Create Charts

1. Navigate to **Charts** → **+ Chart**
2. Select dataset (saved query or table)
3. Choose visualization type
4. Configure chart options
5. Save chart

**Recommended Charts:**
- Bar Chart: Funding by Department
- Line Chart: Publications Over Time
- Pie Chart: Projects by Status
- Big Number: Total Research Funding
- Table: Top Researchers by Publications

#### 4.3 Create Dashboard

1. Navigate to **Dashboards** → **+ Dashboard**
2. Name: "Research Analytics Overview"
3. Drag charts onto canvas
4. Configure layout
5. Add filters (department, date range)
6. Save and publish

### Step 5: Embed in React Application

#### 5.1 Backend Endpoint for Embed Token

```python
# src/local_llm_research_agent/api/routers/superset.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import os

router = APIRouter(prefix="/superset", tags=["superset"])

SUPERSET_URL = os.getenv("SUPERSET_URL", "http://localhost:8088")
SUPERSET_USER = os.getenv("SUPERSET_ADMIN_USER", "admin")
SUPERSET_PASS = os.getenv("SUPERSET_ADMIN_PASSWORD", "LocalLLM@2024!")

class EmbedResponse(BaseModel):
    embed_url: str
    dashboard_id: str

async def get_superset_token() -> str:
    """Get Superset access token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SUPERSET_URL}/api/v1/security/login",
            json={
                "username": SUPERSET_USER,
                "password": SUPERSET_PASS,
                "provider": "db"
            }
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to authenticate with Superset")
        return response.json()["access_token"]

@router.get("/dashboards")
async def list_dashboards():
    """List available Superset dashboards."""
    token = await get_superset_token()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPERSET_URL}/api/v1/dashboard/",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()

@router.get("/embed/{dashboard_id}")
async def get_embed_url(dashboard_id: int) -> EmbedResponse:
    """Get embeddable URL for a dashboard."""
    token = await get_superset_token()
    
    # Create guest token for embedding
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SUPERSET_URL}/api/v1/security/guest_token/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "user": {
                    "username": "embed_user",
                    "first_name": "Embed",
                    "last_name": "User"
                },
                "resources": [
                    {"type": "dashboard", "id": str(dashboard_id)}
                ],
                "rls": []
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail="Failed to create guest token"
            )
        
        guest_token = response.json()["token"]
    
    embed_url = f"{SUPERSET_URL}/embedded/{dashboard_id}?guest_token={guest_token}"
    
    return EmbedResponse(
        embed_url=embed_url,
        dashboard_id=str(dashboard_id)
    )

@router.get("/health")
async def superset_health():
    """Check Superset health."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{SUPERSET_URL}/health")
            return {"status": "healthy" if response.status_code == 200 else "unhealthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

#### 5.2 React Embed Component

```typescript
// frontend/src/components/superset/SupersetEmbed.tsx
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Loader2, ExternalLink, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '@/lib/api';

interface SupersetEmbedProps {
  dashboardId: number;
  title?: string;
  height?: string;
}

export function SupersetEmbed({ 
  dashboardId, 
  title = 'Superset Dashboard',
  height = '600px' 
}: SupersetEmbedProps) {
  const [refreshKey, setRefreshKey] = useState(0);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['superset-embed', dashboardId, refreshKey],
    queryFn: () => api.get(`/superset/embed/${dashboardId}`),
  });

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-96">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="ml-2">Loading dashboard...</span>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center h-96 text-destructive">
          <p>Failed to load Superset dashboard</p>
          <Button 
            variant="outline" 
            className="mt-4"
            onClick={() => refetch()}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle>{title}</CardTitle>
        <div className="flex gap-2">
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => setRefreshKey(k => k + 1)}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => window.open(data.embed_url.split('?')[0].replace('/embedded/', '/superset/dashboard/'), '_blank')}
          >
            <ExternalLink className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <iframe
          src={data.embed_url}
          width="100%"
          height={height}
          frameBorder="0"
          style={{ border: 'none' }}
          title={title}
          sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
        />
      </CardContent>
    </Card>
  );
}
```

#### 5.3 Superset Dashboards Page

```typescript
// frontend/src/pages/SupersetDashboardsPage.tsx
import { useQuery } from '@tanstack/react-query';
import { ExternalLink, BarChart3, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { SupersetEmbed } from '@/components/superset/SupersetEmbed';
import { api } from '@/lib/api';

export function SupersetDashboardsPage() {
  const { data: dashboards, isLoading } = useQuery({
    queryKey: ['superset-dashboards'],
    queryFn: () => api.get('/superset/dashboards'),
  });

  const [selectedDashboard, setSelectedDashboard] = useState<number | null>(null);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Superset Reports</h1>
          <p className="text-muted-foreground">
            Enterprise business intelligence dashboards powered by Apache Superset
          </p>
        </div>
        <Button 
          variant="outline"
          onClick={() => window.open('http://localhost:8088', '_blank')}
        >
          <ExternalLink className="h-4 w-4 mr-2" />
          Open Superset
        </Button>
      </div>

      {selectedDashboard ? (
        <div>
          <Button 
            variant="ghost" 
            onClick={() => setSelectedDashboard(null)}
            className="mb-4"
          >
            ← Back to list
          </Button>
          <SupersetEmbed 
            dashboardId={selectedDashboard}
            height="800px"
          />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {dashboards?.result?.map((dashboard: any) => (
            <Card 
              key={dashboard.id}
              className="cursor-pointer hover:border-primary transition-colors"
              onClick={() => setSelectedDashboard(dashboard.id)}
            >
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  {dashboard.dashboard_title}
                </CardTitle>
                <CardDescription>
                  {dashboard.description || 'No description'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-muted-foreground">
                  <p>Created: {new Date(dashboard.created_on).toLocaleDateString()}</p>
                  <p>Charts: {dashboard.charts?.length || 0}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
```

#### 5.4 Add Route

```typescript
// frontend/src/App.tsx - Add route
import { SupersetDashboardsPage } from '@/pages/SupersetDashboardsPage';

// In routes:
{
  path: '/superset',
  element: <SupersetDashboardsPage />,
}
```

#### 5.5 Add Sidebar Link

```typescript
// frontend/src/components/layout/Sidebar.tsx - Add to navigation
{
  name: 'Superset Reports',
  href: '/superset',
  icon: BarChart3,
}
```

### Step 6: Documentation

#### 6.1 User Guide

Create `docs/superset-guide.md`:

```markdown
# Apache Superset User Guide

## Overview

Apache Superset provides enterprise-grade business intelligence capabilities 
alongside the AI-powered Research Analytics application.

## Accessing Superset

- **URL**: http://localhost:8088
- **Default credentials**: admin / [your password]

## Key Features

### SQL Lab
- Full SQL editor with syntax highlighting
- Query history and saved queries
- Export results to CSV

### Charts
- 40+ visualization types
- Drag-and-drop configuration
- Time series analysis
- Geographic mapping

### Dashboards
- Combine multiple charts
- Cross-filtering
- Native filters
- Scheduled email reports

## Creating a Dashboard

1. **Create Charts First**
   - SQL Lab → Save Query
   - Charts → New Chart
   - Select saved query or table
   - Configure visualization

2. **Build Dashboard**
   - Dashboards → New Dashboard
   - Drag charts onto canvas
   - Add filters
   - Configure refresh interval

3. **Publish**
   - Set permissions
   - Enable embedding if needed

## Embedding in React App

Dashboards can be embedded in the React application:

1. Open Superset dashboard
2. Publish and enable embedding
3. View in React app under "Superset Reports"

## Best Practices

- Use meaningful chart names
- Add descriptions to dashboards
- Configure appropriate refresh intervals
- Use filters for interactivity
```

### Step 7: Health Check Integration

#### 7.1 Add to Health Endpoint

```python
# Update src/local_llm_research_agent/api/routers/health.py
from .superset import superset_health

@router.get("/")
async def health_check():
    """Comprehensive health check for all services."""
    results = await asyncio.gather(
        check_sql_server(),
        check_redis(),
        check_ollama(),
        superset_health(),
        return_exceptions=True
    )
    
    return {
        "status": "healthy" if all(r.get("status") == "healthy" for r in results if isinstance(r, dict)) else "degraded",
        "services": {
            "sql_server": results[0],
            "redis": results[1],
            "ollama": results[2],
            "superset": results[3]
        },
        "timestamp": datetime.utcnow().isoformat()
    }
```

#### 7.2 Update Onboarding Wizard

```typescript
// Add Superset to health check in onboarding wizard
const services = [
  { name: 'SQL Server', endpoint: '/health/sql' },
  { name: 'Redis', endpoint: '/health/redis' },
  { name: 'Ollama', endpoint: '/health/ollama' },
  { name: 'Superset', endpoint: '/superset/health' },
];
```

## File Structure

```
docker/
├── docker-compose.yml          # Updated with Superset service
├── superset/
│   └── superset_config.py      # Superset configuration
├── Dockerfile.superset         # Optional custom Superset image
└── .env                        # Environment variables

src/local_llm_research_agent/
└── api/
    └── routers/
        └── superset.py         # Superset API endpoints

frontend/
└── src/
    ├── components/
    │   └── superset/
    │       └── SupersetEmbed.tsx
    └── pages/
        └── SupersetDashboardsPage.tsx

docs/
└── superset-guide.md           # User documentation

scripts/
└── setup_superset.py           # Automation script
```

## Environment Variables

Add to `.env`:

```bash
# Superset
SUPERSET_URL=http://localhost:8088
SUPERSET_SECRET_KEY=your_secure_random_key_minimum_42_chars
SUPERSET_ADMIN_USER=admin
SUPERSET_ADMIN_PASSWORD=LocalLLM@2024!
```

## Testing Checklist

### Docker Setup
- [ ] `docker-compose up superset` starts successfully
- [ ] Superset accessible at localhost:8088
- [ ] Admin login works
- [ ] Health endpoint returns healthy

### Database Connection
- [ ] SQL Server datasource added
- [ ] Tables visible in SQL Lab
- [ ] Queries execute successfully
- [ ] No authentication errors

### Dashboard Creation
- [ ] Charts can be created from queries
- [ ] Dashboard saves correctly
- [ ] Filters work
- [ ] Refresh works

### Embedding
- [ ] Guest token generated successfully
- [ ] Iframe loads in React app
- [ ] Dashboard interactive in iframe
- [ ] No CORS errors

### Integration
- [ ] Health check includes Superset
- [ ] Sidebar link works
- [ ] External link opens Superset

## Troubleshooting

### "Failed to authenticate with Superset"
- Verify Superset container is running
- Check admin credentials in .env
- Ensure Superset initialization completed

### "Database connection failed"
- Verify SQL Server is accessible from Superset container
- Check network connectivity: `docker exec local-llm-superset ping mssql`
- Verify pymssql driver is installed

### "Iframe not loading"
- Check CORS configuration in superset_config.py
- Verify X-Frame-Options set to ALLOWALL
- Check browser console for errors

### "Guest token creation failed"
- Ensure FEATURE_FLAGS includes EMBEDDED_SUPERSET
- Check dashboard has publish permissions
- Verify PUBLIC_ROLE_LIKE is set

## Rollback Plan

If Superset integration causes issues:

1. Stop Superset: `docker-compose stop superset`
2. Remove from health checks
3. Hide sidebar link (feature flag)
4. All other features continue working

## Notes

- Superset is optional - all Phase 2 features work without it
- Superset uses its own SQLite database for metadata
- Redis cache shared with main application (different DB number)
- Consider Superset-specific backup for production use
