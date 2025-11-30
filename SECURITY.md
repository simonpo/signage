# Security Policy

## Supported Versions

Currently supported versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.7.x   | :white_check_mark: |
| < 0.7   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly:

### Private Disclosure

**Do not** open a public GitHub issue for security vulnerabilities.

Instead, please report security issues via one of these methods:

1. **GitHub Security Advisories** (preferred)
   - Navigate to the Security tab
   - Click "Report a vulnerability"
   - Provide detailed information about the issue

2. **Email** (alternative)
   - Contact the maintainer directly
   - Include detailed steps to reproduce
   - Provide affected versions

### What to Include

When reporting a vulnerability, please include:

- Description of the vulnerability
- Steps to reproduce the issue
- Affected versions
- Potential impact assessment
- Suggested fix (if known)

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Varies by severity
  - Critical: 7-14 days
  - High: 14-30 days
  - Medium: 30-60 days
  - Low: Best effort

## Security Considerations

### API Keys and Credentials

This project integrates with multiple third-party services requiring API credentials:

- **Tesla Fleet API** - Vehicle access and control
- **Weather APIs** - OpenWeatherMap, Ambient Weather
- **Sports APIs** - football-data.org, etc.

**Important:**
- All credentials are stored in `.env` files (gitignored)
- Never commit API keys, tokens, or passwords
- Use `.env.example` as a template only
- Rotate credentials immediately if exposed

### Token Storage

OAuth tokens (e.g., Tesla tokens) are stored in local files:
- `.tesla_tokens.json` - Automatically gitignored
- Contains access and refresh tokens
- Automatically refreshed by the client

### Network Security

**If exposing Tesla OAuth endpoints:**
- Use HTTPS only (via reverse proxy like Caddy/Nginx)
- Configure proper firewall rules
- Use authentication on reverse proxy if possible
- Follow Tesla's OAuth security requirements

### Samsung Frame TV Integration

The TV upload feature uses local network communication:
- WebSocket connection to TV on local network
- First connection requires manual approval on TV
- TV tokens stored in `tv-token.txt` (gitignored)

**Recommendations:**
- Keep TV on isolated VLAN if concerned about security
- Only run upload script on trusted networks
- TV firmware should be kept up-to-date

### Dependencies

This project uses multiple third-party Python packages:
- Regularly update dependencies for security patches
- Review `requirements.txt` for known vulnerabilities
- CI/CD checks run on all commits

**Monitor for vulnerabilities:**
```bash
pip install pip-audit
pip-audit
```

### Docker Considerations

If running in Docker (future enhancement):
- Use non-root user
- Minimal base image (Alpine/slim)
- Mount `.env` as read-only volume
- Regularly update base images

## Best Practices for Users

1. **Credential Rotation**
   - Rotate API keys periodically (every 90 days recommended)
   - Use separate API keys for development vs production
   - Revoke unused tokens immediately

2. **Local Development**
   - Never commit `.env` or token files
   - Use `.env.example` for sharing configuration templates
   - Clear sensitive data from logs before sharing

3. **Production Deployment**
   - Use systemd service with restricted permissions
   - Run as dedicated user (not root)
   - Protect log files containing API responses
   - Use secrets management (Vault, AWS Secrets Manager) for sensitive deployments

4. **Tesla-Specific Security**
   - Tesla Fleet API requires OAuth 2.0
   - Tokens grant vehicle control - protect carefully
   - Use Tesla's virtual key feature appropriately
   - Review Tesla's security best practices

## Known Security Considerations

### API Rate Limiting

Clients implement retry logic and backoff:
- Prevents accidental API abuse
- Circuit breaker pattern for external services
- Configurable timeout and retry limits

### Error Handling

Errors are logged but sensitive data is masked:
- API keys not logged
- OAuth tokens not logged
- Personal data redacted in error messages

### File Permissions

Generated images and logs may contain sensitive data:
- Ensure proper file permissions on output directories
- Consider encrypting at-rest for sensitive deployments
- Implement log rotation to limit data retention

## Disclosure Policy

Once a security issue is fixed:
- Users will be notified via GitHub releases
- CVE may be requested for critical vulnerabilities
- Credit given to reporter (if desired)
- Details published after users have time to update

## Contact

For security concerns, use GitHub Security Advisories or contact the maintainer privately.

For general questions, use GitHub Issues or Discussions.
