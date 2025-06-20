# GitHub Token Rotation Checklist
## GitBridge Token Management Protocol v2 - Human Operator Guide

### ⚠️ CRITICAL: This checklist must be completed for each token rotation

### 🚨 **SPECIAL NOTICE - Token D (Classic PAT):**
Token D has broad permissions (repo, workflow, packages) and affects:
- GitHub Actions workflows
- CI/CD pipeline operations  
- Package registry access
- Automated deployments

**REQUIRES:** Coordination with deployment schedule and extended testing period.

---

## Pre-Rotation Phase

### 🔍 Assessment and Planning
- [ ] **Confirm token expiration date**
  - Token ID: _________________
  - Current expiration: _________________
  - Days remaining: _________________
  - Alarm trigger passed: Yes / No

- [ ] **Identify affected systems**
  - Review `meta/token_registry.json` for dependencies
  - Check `docs/github_tokens/README.md` for linked files
  - Verify all systems using this token
  - Document downtime window if required

- [ ] **Backup current configuration**
  - Backup current `.env` files
  - Export current environment variables
  - Save current `token_registry.json`
  - Create restore point

### 📋 Environment Preparation
- [ ] **Schedule maintenance window**
  - Start time: _________________
  - Expected duration: _________________
  - Stakeholders notified: Yes / No
  - Backup operator available: Yes / No

- [ ] **Prepare secure workspace**
  - Clean terminal history
  - Ensure secure network connection
  - Close unnecessary applications
  - Enable screen lock timeout

---

## Token Generation Phase

### 🔐 GitHub Token Creation
- [ ] **Access GitHub Settings**
  - Navigate to GitHub.com → Settings → Developer settings
  - Click "Personal access tokens" → "Fine-grained tokens"
  - Click "Generate new token"

- [ ] **Configure token settings**
  - Token name: `GitBridge-TokenX-YYYY-MM-DD`
  - Expiration: Set to 60 days from creation
  - Resource owner: Verify correct account
  - Repository access: Configure per token requirements

- [ ] **Set permissions** (Reference: `token_registry.json`)
  - **Token A permissions:**
    - [ ] Contents: Read and write
    - [ ] Metadata: Read
    - [ ] Pull requests: Read and write
    - [ ] Issues: Read and write
  - **Token B permissions:**
    - [ ] Contents: Read and write
    - [ ] Metadata: Read
    - [ ] Actions: Read
  - **Token D permissions (Classic PAT):**
    - [ ] repo: Full repository access
    - [ ] workflow: GitHub Actions management
    - [ ] write:packages: Package registry write access
    - [ ] read:packages: Package registry read access

- [ ] **Generate and secure token**
  - Copy token immediately (only shown once)
  - Store in secure password manager
  - Do NOT save to clipboard or browser
  - Verify token format: `ghp_` prefix, 36+ characters

### 🧪 Token Validation
- [ ] **Test token functionality**
  - Create test API call using new token
  - Verify repository access permissions
  - Test with minimal operation (e.g., read repository info)
  - Confirm rate limits are appropriate

---

## System Update Phase

### 🔧 Configuration Updates
- [ ] **Update environment variables**
  - [ ] Production `.env` file
  - [ ] Development `.env.alt` file
  - [ ] CI/CD pipeline secrets (if applicable)
  - [ ] Docker environment files
  - [ ] Kubernetes secrets (if applicable)

- [ ] **Update configuration files**
  - **For Token A:**
    - [ ] `config.py` - Update GITHUB_TOKEN_A reference
    - [ ] `api_handler.py` - Verify token usage
    - [ ] Environment-specific configs
  - **For Token B:**
    - [ ] `upload_script.py` - Update token reference
    - [ ] Test environment configurations
  - **For Token D:**
    - [ ] `.github/workflows/` - Update GitHub Actions secrets
    - [ ] `ci_config.json` - Update CI configuration (if exists)
    - [ ] GitHub repository secrets - Update GITBRIDGE_TOKEN_CLASSIC
    - [ ] Package registry configurations

- [ ] **Update documentation**
  - [ ] `meta/token_registry.json` - Update token metadata
  - [ ] `docs/github_tokens/README.md` - Update table
  - [ ] Set new alarm trigger date (5 days before expiration)

### 🔄 Service Management
- [ ] **Restart affected services**
  - [ ] Stop GitBridge CLI processes
  - [ ] Restart webhook server (if applicable)
  - [ ] Restart Flask application
  - [ ] Restart any containerized services
  - [ ] Clear application caches

- [ ] **Verify service health**
  - [ ] Check service logs for authentication errors
  - [ ] Verify API connectivity
  - [ ] Test automated workflows
  - [ ] Monitor resource utilization

---

## Validation Phase

### ✅ Functionality Testing
- [ ] **Test GitBridge CLI operations**
  - [ ] Repository listing
  - [ ] File read operations
  - [ ] File write operations (if applicable)
  - [ ] Pull request operations
  - [ ] Issue management

- [ ] **Verify automated workflows**
  - [ ] Webhook processing
  - [ ] Scheduled tasks
  - [ ] Integration tests
  - [ ] End-to-end workflows

- [ ] **Security validation**
  - [ ] No authentication errors in logs
  - [ ] Token not exposed in logs/errors
  - [ ] Rate limiting functioning correctly
  - [ ] Audit logs show new token usage

### 📊 Monitoring Setup
- [ ] **Configure monitoring alerts**
  - [ ] Update expiration monitoring
  - [ ] Set up authentication failure alerts
  - [ ] Configure rate limit warnings
  - [ ] Test alert delivery

---

## Cleanup Phase

### 🗑️ Security Cleanup
- [ ] **Invalidate old token immediately**
  - Go to GitHub → Settings → Personal access tokens
  - Find old token in list
  - Click "Revoke" or "Delete"
  - Confirm token is no longer accessible

- [ ] **Clear sensitive data**
  - [ ] Clear terminal/shell history
  - [ ] Remove old token from password manager
  - [ ] Clear browser saved passwords/autofill
  - [ ] Secure delete backup files with old tokens

### 📝 Documentation Updates
- [ ] **Update token registry**
  - [ ] New creation date
  - [ ] New expiration date
  - [ ] New alarm trigger date
  - [ ] Update `last_rotated` field
  - [ ] Increment version/rotation counter

- [ ] **Log rotation completion**
  - [ ] Update `logs/token_audit_log.md` with rotation details
  - [ ] Record completion time and duration
  - [ ] Note any issues encountered
  - [ ] Update next rotation due date

---

## Post-Rotation Monitoring

### 📈 24-Hour Monitoring
- [ ] **Monitor system health** (Next 24 hours)
  - [ ] Check error logs every 4 hours
  - [ ] Verify automated processes run successfully
  - [ ] Monitor API rate limits and usage
  - [ ] Check webhook delivery success rates

- [ ] **Incident response preparation**
  - [ ] Ensure rollback procedure is documented
  - [ ] Keep backup token ready (if available)
  - [ ] Monitor user reports and system alerts
  - [ ] Document any anomalies

### 🔄 Set Next Rotation
- [ ] **Schedule next rotation**
  - Next rotation due: _________________ (45-50 days from now)
  - Calendar reminder set: Yes / No
  - Automated monitoring configured: Yes / No
  - Team notification scheduled: Yes / No

---

## Sign-off

### ✍️ Completion Verification
**Operator:** _________________  
**Date:** _________________  
**Time:** _________________  
**Token Rotated:** _________________  
**Duration:** _________________ minutes

**All checklist items completed:** ☐ Yes ☐ No  
**Systems functioning normally:** ☐ Yes ☐ No  
**Monitoring alerts configured:** ☐ Yes ☐ No  
**Documentation updated:** ☐ Yes ☐ No

### 🚨 Emergency Information
**If issues arise during rotation:**
1. Immediately document the issue
2. Check if old token is still valid (don't revoke until new token works)
3. Review logs for specific error messages
4. Contact: Zachary Lark (GitBridge maintainer)
5. Escalation: Cursor Agent monitoring system

**Emergency rollback procedure:**
1. Restore backup environment variables
2. Restart affected services
3. Verify system functionality
4. Document rollback reason
5. Schedule immediate retry with investigation

---

**Protocol Version:** v2 (June 2025)  
**Last Updated:** 2025-01-11  
**Next Checklist Review:** 2025-07-01 