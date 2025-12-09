# 🔐 Security Policy

> **Security guidelines and vulnerability reporting for the Local LLM Research Agent**

---

## 📑 Table of Contents

- [Supported Versions](#-supported-versions)
- [Reporting a Vulnerability](#-reporting-a-vulnerability)
- [Security Best Practices](#-security-best-practices)
- [Known Security Considerations](#-known-security-considerations)
- [Security Updates](#-security-updates)

---

## ✅ Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x.x | ✅ Active support |
| < 1.0 | ❌ No support |

---

## 🚨 Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

| Step | Action |
|------|--------|
| 1 | ❌ **DO NOT** create a public GitHub issue |
| 2 | 📧 Email security concerns to maintainers privately |
| 3 | 📝 Include detailed information (see below) |

### Information to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### What to Expect

| Timeline | Response |
|----------|----------|
| 48 hours | Acknowledgment of receipt |
| 7 days | Vulnerability assessment and severity rating |
| 30 days | Resolution for critical vulnerabilities |
| Release | Credit in release notes (unless you prefer anonymity) |

---

## 🏆 Security Best Practices

### ⚙️ Environment Variables

| Practice | Status | Description |
|----------|--------|-------------|
| Never commit `.env` files | 🔴 Critical | Use `.gitignore` |
| Use `.env.example` as template | ✅ Recommended | Safe documentation |
| Rotate credentials regularly | ✅ Recommended | Limit exposure |
| Strong SQL Server passwords | 🔴 Critical | Avoid defaults |

```bash
# ❌ Bad - default password
MSSQL_SA_PASSWORD=LocalLLM@2024!

# ✅ Good - strong unique password
MSSQL_SA_PASSWORD=YourSecure!P@ssw0rd#2024
```

### 🗄️ SQL Server Security

| Practice | Priority | Description |
|----------|----------|-------------|
| Windows Authentication | ✅ Preferred | More secure than SQL auth |
| Use `READONLY=true` | 🔴 High | Safe exploration mode |
| Minimum permissions | 🔴 High | Principle of least privilege |
| Regular updates | 🟡 Medium | Security patches |

```bash
# Enable read-only mode for safe exploration
MCP_MSSQL_READONLY=true
```

### 🖥️ Local Deployment

| Practice | Priority | Description |
|----------|----------|-------------|
| Localhost only for Ollama | ✅ Default | No external exposure |
| Don't expose Streamlit publicly | 🔴 High | Port 8501 |
| Firewall SQL Server port | 🔴 High | Port 1433 |
| Update dependencies | 🟡 Medium | Regular updates |

### 🐳 Docker Security

| Practice | Priority | Description |
|----------|----------|-------------|
| Change default password | 🔴 Critical | Never use `LocalLLM@2024!` in production |
| Use `.env` for credentials | ✅ Recommended | Don't hardcode |
| Review `docker-compose.yml` | 🟡 Medium | Before deploying |
| Keep images updated | 🟡 Medium | Pull latest versions |

---

## ⚠️ Known Security Considerations

### 🦙 Local LLM (Ollama)

| Consideration | Risk Level | Mitigation |
|---------------|------------|------------|
| Local-only inference | ✅ Low | No external data transfer |
| Unexpected model output | 🟡 Medium | Review generated content |
| SQL injection potential | 🔴 High | Validate generated SQL |

> 💡 **Tip:** All inference runs locally via Ollama - no data is sent to external APIs.

### 🔌 MCP Server Communication

| Consideration | Risk Level | Mitigation |
|---------------|------------|------------|
| Stdio communication | ✅ Low | Local process only |
| No network exposure | ✅ Low | Default configuration |
| Third-party code | 🟡 Medium | Review MCP server source |

### 📊 SQL Query Generation

| Consideration | Risk Level | Mitigation |
|---------------|------------|------------|
| Natural language to SQL | 🔴 High | Review generated queries |
| Data modification | 🔴 High | Use read-only mode |
| Audit trails | 🟡 Medium | Implement query logging |

```python
# ✅ Always validate generated SQL
if "DROP" in generated_sql or "DELETE" in generated_sql:
    raise SecurityError("Dangerous SQL operation blocked")
```

---

## 🔄 Security Updates

Security updates are released as patch versions.

### Stay Updated

| Method | Action |
|--------|--------|
| GitHub Releases | Watch repository for notifications |
| Dependabot | Automatic dependency vulnerability alerts |
| Security Advisories | Monitor for CVEs in dependencies |

---

## 📚 Dependencies

We monitor dependencies for known vulnerabilities:

| Tool | Purpose |
|------|---------|
| GitHub Dependabot | Automated vulnerability scanning |
| Regular audits | Periodic manual review |
| Quick patches | Critical updates prioritized |

---

*Last Updated: December 2024*
