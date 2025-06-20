# GitHub Token Management Documentation
## GitBridge Token Management Protocol v2

### Token Registry Overview

| Token Alias | Created       | Expires       | Repositories            | Linked Files                             | Alarm Trigger |
|-------------|---------------|---------------|--------------------------|------------------------------------------|----------------|
| Token A     | 2025-06-11    | 2025-12-10    | GitBridgev1              | config.py, .env, api_handler.py          | 2025-12-05     |
| Token B     | 2025-06-11    | 2025-12-10    | GitBridgev1              | upload_script.py, .env.alt               | 2025-12-05     |
| Token42     | 2025-06-11    | 2026-04-15    | GitBridgev1              | .github/workflows/, ci_config.json       | 2026-04-10     |

---

### Token Functions and Dependencies

#### Token A (Fine-grained Personal Access Token)
- **Function:** Primary GitBridge repository access for automated operations
- **Permissions:** 
  - Contents: Read/Write
  - Metadata: Read
  - Pull requests: Read/Write
  - Issues: Read/Write
- **Dependencies:**
  - GitBridge CLI operations
  - Automated repository synchronization
  - Atlas_PALM integration workflows
- **Critical Systems:** Main GitBridge workflow automation

#### Token B (Fine-grained Personal Access Token)  
- **Function:** Secondary token for MAS Lite Protocol v2.1 operations
- **Permissions:**
  - Contents: Read/Write
  - Metadata: Read
  - Actions: Read
- **Dependencies:**
  - MAS_Lite repository operations
  - PALM_Testing environment
  - Upload script automation
- **Critical Systems:** Testing and development workflows

#### Token D (Classic Personal Access Token)
- **Function:** GitHub Actions and CI/CD pipeline operations
- **Permissions (Scopes):**
  - repo (full repository access)
  - workflow (GitHub Actions management)
  - write:packages (GitHub Package Registry write)
  - read:packages (GitHub Package Registry read)
- **Dependencies:**
  - GitHub Actions workflows
  - CI/CD pipeline operations
  - Package deployment and publishing
  - Automated build processes
- **Critical Systems:** Production deployment and package management

---

### Update Procedure Post-Regeneration

1. **Pre-Regeneration Checklist:**
   - Verify current token expiration date
   - Backup current token securely
   - Identify all dependent systems
   - Schedule maintenance window if needed

2. **Token Regeneration Process:**
   - Generate new fine-grained token via GitHub Settings
   - Configure identical permissions as previous token
   - Test token functionality in staging environment
   - Document new token creation date and expiration

3. **System Update Process:**
   - Update environment variables (.env files)
   - Update configuration files (config.py)
   - Update CI/CD pipeline secrets
   - Restart affected services

4. **Validation Steps:**
   - Test GitBridge CLI operations
   - Verify repository access permissions
   - Confirm automated workflows function correctly
   - Monitor for any authentication errors

5. **Post-Update Actions:**
   - Update token registry (token_registry.json)
   - Set new alarm trigger date
   - Invalidate old token immediately
   - Document change in audit log

---

### Environment Variable Configuration

#### Required Environment Variables
```bash
# Token A - Primary GitBridge Operations
GITHUB_TOKEN_A=ghp_xxxxxxxxxxxxxxxxxxxx

# Token B - MAS Lite Operations  
GITHUB_TOKEN_B=ghp_xxxxxxxxxxxxxxxxxxxx

# Token D - GitBridge Workflow Operations (Classic PAT)
GITBRIDGE_TOKEN_CLASSIC=github_pat_xxxxxxxxxxxxxxxxxx

# Webhook Secret
GITHUB_WEBHOOK_SECRET=webhook_secret_here

# Flask Application Secret
FLASK_SECRET_KEY=flask_secret_key_here
```

#### File Locations
- **Production:** `/config/.env`
- **Development:** `/config/.env.alt`
- **Testing:** Environment-specific configuration

---

### Security Guidelines

1. **Token Storage:**
   - Never commit tokens to version control
   - Use environment variables exclusively
   - Encrypt tokens in production environments
   - Rotate tokens before expiration

2. **Access Control:**
   - Limit token permissions to minimum required
   - Use fine-grained tokens instead of classic tokens
   - Monitor token usage through GitHub audit logs
   - Implement token rotation automation where possible

3. **Monitoring:**
   - Set up expiration alerts 5 days before expiry
   - Monitor authentication failures
   - Track token usage patterns
   - Log all token-related operations

---

### Support and Troubleshooting

#### Common Issues
- **Authentication Failures:** Check token expiration and permissions
- **Permission Denied:** Verify repository access in token settings
- **Rate Limiting:** Monitor API usage and implement backoff strategies

#### Emergency Contacts
- **Primary:** Zachary Lark (GitBridge maintainer)
- **Secondary:** Cursor Agent (automated monitoring)

---

**Last Updated:** 2025-01-11  
**Next Review:** 2025-07-01  
**Protocol Version:** v2 (June 2025) 