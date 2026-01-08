# ⚠️ SKILLS-FIRST RULE - READ THIS EVERY SESSION

## The Golden Rule

**NEVER implement ANYTHING without checking if a skill exists first!**

## Why This Matters

You have access to **169 expert skill files** covering nearly every technology in this project. Each skill contains:
- Best practices and patterns
- Common pitfalls to avoid
- Code examples
- Expert guidance

**Implementing without checking skills = Reinventing the wheel poorly**

## How to Check Skills

### 1. Identify What You Need
Ask: "What technology or pattern am I working with?"
- Working with Pydantic AI? → Check `pydantic-ai` skill
- Building React components? → Check `react-typescript` skill
- Designing prompts? → Check `prompt-engineering` skill
- Optimizing context? → Check `context-engineering` skill

### 2. Check If Skill Exists
```powershell
Get-ChildItem "C:\Users\frgarofa\.claude\skills" | Where-Object { $_.Name -match "[keyword]" }
```

### 3. Read The Skill
```powershell
Get-Content "C:\Users\frgarofa\.claude\skills\[skill-name]\SKILL.md"
```

### 4. Apply The Patterns
Use the skill's guidance in your implementation. Reference it in decisions.

## Available Skills (169 Total)

### AI & LLM
- `pydantic-ai` - Pydantic AI framework patterns
- `ollama` - Local LLM with Ollama
- `langchain` - LangChain framework
- `llamaindex` - LlamaIndex patterns
- `autogen` - AutoGen multi-agent
- `crewai` - CrewAI orchestration
- `guidance` - Microsoft Guidance
- `instructor` - Structured outputs
- `semantic-kernel` - Semantic Kernel
- `dspy` - DSPy framework
- `openai-api` - OpenAI API usage
- `anthropic-claude-api` - Claude API
- `huggingface` - HuggingFace models

### MCP & Integration
- `mcp-development` - MCP server development
- `mssql-mcp` - SQL Server MCP
- `mongodb-mcp` - MongoDB MCP
- `postgresql-mcp` - PostgreSQL MCP
- `playwright-mcp` - Browser automation MCP
- `azure-mcp` - Azure services MCP
- `fabric-rti-mcp` - Fabric RTI MCP

### RAG & Vector
- `rag-patterns` - RAG pipeline patterns
- `vector-databases` - Vector DB patterns
- `elasticsearch` - Elasticsearch
- `clickhouse` - ClickHouse
- `redis-cache` - Redis caching

### Frontend
- `react-typescript` - React + TypeScript
- `react-native` - React Native
- `nextjs-app-router` - Next.js App Router
- `tailwind-ui` - Tailwind CSS
- `component-library` - Component design
- `state-management` - State patterns
- `responsive-design` - Responsive UI
- `ui-ux-principles` - UX design

### Backend & API
- `fastapi` - FastAPI patterns (if exists)
- `nodejs` - Node.js patterns (if exists)
- `openapi-swagger` - API documentation
- `rest-api` - REST patterns (if exists)
- `graphql` - GraphQL (if exists)

### Database
- `mongodb-mcp` - MongoDB
- `postgresql-mcp` - PostgreSQL
- `mssql-mcp` - SQL Server
- `redis-cache` - Redis
- `neo4j` - Graph databases
- `influxdb` - Time series

### Testing
- `pytest-advanced` - Advanced pytest
- `jest` - JavaScript testing
- `cypress` - E2E testing
- `playwright-mcp` - Browser testing
- `selenium` - Web testing
- `frontend-testing` - Frontend test patterns

### DevOps & Infrastructure
- `docker-kubernetes` - Container orchestration
- `terraform-iac` - Terraform IaC
- `pulumi-iac` - Pulumi IaC
- `github-actions` - CI/CD workflows
- `azure-devops-pipelines` - Azure Pipelines
- `helm-charts` - Kubernetes Helm
- `kustomize` - Kustomize configs
- `argocd` - GitOps with ArgoCD
- `flux-cd` - Flux continuous delivery

### Azure Services
- `azure-ai` - Azure AI services
- `azure-aks` - Azure Kubernetes
- `azure-functions` - Serverless functions
- `azure-cosmos-db` - Cosmos DB
- `azure-container-apps` - Container Apps
- `azure-static-web-apps` - Static Web Apps
- `azure-service-bus` - Service Bus messaging
- `azure-event-grid` - Event Grid
- `microsoft-fabric` - Microsoft Fabric

### Prompt & Context Engineering
- `prompt-engineering` - Prompt design patterns
- `context-engineering` - Context optimization
- `agentic-workflows` - Agent workflows

### Data & ML
- `pandas` - Data manipulation
- `dbt` - Data transformation
- `mlflow` - ML lifecycle
- `jupyter` - Jupyter notebooks
- `data-visualization` - Viz patterns

### Other Technologies
- `streamlit-dashboards` - Streamlit apps
- `git-advanced` - Advanced Git
- `github` - GitHub features
- `ansible` - Configuration management
- `packer` - Image building
- `grafana-dashboards` - Monitoring dashboards
- `prometheus` - Metrics collection

## Pre-Task Checklist

Before starting ANY implementation:

```
[ ] 1. What technology/pattern am I using?
[ ] 2. Does a skill exist for this? (Check skills directory)
[ ] 3. Have I read the SKILL.md file?
[ ] 4. Am I applying the patterns from the skill?
[ ] 5. Can I reference the skill in my implementation notes?
```

## Session Start Ritual

**Every session, remind yourself:**
1. Read `.context/SESSION_MEMORY.md`
2. Read `.context/SKILLS_REMINDER.md` (this file)
3. Query Archon for active tasks
4. When starting work, CHECK SKILLS FIRST

## Violation = Immediate Stop

If you catch yourself implementing without checking skills:
1. STOP immediately
2. Check for relevant skill
3. Read the skill
4. Restart implementation with skill guidance

## Remember

**You have 169 expert consultants available. Use them!**

Don't reinvent wheels. Don't miss best practices. Don't skip expert guidance.

**SKILLS FIRST. ALWAYS.**
