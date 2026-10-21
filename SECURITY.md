# Security Documentation

## Overview

This document describes the security architecture, threat model, and protective measures implemented in the WhatsApp Automation Platform.

## Threat Model

### Assets Protected
- **User credentials** (passwords, JWT tokens)
- **WhatsApp credentials** (access tokens, app secrets, webhook verify tokens)
- **Customer data** (phone numbers, messages, conversations)
- **Business data** (workflows, templates, contacts)
- **API keys** for external integrations

### Threat Actors
1. **External attackers** - Unauthenticated internet actors
2. **Compromised user accounts** - Credential stuffing, phishing
3. **Malicious insiders** - Authorized users exceeding permissions
4. **Supply chain** - Compromised dependencies, container images

### Attack Vectors
| Vector | Mitigation |
|--------|------------|
| Credential theft | bcrypt + JWT with short expiry, org-scoped tokens |
| SQL injection | SQLAlchemy ORM, parameterized queries |
| XSS | React auto-escaping, CSP headers |
| CSRF | SameSite cookies, JWT in Authorization header |
| SSRF | URL allowlist for outbound HTTP, no user-controlled URLs |
| Webhook spoofing | HMAC-SHA256 signature verification |
| Secret leakage | Fernet encryption at rest, never in logs |
| Token replay | Short JWT expiry (30 min), org-scoped |
| Privilege escalation | Org-level authorization on every request |

## Security Controls

### Authentication & Authorization

#### Password Security
- **Algorithm**: bcrypt (via passlib) with default cost factor
- **Minimum length**: 12 characters
- **No password reuse**: Not enforced (can be added)

#### JWT Tokens
- **Algorithm**: HS256
- **Expiry**: 30 minutes (configurable via `APP_ACCESS_TOKEN_MINUTES`)
- **Claims**: `sub` (user_id), `org` (organization_id), `exp`
- **Storage**: HTTP-only cookies or Authorization header
- **Rotation**: New token on login, old tokens invalidated implicitly

#### Organization-Level Authorization
- Every database query includes `organization_id` filter
- API dependencies extract `organization_id` from JWT
- Row-level checks on all mutating operations
- Webhook processing resolves org from phone_number_id

#### Role-Based Access Control
| Role | Permissions |
|------|-------------|
| admin | Full org access, manage members, manage accounts |
| member | Read/write contacts, conversations, workflows |
| viewer | Read-only access |

### Data Protection

#### Encryption at Rest
- **WhatsApp credentials**: Fernet (AES-256) encryption
- **Encryption key**: 32-byte base64 key from `ENCRYPTION_KEY` env var
- **Key derivation**: PBKDF2-HMAC-SHA256 (100k iterations) if key not 32 bytes
- **Database**: PostgreSQL on encrypted volumes (infrastructure responsibility)

#### Encryption in Transit
- **API**: HTTPS/TLS 1.3 (terminated at reverse proxy)
- **Database**: TLS (managed PostgreSQL)
- **Redis**: TLS (managed Redis)
- **WhatsApp API**: HTTPS only

#### Secrets Management
- **Never committed**: `.env` in `.gitignore`
- **Production**: Use secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.)
- **Docker**: Secrets via `docker secret` or env vars at runtime
- **Key rotation**: Manual process (re-encrypt with new key)

#### Data Minimization
- Message bodies not logged by default
- PII (phone numbers) only stored as needed
- Webhook payloads processed and discarded after persistence
- Audit logs exclude sensitive fields

### Webhook Security

#### Signature Verification
```python
# HMAC-SHA256 verification
expected = hmac.new(
    app_secret.encode(),
    json.dumps(payload, separators=(",", ":")).encode(),
    hashlib.sha256
).hexdigest()
hmac.compare_digest(expected, provided)
```

#### Replay Protection
- Meta includes timestamp in payload
- Reject payloads older than 5 minutes (configurable)
- Idempotency via message ID deduplication

#### Payload Validation
- Strict JSON schema validation
- Size limits on incoming requests
- Rate limiting per IP/account

### Network Security

#### CORS Policy
- Configurable origins via `APP_CORS_ORIGINS`
- Credentials allowed only for known origins
- No wildcard origins in production

#### Rate Limiting
- Not yet implemented (planned for Phase 7)
- Recommended: Per-IP, per-user, per-org limits

#### HTTP Security Headers
Implemented via Nginx in production:
- `Strict-Transport-Security`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy`
- `Referrer-Policy: strict-origin-when-cross-origin`

### Dependency Security

#### Supply Chain
- **pinned versions** in `requirements.txt` and `package.json`
- **No unpinned dependencies**
- **Regular updates** via Dependabot/Renovate
- **Vulnerability scanning**: `pip-audit`, `npm audit`

#### Container Security
- Non-root user in containers (`app` user)
- Minimal base images (python:3.12-slim, node:22-alpine)
- No unnecessary packages
- Read-only root filesystem where possible

### Audit Logging

#### Events Logged
- Authentication (login, logout, failed attempts)
- Authorization failures
- WhatsApp account CRUD
- Message sending (metadata only)
- Webhook processing
- Organization membership changes
- Role changes

#### Log Format
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "info",
  "event": "whatsapp_account_created",
  "user_id": "uuid",
  "organization_id": "uuid",
  "request_id": "correlation-id",
  "ip": "192.0.2.1"
}
```

#### Log Protection
- No PII in logs (phone numbers, message content redacted)
- Structured JSON for SIEM ingestion
- Retention: 90 days minimum

## Incident Response

### Security Incident Classification
| Severity | Examples | Response Time |
|----------|----------|---------------|
| Critical | Active breach, credential leak | < 1 hour |
| High | Auth bypass, data exposure | < 4 hours |
| Medium | Vulnerability, failed attacks | < 24 hours |
| Low | Info disclosure, config issues | < 7 days |

### Response Procedures
1. **Detect**: Alert from monitoring, log analysis, user report
2. **Contain**: Revoke tokens, disable accounts, block IPs
3. **Eradicate**: Patch vulnerability, rotate secrets
4. **Recover**: Restore from clean backup if needed
5. **Post-mortem**: Document, improve controls

### Credential Rotation
- **JWT secret**: Rotate quarterly, invalidate all sessions
- **Encryption key**: Annual rotation with re-encryption
- **WhatsApp tokens**: Per Meta policy (60 days)
- **Database passwords**: Per infrastructure policy

## Compliance Considerations

### GDPR (EU)
- **Lawful basis**: Legitimate interest (business communication)
- **Data subject rights**: Export/delete via API
- **Data processing agreement**: Required with Meta
- **Retention**: Configurable per org, default 2 years
- **DPO**: Assign if required by volume

### SOC 2 Type II
- **Security**: Implemented controls above
- **Availability**: Multi-AZ deployment, health checks
- **Confidentiality**: Encryption, access controls
- **Processing Integrity**: Idempotency, audit logs
- **Privacy**: Data minimization, consent tracking

### Industry Standards
- **OWASP Top 10**: Addressed via controls above
- **NIST CSF**: Identify, Protect, Detect, Respond, Recover
- **ISO 27001**: Aligned controls (not certified)

## Secure Development Practices

### Code Review Requirements
- All changes via PR with review
- Security-focused review for auth/crypto changes
- Static analysis in CI (ruff, mypy, npm audit)

### Testing
- Unit tests for auth, encryption, webhook verification
- Integration tests for API endpoints
- Penetration testing annually (planned)

### Secure Defaults
- `WHATSAPP_MOCK_MODE=true` in development
- Debug endpoints disabled in production
- No sample data in production
- Secure cookie settings (HttpOnly, Secure, SameSite)

## Security Checklist for Deployments

- [ ] `APP_SECRET_KEY` ≥ 32 random chars
- [ ] `ENCRYPTION_KEY` 32-byte base64
- [ ] HTTPS enforced everywhere
- [ ] Database TLS enabled
- [ ] Redis TLS enabled
- [ ] Secrets in vault, not env vars
- [ ] CORS restricted to known domains
- [ ] Rate limiting configured
- [ ] Monitoring/alerting active
- [ ] Backup encryption verified
- [ ] Incident response plan tested
- [ ] Dependency scan clean

## Reporting Security Issues

**Do not file public issues for security vulnerabilities.**

Email: security@yourdomain.com (configure in production)

Include:
- Description of vulnerability
- Steps to reproduce
- Impact assessment
- Suggested fix (if any)

We aim to acknowledge within 24 hours and provide timeline for fix.

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-10-20 | Initial security documentation |