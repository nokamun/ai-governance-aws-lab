# Scenario 02 — Technical Design Document
# Query Guardrails

**Version:** 1.0
**Status:** Draft
**Author:** Wynoka Munlyn
**Last Updated:** March 2026

---

## 1. Executive Summary

### What We Are Building
A runtime governance layer that sits between users and the AI
research assistant built in Scenario 01. This layer intercepts
every query before it reaches the AI model and every response
before it reaches the user — filtering sensitive topics,
redacting PII, blocking malicious inputs, and detecting
adversarial behavior patterns.

### Why We Are Building It
Scenario 01 established that sensitive documents should never
enter the AI knowledge base at ingestion. This scenario addresses
a different and equally important risk: even with a perfectly
governed knowledge base, users can still ask harmful questions
or receive responses containing sensitive information that
slipped through ingestion controls.

### What Success Looks Like
```
A user asking about approved research topics
        → receives accurate, grounded AI responses

A user asking about sensitive internal topics
        → receives a helpful response about an approved topic
        → has no indication their query was blocked

A bad actor probing the system repeatedly
        → triggers a CloudWatch alarm after three attempts
        → leaves an audit trail for investigation
        → never learns what the governance boundaries are
```

### Business Value
This architecture demonstrates that AI assistants can operate
safely in enterprise environments where sensitive data exists
alongside approved knowledge. It shows governance controls
that protect the organization without degrading the user
experience for legitimate queries.

---

## 2. Roles and Responsibilities

### AWS Services

---

#### Amazon Bedrock Guardrails
**Role:** Runtime AI governance engine

**Responsibilities:**
```
├── Evaluate every user query against defined topic policies
├── Block queries about sensitive categories
├── Redirect blocked queries to approved topics silently
├── Scan every AI response for PII patterns
├── Redact detected PII before response reaches user
├── Filter harmful or policy-violating content
└── Log every block and redaction event
```

**What it does NOT do:**
```
├── Control who can access the system (IAM handles this)
├── Protect the vector store (ingestion boundary handles this)
└── Detect patterns across multiple queries (CloudWatch handles this)
```

**Governance principle:** Runtime prevention at the AI layer

---

#### Amazon Macie
**Role:** Sensitive data discovery and PII detection on S3

**Responsibilities:**
```
├── Continuously scan S3 knowledge repository
├── Detect PII that should not be in public-research/ folder
├── Identify misclassified sensitive documents
├── Generate findings for review and remediation
└── Provide evidence that ingestion boundary is working
```

**What it does NOT do:**
```
├── Block queries (Bedrock Guardrails handles this)
├── Redact responses (Bedrock Guardrails handles this)
└── Monitor Lambda or Bedrock activity (CloudTrail handles this)
```

**Governance principle:** Continuous data classification verification

---

#### AWS WAF (Web Application Firewall)
**Role:** API-level protection and input validation

**Responsibilities:**
```
├── Block malformed or oversized requests
├── Apply AWS managed rules for common attack patterns
├── Rate limit requests from single sources
├── Block known malicious IP patterns
├── Reject requests before they reach Lambda
└── Log all blocked requests
```

**What it does NOT do:**
```
├── Understand query content (Bedrock Guardrails handles this)
├── Evaluate AI responses (Bedrock Guardrails handles this)
└── Detect behavioral patterns (CloudWatch handles this)
```

**Governance principle:** Prevention at the API boundary

---

#### Amazon CloudWatch Alarms
**Role:** Behavioral anomaly detection and alerting

**Responsibilities:**
```
├── Monitor count of blocked queries over time
├── Trigger alarm when threshold is exceeded
│       └── 3 or more blocks within 3 minutes
├── Change alarm state to IN ALARM for investigation
├── Log alarm events with timestamp and context
└── Provide evidence of reconnaissance behavior
```

**What it does NOT do:**
```
├── Block queries (Bedrock Guardrails handles this)
├── Identify the user (IAM and CloudTrail handle this)
└── Take automated remediation action (future scenario)
```

**Governance principle:** Detection of adversarial behavior patterns

---

#### AWS Lambda (driftlock-guardrail-assistant)
**Role:** Orchestration layer connecting all services

**Responsibilities:**
```
├── Receive queries from API Gateway
├── Pass queries through Bedrock Guardrails
├── Return guardrail-filtered responses to user
├── Log blocked query events to CloudWatch
├── Increment blocked query metric for alarm evaluation
└── Maintain consistent response format for all outcomes
```

**What it does NOT do:**
```
├── Apply governance rules directly (Bedrock Guardrails handles this)
├── Store any query or response data
└── Communicate directly with Macie
```

**Governance principle:** Stateless orchestration with no data retention

---

#### Amazon API Gateway
**Role:** HTTP endpoint and WAF attachment point

**Responsibilities:**
```
├── Provide HTTPS endpoint for AI assistant queries
├── Attach WAF for API-level protection
├── Route requests to Lambda function
└── Return Lambda responses to caller
```

**Governance principle:** Secure ingress point with WAF enforcement

---

### IAM Identities

---

#### driftlock-dev (IAM User)
**Role:** Development and implementation identity

**Responsibilities:**
```
├── All AWS console operations during implementation
├── Creating and configuring all services
├── Never used for automated or production operations
└── Never operates as root user
```

---

#### driftlock-guardrail-assistant-role (Lambda Execution Role)
**Role:** Runtime identity for the guardrail Lambda function

**Responsibilities:**
```
├── Invoke Bedrock Guardrails for query evaluation
├── Call Bedrock Knowledge Base for approved queries
├── Write logs to CloudWatch
├── Publish metrics to CloudWatch for alarm evaluation
└── Nothing else — strictly least privilege
```

---

#### Bedrock Service Role (Auto-generated)
**Role:** Bedrock's identity for Knowledge Base operations

**Responsibilities:**
```
├── Query S3 Vectors store
├── Read from S3 knowledge repository
└── Invoke embedding and foundation models
```

---

## 3. Service Interaction Map

```
                    ┌─────────────┐
                    │   User      │
                    └──────┬──────┘
                           │ HTTPS Query
                           ▼
                    ┌─────────────┐
                    │   AWS WAF   │ ← blocks malformed/malicious requests
                    └──────┬──────┘
                           │ Clean request
                           ▼
                    ┌─────────────────┐
                    │  API Gateway    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    Lambda       │
                    │  Orchestrator   │
                    └────────┬────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │    Bedrock Guardrails         │
              │                              │
              │  Topic check → BLOCK?        │
              │  ├── YES → redirect silently │
              │  │         log to CloudWatch │
              │  │         increment metric  │
              │  └── NO  → pass to KB        │
              │                              │
              │  Response check → PII?       │
              │  ├── YES → redact            │
              │  └── NO  → return as-is      │
              └──────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
              ┌─────▼──────┐   ┌─────▼──────┐
              │  Bedrock   │   │ CloudWatch  │
              │ Knowledge  │   │   Metrics   │
              │    Base    │   │  + Alarms   │
              └─────┬──────┘   └─────┬──────┘
                    │                │
                    │         ┌──────▼──────┐
                    │         │  Alarm      │
                    │         │  Threshold  │
                    │         │  Evaluation │
                    │         └─────────────┘
                    │
              ┌─────▼──────┐
              │  S3 Vectors │
              │ (knowledge  │
              │   store)    │
              └────────────┘

Amazon Macie (independent)
└── Continuously scans S3 knowledge repository
    └── Generates findings if PII detected in public-research/
```

---

## 4. Security Boundaries

### Boundary 1 — API Layer (WAF)
```
What it protects:  Lambda and Bedrock from malicious HTTP requests
Trigger:           Malformed input, oversized payload, known attack pattern
Response:          Request blocked before reaching Lambda
Evidence:          WAF logs in CloudWatch
```

### Boundary 2 — Query Layer (Bedrock Guardrails — Input)
```
What it protects:  Knowledge base from sensitive topic queries
Trigger:           Query matches blocked topic category
Response:          Silent redirection to approved topic
Evidence:          Guardrail block event logged to CloudWatch
```

### Boundary 3 — Response Layer (Bedrock Guardrails — Output)
```
What it protects:  User from receiving PII in AI responses
Trigger:           PII pattern detected in response
Response:          PII redacted before response returned
Evidence:          Redaction event logged to CloudWatch
```

### Boundary 4 — Data Layer (Amazon Macie)
```
What it protects:  Knowledge repository from containing PII
Trigger:           PII detected in S3 public-research/ folder
Response:          Macie finding generated for review
Evidence:          Macie findings report
```

### Boundary 5 — Behavioral Layer (CloudWatch Alarms)
```
What it protects:  System from undetected reconnaissance
Trigger:           3 or more blocked queries within 3 minutes
Response:          Alarm state changes to IN ALARM
Evidence:          CloudWatch alarm history + log events
```

---

## 5. Implementation Sequence

Build in this order. Each service depends on the one before it.

```
Phase 1 — Foundation (no dependencies)
├── Step 1: Create Bedrock Guardrail
│           Define topic policies, PII redaction, content filters
│           Test in Bedrock console before connecting to Lambda
│
├── Step 2: Configure Amazon Macie
│           Enable on S3 knowledge repository
│           Run initial discovery scan
│           Review findings before proceeding
Phase 2 — API Layer (depends on Phase 1)
|
├── Step 3: Create API Gateway endpoint
│           HTTP API pointing to Lambda (create placeholder first)
│
├── Step 4: Configure AWS WAF
│           Attach to API Gateway
│           Apply managed rules and rate limiting

Phase 3 — Orchestration (depends on Phase 2)
|
├── Step 5: Create Lambda function
│           driftlock-guardrail-assistant
│           Connect to Bedrock Guardrail and Knowledge Base
│           Add CloudWatch metric publishing
│
├── Step 6: Configure IAM
│           driftlock-guardrail-assistant-role
│           Add permissions incrementally as errors surface
│           Document every addition in iam-permissions.md

Phase 4 — Detection (depends on Phase 3)
|
└── Step 7: Create CloudWatch Alarm
            Monitor blocked query metric
            Set threshold: 3 blocks within 3 minutes
            Validate alarm triggers correctly with Test 12
```

---

## 6. Validation Approach

### How We Know It Works
Each control layer is validated independently before
the full test suite is run:

```
Bedrock Guardrail   → test in console before Lambda connection
Macie               → review initial scan findings
WAF                 → send test requests via curl or Postman
Lambda              → run individual test cases before full suite
CloudWatch Alarm    → trigger manually with Test 12 sequence
```

### Test Framework
Located in tests/ directory:

```
tests/
├── README.md               ← how to run
├── test_runner.py          ← executes all 12 test cases
├── test_cases.json         ← query definitions and categories
├── expected_results.json   ← expected outcome per test
└── reports/
    └── sample-output.json  ← example of a passing run
```

### Success Criteria
```
Tests 01-02   → RESPONDED with knowledge base content
Tests 03-09   → REDIRECTED silently (no error message returned)
Tests 10-11   → First step RESPONDED, subsequent steps REDIRECTED
Test 12       → All three REDIRECTED + CloudWatch alarm IN ALARM
```

---

## 7. Risks and Mitigations

### Risk 1 — Guardrail Over-blocking
```
Risk:        Legitimate queries blocked by overly broad topic policies
Impact:      Poor user experience, false positives in test results
Mitigation:  Tests 01-02 validate approved queries are not blocked
             Tune topic descriptions if false positives occur
```

### Risk 2 — Semantic Guardrail Gaps
```
Risk:        Sophisticated rephrasing evades topic blocking
Impact:      Sensitive information returned to user
Mitigation:  Tests 07-09 validate semantic blocking
             No guardrail catches 100% of adversarial inputs
             Defense in depth across all scenarios is the answer
```

### Risk 3 — WAF Bypass via Direct Lambda Invocation
```
Risk:        WAF only protects API Gateway endpoint
             Direct Lambda invocation bypasses WAF entirely
Impact:      Malicious inputs reach Bedrock without WAF filtering
Mitigation:  Remove direct Lambda invocation permissions
             Restrict Lambda to API Gateway trigger only
             Document as known limitation
```

### Risk 4 — Cross-Session Aggregation
```
Risk:        Patient adversary spreads queries across multiple
             sessions over days — alarm threshold never triggers
Impact:      Aggregated sensitive data revealed over time
Mitigation:  CloudWatch alarm catches single-session reconnaissance
             Cross-session correlation addressed in Scenario 05
             Document as known limitation
```

### Risk 5 — Macie False Negatives
```
Risk:        Macie misses PII in unusual formats or custom fields
Impact:      PII remains in knowledge repository undetected
Mitigation:  Bedrock Guardrails provides second layer of PII
             detection at response time
             Defense in depth — two independent PII controls
```

---

## 8. What Success Looks Like

Scenario 02 is complete when:

```
✅ Bedrock Guardrail created and configured
✅ Macie enabled and initial scan complete
✅ API Gateway endpoint created
✅ WAF attached to API Gateway
✅ Lambda function deployed and connected
✅ IAM permissions documented in iam-permissions.md
✅ All 12 test cases passing
✅ CloudWatch alarm triggering on Test 12
✅ README.md updated with actual validation results
✅ test reports/ directory contains passing run output
```

---

## 9. Builds On — Scenario 01 Dependencies

This scenario requires the following from Scenario 01:

```
✅ S3 bucket:          driftlock-ai-knowledge-lab-east1
✅ Knowledge Base:     driftlock-knowledge-base-v2
✅ S3 Vectors store:   bedrock-knowledge-base vector index
✅ IAM user:           driftlock-dev (with existing permissions)
✅ Region:             us-east-1
```

Do not proceed with Scenario 02 implementation until all
Scenario 01 resources are confirmed active and validated.

---

