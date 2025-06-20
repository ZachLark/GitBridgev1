# GitBridge API Key Rotation Plan

**Task**: P20P5S1 - Create a Secure API Key Rotation Plan  
**Date**: 2025-06-19  
**Status**: Implementation Plan  

---

## 🔐 **Current Key Management**

### **Environment Variables**
```bash
# .env file (local development)
OPENAI_API_KEY=sk-...
GROK_API_KEY=grok_...
WEBHOOK_SECRET=ghp_...
```

### **Key Types & Usage**
- **OpenAI API Key**: GPT-4o integration (P20P2S1)
- **Grok API Key**: Grok 3 integration (P20P6 - future)
- **Webhook Secret**: GitHub webhook verification (P20P3S1)

---

## 🔄 **Key Rotation Strategy**

### **1. Development Environment Rotation**

#### **Manual Rotation Process**
```bash
# 1. Generate new keys
# OpenAI: https://platform.openai.com/api-keys
# Grok: https://console.groq.com/keys

# 2. Update .env file
cp .env .env.backup.$(date +%Y%m%d)
# Edit .env with new keys

# 3. Test integration
python tests/test_gpt4o_connection.py
python tests/test_grok_connection.py  # Future

# 4. Verify webhook functionality
curl -X POST http://localhost:5000/webhook/github \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: pull_request" \
  -d @tests/sample_webhook_payload.json
```

#### **Rotation Schedule**
- **Development**: Every 30 days
- **Staging**: Every 15 days  
- **Production**: Every 7 days

### **2. Production Environment Rotation**

#### **GitHub Secrets Automation**
```yaml
# .github/workflows/rotate-keys.yml
name: Rotate API Keys
on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly at 2 AM Sunday
  workflow_dispatch:  # Manual trigger

jobs:
  rotate-keys:
    runs-on: ubuntu-latest
    steps:
      - name: Generate new OpenAI key
        run: |
          # Automated key generation via OpenAI API
          NEW_OPENAI_KEY=$(curl -X POST "https://api.openai.com/v1/api_keys" \
            -H "Authorization: Bearer ${{ secrets.OPENAI_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{"name": "gitbridge-$(date +%Y%m%d)"}' | jq -r '.secret')
          
          # Update GitHub secret
          gh secret set OPENAI_API_KEY --body "$NEW_OPENAI_KEY"
      
      - name: Generate new Grok key
        run: |
          # Automated key generation via Grok API
          NEW_GROK_KEY=$(curl -X POST "https://api.groq.com/openai/v1/api_keys" \
            -H "Authorization: Bearer ${{ secrets.GROK_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{"name": "gitbridge-$(date +%Y%m%d)"}' | jq -r '.secret')
          
          # Update GitHub secret
          gh secret set GROK_API_KEY --body "$NEW_GROK_KEY"
      
      - name: Test new keys
        run: |
          # Run integration tests with new keys
          python -m pytest tests/test_api_integration.py
```

#### **Secrets Management**
```bash
# GitHub Secrets (production)
OPENAI_API_KEY=sk-...          # Rotated weekly
GROK_API_KEY=grok_...          # Rotated weekly  
WEBHOOK_SECRET=ghp_...         # Rotated monthly
DEPLOYMENT_KEY=ssh-...         # Rotated quarterly
```

---

## 🛡️ **Security Best Practices**

### **Key Storage**
- ✅ **Never commit keys to version control**
- ✅ **Use environment variables for local development**
- ✅ **Use GitHub Secrets for production**
- ✅ **Implement key expiration policies**

### **Access Control**
- ✅ **Principle of least privilege**
- ✅ **Regular access reviews**
- ✅ **Audit logging for key usage**
- ✅ **Emergency key revocation procedures**

### **Monitoring & Alerting**
```python
# key_monitoring.py
import logging
from datetime import datetime, timedelta

def monitor_key_usage(api_key: str, usage_data: dict):
    """Monitor API key usage for anomalies."""
    if usage_data['daily_requests'] > 1000:
        logging.warning(f"High API usage detected: {usage_data['daily_requests']} requests")
    
    if usage_data['error_rate'] > 0.05:
        logging.error(f"High error rate detected: {usage_data['error_rate']:.2%}")
```

---

## 🔧 **Implementation Steps**

### **Phase 1: Development Setup**
1. ✅ Create `.env.example` template
2. ✅ Implement key validation in startup
3. ✅ Add key rotation testing scripts
4. ✅ Document manual rotation procedures

### **Phase 2: Production Automation**
1. 🔄 Set up GitHub Actions for automated rotation
2. 🔄 Implement key health monitoring
3. 🔄 Create emergency key revocation procedures
4. 🔄 Set up alerting for key expiration

### **Phase 3: Advanced Security**
1. 🔄 Implement key versioning
2. 🔄 Add key usage analytics
3. 🔄 Create key performance metrics
4. 🔄 Implement zero-downtime key rotation

---

## 📊 **Key Rotation Checklist**

### **Pre-Rotation**
- [ ] Backup current keys
- [ ] Generate new keys
- [ ] Test new keys in staging
- [ ] Schedule maintenance window
- [ ] Notify team members

### **During Rotation**
- [ ] Update environment variables
- [ ] Update GitHub Secrets
- [ ] Restart services
- [ ] Run integration tests
- [ ] Verify webhook functionality

### **Post-Rotation**
- [ ] Monitor for errors
- [ ] Update documentation
- [ ] Archive old keys
- [ ] Update rotation schedule
- [ ] Log rotation completion

---

## 🚨 **Emergency Procedures**

### **Key Compromise Response**
```bash
# 1. Immediate revocation
curl -X DELETE "https://api.openai.com/v1/api_keys/$COMPROMISED_KEY" \
  -H "Authorization: Bearer $ADMIN_KEY"

# 2. Generate emergency key
NEW_KEY=$(python scripts/generate_emergency_key.py)

# 3. Update all environments
echo "OPENAI_API_KEY=$NEW_KEY" > .env
gh secret set OPENAI_API_KEY --body "$NEW_KEY"

# 4. Restart services
sudo systemctl restart gitbridge-webhook
sudo systemctl restart gitbridge-cursor
```

### **Rollback Procedures**
```bash
# Restore previous key from backup
cp .env.backup.$(date -d '7 days ago' +%Y%m%d) .env
gh secret set OPENAI_API_KEY --body "$PREVIOUS_KEY"
```

---

## 📈 **Monitoring & Metrics**

### **Key Health Metrics**
- **Usage Rate**: Requests per hour/day
- **Error Rate**: Failed requests percentage
- **Response Time**: Average API response time
- **Cost Tracking**: API usage costs
- **Quota Usage**: Rate limit utilization

### **Alerting Rules**
- **High Usage**: >1000 requests/hour
- **High Errors**: >5% error rate
- **Slow Response**: >5s average response time
- **Quota Warning**: >80% of daily quota used
- **Key Expiration**: <7 days until expiration

---

*This plan ensures secure, automated key management for GitBridge's AI integration infrastructure.* 