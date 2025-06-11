# SmartRepo Fallback Protocol Specification

## Protocol Overview
- **Version**: MAS Lite Protocol v2.1
- **Generated**: 2025-06-09 07:00:13 UTC
- **Total Specifications**: 12
- **Supported Fallback Types**: AUTO_RETRY, GPT_ESCALATE, STUB_REPO, NOTIFY_ONLY

## Fallback Type Definitions

### AUTO_RETRY
Automatically retry the failed operation with exponential backoff and circuit breaker logic.
- **Use Case**: Transient failures, network issues, temporary resource constraints
- **Human Review**: Not required
- **Max Retries**: Configurable per specification

### GPT_ESCALATE  
Escalate to GPT agent for intelligent problem analysis and resolution.
- **Use Case**: Complex validation errors, content generation failures, metadata repair
- **Human Review**: May be required based on severity
- **Timeout**: 600 seconds

### STUB_REPO
Create minimal stub repository with basic structure to ensure system stability.
- **Use Case**: Missing critical components, validation timeouts, incomplete data
- **Human Review**: Optional - can be reviewed post-creation
- **Content**: Minimal but valid repository structure

### NOTIFY_ONLY
Notify administrators without automated intervention.
- **Use Case**: Critical system failures, permission issues, filesystem problems  
- **Human Review**: Always required
- **Escalation**: Immediate for critical severity

## Fallback Specifications

### METADATA_MISSING
- **Fallback Type**: STUB_REPO
- **Severity**: medium
- **Auto Retry Count**: 0
- **Human Review Required**: False
- **Estimated Resolution**: 2-5 minutes

**Trigger Conditions:**
- repo_metadata.json file not found
- metadata directory missing
- required metadata fields missing

**Recommended Action:**
Create minimal stub repository with basic metadata structure

**GPT Prompt Template:**
```
Task: Generate minimal repository metadata for failed repository creation.

Context: Repository metadata is missing or incomplete for task: {task_id}
Error Details: {error_details}

Please generate a minimal but valid repo_metadata.json structure with:
1. Basic task information
2. Default branch configuration
3. Placeholder commit history
4. Standard directory structure

Ensure MAS Lite Protocol v2.1 compliance with SHA256 integrity.
```

---

### METADATA_INVALID
- **Fallback Type**: GPT_ESCALATE
- **Severity**: high
- **Auto Retry Count**: 1
- **Human Review Required**: True
- **Estimated Resolution**: 5-10 minutes

**Trigger Conditions:**
- metadata validation failed
- corrupt metadata structure
- schema validation errors
- encoding issues in metadata

**Recommended Action:**
Escalate to GPT for metadata repair and validation

**GPT Prompt Template:**
```
Task: Repair and validate corrupted repository metadata.

Context: Repository metadata validation failed for task: {task_id}
Error Details: {error_details}
Current Metadata: {current_metadata}

Please analyze and repair the metadata issues:
1. Fix schema validation errors
2. Resolve encoding problems
3. Ensure field completeness
4. Validate against MAS Lite Protocol v2.1
5. Provide corrected metadata structure

Include explanation of fixes applied.
```

---

### BRANCH_CREATION_FAILED
- **Fallback Type**: AUTO_RETRY
- **Severity**: low
- **Auto Retry Count**: 3
- **Human Review Required**: False
- **Estimated Resolution**: 1-3 minutes

**Trigger Conditions:**
- git branch creation failed
- branch naming conflicts
- insufficient permissions for branch operations

**Recommended Action:**
Retry branch creation with alternative naming strategy

**GPT Prompt Template:**
```
Task: Resolve branch creation failure and suggest alternative approach.

Context: Git branch creation failed for task: {task_id}
Error Details: {error_details}
Attempted Branch Name: {branch_name}

Please suggest:
1. Alternative branch naming strategy
2. Conflict resolution approach
3. Permission issue workarounds
4. Fallback branch structure

Ensure compatibility with GitBridge workflow.
```

---

### BRANCH_METADATA_SYNC_FAILED
- **Fallback Type**: GPT_ESCALATE
- **Severity**: high
- **Auto Retry Count**: 1
- **Human Review Required**: True
- **Estimated Resolution**: 10-15 minutes

**Trigger Conditions:**
- branch metadata synchronization failed
- branch-metadata linkage broken
- inconsistent branch state

**Recommended Action:**
Escalate to GPT for branch-metadata reconciliation

**GPT Prompt Template:**
```
Task: Reconcile branch and metadata synchronization issues.

Context: Branch-metadata sync failed for task: {task_id}
Error Details: {error_details}
Branch State: {branch_state}
Metadata State: {metadata_state}

Please provide:
1. Root cause analysis of sync failure
2. Reconciliation strategy
3. Data integrity verification steps
4. Prevention measures for future occurrences

Ensure MAS Lite Protocol v2.1 compliance.
```

---

### CHECKLIST_FORMAT_ERROR
- **Fallback Type**: AUTO_RETRY
- **Severity**: low
- **Auto Retry Count**: 2
- **Human Review Required**: False
- **Estimated Resolution**: 2-5 minutes

**Trigger Conditions:**
- checklist validation failed
- malformed checkbox syntax
- insufficient checklist items
- duplicate checklist items

**Recommended Action:**
Auto-repair checklist formatting and regenerate

**GPT Prompt Template:**
```
Task: Repair and standardize checklist formatting.

Context: Checklist validation failed for task: {task_id}
Error Details: {error_details}
Current Checklist: {checklist_content}

Please fix:
1. Checkbox syntax errors ([x], [ ], [-])
2. Missing list markers (-, *)
3. Duplicate item removal
4. Minimum item count compliance (3-20 items)
5. Lifecycle coverage gaps

Provide corrected checklist in standard format.
```

---

### CHECKLIST_MISSING
- **Fallback Type**: STUB_REPO
- **Severity**: medium
- **Auto Retry Count**: 0
- **Human Review Required**: False
- **Estimated Resolution**: 3-7 minutes

**Trigger Conditions:**
- checklist file not found
- checklist directory missing
- empty checklist file

**Recommended Action:**
Generate minimal stub checklist with standard lifecycle items

**GPT Prompt Template:**
```
Task: Generate standard checklist for repository task.

Context: Checklist is missing for task: {task_id}
Error Details: {error_details}

Please create a comprehensive checklist including:
1. Planning phase items
2. Development phase items
3. Testing phase items
4. Review phase items
5. Deployment phase items
6. Documentation phase items

Use proper format: - [x]/[ ]/[-] Item description
Ensure 3-20 items total with actionable language.
```

---

### README_GENERATION_FAILED
- **Fallback Type**: AUTO_RETRY
- **Severity**: low
- **Auto Retry Count**: 2
- **Human Review Required**: False
- **Estimated Resolution**: 3-5 minutes

**Trigger Conditions:**
- README.md generation failed
- template processing error
- content generation timeout

**Recommended Action:**
Retry README generation with simplified template

**GPT Prompt Template:**
```
Task: Generate simplified README for failed repository creation.

Context: README generation failed for task: {task_id}
Error Details: {error_details}
Available Metadata: {metadata}

Please create a basic README.md with:
1. Project title and description
2. Basic usage instructions
3. Installation steps
4. Contributing guidelines
5. License information

Keep content minimal but informative. Ensure ≥500 characters.
```

---

### README_CONTENT_INVALID
- **Fallback Type**: GPT_ESCALATE
- **Severity**: medium
- **Auto Retry Count**: 1
- **Human Review Required**: True
- **Estimated Resolution**: 5-10 minutes

**Trigger Conditions:**
- README content validation failed
- insufficient content length
- missing required sections
- malformed markdown syntax

**Recommended Action:**
Escalate to GPT for comprehensive README enhancement

**GPT Prompt Template:**
```
Task: Enhance and validate README content for repository.

Context: README validation failed for task: {task_id}
Error Details: {error_details}
Current README: {readme_content}
Validation Issues: {validation_issues}

Please enhance the README to address:
1. Content length requirements (≥500 characters)
2. Missing required sections
3. Markdown syntax errors
4. Technical accuracy
5. User experience improvements

Provide complete, well-structured README.md content.
```

---

### COMMIT_VALIDATION_FAILED
- **Fallback Type**: AUTO_RETRY
- **Severity**: medium
- **Auto Retry Count**: 3
- **Human Review Required**: False
- **Estimated Resolution**: 2-5 minutes

**Trigger Conditions:**
- commit message validation failed
- commit hash verification failed
- commit metadata inconsistency

**Recommended Action:**
Retry commit with corrected metadata and validation

**GPT Prompt Template:**
```
Task: Fix commit validation issues and retry.

Context: Commit validation failed for task: {task_id}
Error Details: {error_details}
Commit Message: {commit_message}
Commit Metadata: {commit_metadata}

Please provide:
1. Corrected commit message following standards
2. Fixed metadata structure
3. Validation compliance steps
4. Hash integrity verification

Ensure MAS Lite Protocol v2.1 compliance.
```

---

### FILESYSTEM_ERROR
- **Fallback Type**: NOTIFY_ONLY
- **Severity**: critical
- **Auto Retry Count**: 0
- **Human Review Required**: True
- **Estimated Resolution**: 15-30 minutes

**Trigger Conditions:**
- insufficient disk space
- file permission errors
- directory creation failed
- file system corruption

**Recommended Action:**
Notify system administrators of filesystem issues

**GPT Prompt Template:**
```
Task: Analyze filesystem error and provide recovery recommendations.

Context: Filesystem error occurred during repository creation for task: {task_id}
Error Details: {error_details}
System State: {system_state}

Please provide:
1. Root cause analysis
2. Immediate recovery steps
3. System health recommendations
4. Prevention strategies
5. Alternative storage options

Include urgency assessment and escalation path.
```

---

### NETWORK_FAILURE
- **Fallback Type**: AUTO_RETRY
- **Severity**: medium
- **Auto Retry Count**: 5
- **Human Review Required**: False
- **Estimated Resolution**: 5-15 minutes

**Trigger Conditions:**
- network connectivity lost
- API endpoint unavailable
- timeout during external calls
- DNS resolution failed

**Recommended Action:**
Retry operation with exponential backoff and circuit breaker

**GPT Prompt Template:**
```
Task: Handle network failure with retry strategy.

Context: Network failure during repository operation for task: {task_id}
Error Details: {error_details}
Network State: {network_state}

Please suggest:
1. Optimal retry intervals
2. Circuit breaker configuration
3. Offline mode capabilities
4. Alternative endpoints/services
5. Degraded functionality options

Ensure graceful degradation of services.
```

---

### VALIDATION_TIMEOUT
- **Fallback Type**: STUB_REPO
- **Severity**: high
- **Auto Retry Count**: 0
- **Human Review Required**: True
- **Estimated Resolution**: 10-20 minutes

**Trigger Conditions:**
- validation process timeout
- resource exhaustion during validation
- infinite loop in validation logic

**Recommended Action:**
Create stub repository with minimal validation

**GPT Prompt Template:**
```
Task: Handle validation timeout with fallback approach.

Context: Validation timeout occurred for task: {task_id}
Error Details: {error_details}
Validation State: {validation_state}

Please provide:
1. Timeout root cause analysis
2. Minimal validation strategy
3. Stub repository structure
4. Performance optimization suggestions
5. Monitoring improvements

Ensure basic functionality while investigating timeout.
```

---

## Global Configuration

### Retry Configuration
- **Max Retry Attempts**: 5
- **Base Retry Delay**: 2.0 seconds
- **Exponential Backoff Factor**: 1.5
- **Circuit Breaker Threshold**: 3

### Timeout Configuration
- **Human Review Timeout**: 1800 seconds (30 minutes)
- **GPT Escalation Timeout**: 600 seconds (10 minutes)

### Fallback Priority Order
1. AUTO_RETRY
2. STUB_REPO
3. GPT_ESCALATE
4. NOTIFY_ONLY

## Usage Examples

### Basic Fallback Retrieval
```python
from smartrepo_fallback_spec import SmartRepoFallbackProtocol

protocol = SmartRepoFallbackProtocol()
spec = protocol.get_fallback_spec("CHECKLIST_FORMAT_ERROR")

if spec['fallback_type'] == 'AUTO_RETRY':
    # Implement retry logic
    retry_count = spec['auto_retry_count']
elif spec['fallback_type'] == 'GPT_ESCALATE':
    # Escalate to GPT with provided template
    prompt = spec['gpt_prompt_template'].format(
        task_id="example-task",
        error_details="Validation failed"
    )
```

### Fallback Chain for Multiple Errors
```python
error_codes = ["METADATA_INVALID", "CHECKLIST_MISSING", "README_GENERATION_FAILED"]
fallback_chain = protocol.suggest_fallback_chain(error_codes)

for spec in fallback_chain:
    print(f"Fallback: STUB_REPO")
    print(f"Severity: high")
    print(f"Action: Create stub repository with minimal validation")
```

## Integration Notes

### MAS Lite Protocol v2.1 Compliance
- All fallback specifications include SHA256 integrity hashing
- UTC timestamps with ISO format
- Session correlation for audit trail linkage
- Structured metadata for version tracking

### SmartRepo Ecosystem Integration
- Compatible with smartrepo_audit_logger for operation tracking
- Designed for use by automated fallback builder (P18P4S4)
- Supports human-in-the-loop and AI-in-the-loop resolution methods
- Integration ready for Phase 22 GPT-based intervention logic

---

*Generated by GitBridge SmartRepo Fallback Protocol - Phase 18P4S3*
