# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in this project, please report it responsibly.

### How to Report

1. **DO NOT** create a public GitHub issue for security vulnerabilities
2. Email security concerns to the repository maintainers privately
3. Include as much detail as possible:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt within 48 hours
- **Assessment**: We will assess the vulnerability and determine severity within 7 days
- **Resolution**: Critical vulnerabilities will be addressed within 30 days
- **Credit**: We will credit reporters in release notes (unless you prefer anonymity)

## Security Best Practices for Users

### Environment Variables

- **NEVER** commit `.env` files to version control
- Use `.env.example` as a template only
- Rotate credentials regularly
- Use strong passwords for SQL Server authentication

### SQL Server Security

- Prefer Windows Authentication over SQL Server Authentication when possible
- Use the `READONLY=true` setting when exploring data
- Grant minimum necessary permissions to database users
- Keep SQL Server updated with security patches

### Local Deployment

- Run Ollama on localhost only (default configuration)
- Do not expose the Streamlit port (8501) to the public internet
- Use firewall rules to restrict access to SQL Server port (1433)
- Keep all dependencies updated

### Docker Security

- Do not use the default `LocalLLM@2024!` password in production
- Set `MSSQL_SA_PASSWORD` via environment variable or `.env` file
- Review the `docker-compose.yml` before deploying
- Keep Docker and images updated

## Known Security Considerations

### Local LLM (Ollama)

- All inference runs locally - no data sent to external APIs
- Model responses may contain unexpected content
- Validate and sanitize any generated SQL before execution

### MCP Server Communication

- MCP servers communicate via stdio (local process)
- No network exposure by default
- Review MCP server source code before use

### SQL Queries

- The agent generates SQL based on natural language
- Always review generated queries before execution
- Use read-only mode for exploration
- Implement query logging for audit trails

## Security Updates

Security updates will be released as patch versions. Subscribe to repository releases to be notified of security fixes.

## Dependencies

We monitor dependencies for known vulnerabilities using GitHub's Dependabot. Critical dependency updates are prioritized.
