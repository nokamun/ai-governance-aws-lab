# IAM Permissions Log — Scenario 02
# Query Guardrails

This document tracks every IAM permission added during Scenario 02,
why it was added, and the governance principle it demonstrates.
It also documents service substitutions made due to free tier
limitations and the production recommendations for each.

---

## Identities Used

| Identity | Type | Purpose |
|---|---|---|
| driftlock-dev | IAM User | Development identity — all console and CLI operations |
| driftlock-guardrail-assistant-role | IAM Role | Lambda execution role for guardrail query assistant |
| driftlock-pii-scanner-role | IAM Role | Lambda execution role for PII scanner |

---

## IAM User: driftlock-dev

### Permissions Added This Scenario

| # | Permission | Type | Reason Added |
|---|---|---|---|
| 1 | AmazonAPIGatewayAdministrator | Managed | Create and configure HTTP API Gateway endpoint |
| 2 | AWSWAFConsoleFullAccess | Managed | Create and configure WAF Web ACL and rules |
| 3 | AWSCloudShellFullAccess | Managed | Browser-based CLI for metric publishing and alarm validation |
| 4 | CloudWatchFullAccess | Managed | Create CloudWatch Alarms and view custom metrics |
| 5 | driftlock-dev-supplemental | Inline | WAF permissions consolidated after hitting managed policy quota |

### Permissions Removed This Scenario

| Permission | Reason Removed |
|---|---|
| AmazonMacieFullAccess | Macie requires subscription — not implemented |
| ComprehendFullAccess | Comprehend requires subscription — regex scanner built instead |

### Managed Policy Quota Lesson

```
AWS accounts have a quota of 10 managed policies per IAM entity
        ↓
driftlock-dev reached the limit during Scenario 02
        ↓
Resolution: Remove unused policies and consolidate
WAF permissions into inline policy

Governance principle:
Regular permission audits prevent quota issues
Inline policies are better for scoped project-specific
permissions — they cannot be accidentally attached elsewhere
```

### driftlock-dev-supplemental Policy

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowWAFFullAccess",
            "Effect": "Allow",
            "Action": [
                "wafv2:*"
            ],
            "Resource": "*"
        }
    ]
}
```

### Complete driftlock-dev Permission State (End of Scenario 02)

```
Managed Policies (6):
├── AmazonAPIGatewayAdministrator
├── AmazonBedrockFullAccess
├── AmazonS3FullAccess
├── AWSLambda_FullAccess
├── IAMFullAccess
└── CloudWatchFullAccess

Inline Policies (2):
├── driftlock-s3vectors-policy    (from Scenario 01)
└── driftlock-dev-supplemental    (WAF permissions)
```

---

## Lambda Execution Role: driftlock-guardrail-assistant-role
### Query Guardrail Orchestrator

### Permissions Log

| # | Permission | Type | Reason Added |
|---|---|---|---|
| 1 | CloudWatchLogsPolicy | Managed | Basic Lambda execution — write logs to CloudWatch |
| 2 | driftlock-guardrail-assistant-policy | Inline | Bedrock KB query, guardrail evaluation, metric publishing |

### driftlock-guardrail-assistant-policy

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowBedrockKnowledgeBaseQuery",
            "Effect": "Allow",
            "Action": [
                "bedrock:RetrieveAndGenerate",
                "bedrock:Retrieve",
                "bedrock:InvokeModel"
            ],
            "Resource": [
                "arn:aws:bedrock:us-east-1:YOUR_ACCOUNT_ID:knowledge-base/YOUR_KB_ID",
                "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-lite-v1:0"
            ]
        },
        {
            "Sid": "AllowBedrockGuardrail",
            "Effect": "Allow",
            "Action": [
                "bedrock:ApplyGuardrail"
            ],
            "Resource": "arn:aws:bedrock:us-east-1:YOUR_ACCOUNT_ID:guardrail/your-guardrail-id"
        },
        {
            "Sid": "AllowCloudWatchMetrics",
            "Effect": "Allow",
            "Action": [
                "cloudwatch:PutMetricData"
            ],
            "Resource": "*"
        }
    ]
}
```

### Why Each Permission Is Scoped

```
bedrock:RetrieveAndGenerate + Retrieve + InvokeModel
└── Scoped to specific Knowledge Base ARN and model ARN
    Cannot query other KBs or invoke other models
    Same pattern as Scenario 01 Bedrock Lambda

bedrock:ApplyGuardrail
└── Scoped to specific Guardrail ARN
    Cannot apply other guardrails
    Cannot modify guardrail configuration

cloudwatch:PutMetricData
└── Resource * required — CloudWatch metrics do not
    have individual ARNs that can be scoped
    This is a known AWS service limitation
    Acceptable because action is narrowly defined
```

---

## Lambda Execution Role: driftlock-pii-scanner-role
### PII Discovery Scanner

### Permissions Log

| # | Permission | Type | Reason Added |
|---|---|---|---|
| 1 | CloudWatchLogsPolicy | Managed | Basic Lambda execution — write logs to CloudWatch |
| 2 | driftlock-pii-scanner-s3-policy | Inline | Read public-research/ documents for PII scanning |
| 3 | driftlock-pii-scanner-comprehend-policy | Inline | Call Comprehend DetectPiiEntities (policy exists, subscription required) |

### driftlock-pii-scanner-s3-policy

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowPublicResearchRead",
            "Effect": "Allow",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::driftlock-ai-knowledge-lab-east1/public-research/*"
        },
        {
            "Sid": "AllowBucketList",
            "Effect": "Allow",
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::driftlock-ai-knowledge-lab-east1",
            "Condition": {
                "StringLike": {
                    "s3:prefix": "public-research/*"
                }
            }
        }
    ]
}
```

### Why This Is Stronger Than AmazonS3ReadOnlyAccess

```
AmazonS3ReadOnlyAccess
└── Grants read access to ALL S3 buckets in the account
    If this Lambda is compromised it can read everything

driftlock-pii-scanner-s3-policy
└── Grants read access ONLY to public-research/ in ONE bucket
    If this Lambda is compromised it can only read
    approved documents — nothing sensitive is reachable

This is least privilege applied at the resource level
not just the action level
```

### driftlock-pii-scanner-comprehend-policy

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowComprehendPIIDetection",
            "Effect": "Allow",
            "Action": "comprehend:DetectPiiEntities",
            "Resource": "*"
        }
    ]
}
```

### Comprehend Subscription Note

```
This policy exists and is attached to the role
However Amazon Comprehend requires a subscription
not available on the free tier development account

SubscriptionRequiredException returned when called:
"The AWS Access Key Id needs a subscription
 for the service"

Resolution:
Lambda uses custom regex-based PII detection instead
Policy retained for documentation purposes and to
show what production implementation requires

Production recommendation:
Enable Amazon Comprehend on the account
OR use Amazon Macie for continuous S3 scanning
Both provide more sophisticated PII detection
than custom regex patterns
```

---

## Service Substitutions

### Amazon Macie → Custom Regex Scanner

```
What Macie provides:
├── Continuous automated S3 scanning
├── Native S3 integration
├── Managed data identifiers
├── Findings dashboard
└── Automatic alerting on PII discovery

Why substituted:
Macie requires a subscription
Minimum $1/month per bucket scanned
Not available on free tier account

What was built instead:
driftlock-pii-scanner Lambda
├── 14 custom regex patterns
├── Scans public-research/ on demand
├── Logs findings to CloudWatch
└── Produces clean scan report

Production recommendation:
Enable Amazon Macie on the account
Configure it to scan driftlock-ai-knowledge-lab-east1
Set up findings export to CloudWatch Events
```

### Amazon Comprehend → Custom Regex Scanner

```
What Comprehend provides:
├── ML-based NLP entity detection
├── Higher accuracy than regex
├── Handles variations and context
├── 50,000 units/month free tier (on eligible accounts)
└── DetectPiiEntities API

Why substituted:
Comprehend subscription required on this account
SubscriptionRequiredException on first API call

What was built instead:
Same driftlock-pii-scanner Lambda
Custom regex handles well-structured PII patterns

Production recommendation:
Use Amazon Comprehend for NLP-based detection
Catches context-dependent PII that regex misses
```

### AWS WAF → API Gateway Throttling

```
What WAF provides:
├── Per-IP rate limiting
├── Content inspection (SQL injection, XSS)
├── AWS Managed Rule Groups
├── Known bad inputs blocking
└── IP reputation list enforcement

Why substituted:
WAF Web ACL created successfully (driftlock-waf-acl)
Attachment to API Gateway requires subscription
ListResourcesForWebACL returned SubscriptionRequiredException

What was implemented instead:
API Gateway throttling on $default stage:
├── Rate limit:  100 requests/second
└── Burst limit: 50 requests

Production recommendation:
Attach driftlock-waf-acl to driftlock-guardrail-api
$default stage using Associated AWS Resources tab
Provides per-IP rate limiting and content inspection
```

---

## AWS Resources Created This Scenario

| Resource | Type | Region | Purpose |
|---|---|---|---|
| driftlock-query-guardrail | Bedrock Guardrail | us-east-1 | Runtime query and response governance |
| driftlock-guardrail-api | API Gateway HTTP API | us-east-1 | HTTPS endpoint for AI assistant queries |
| driftlock-waf-acl | WAF Web ACL | us-east-1 | API protection (created, not attached) |
| driftlock-guardrail-assistant | Lambda | us-east-1 | Query orchestration with guardrail |
| driftlock-pii-scanner | Lambda | us-east-1 | On-demand PII discovery scanner |
| driftlock-reconnaissance-alarm | CloudWatch Alarm | us-east-1 | Reconnaissance behavior detection |

---

## Key Governance Lessons

### 1. Managed policy quotas require proactive management
AWS accounts have a quota of 10 managed policies per IAM
entity. As projects grow permissions accumulate. Regular
audits and consolidation into inline policies prevents
hitting the quota unexpectedly.

### 2. Inline policies are better for project-specific permissions
Inline policies cannot be accidentally attached to other
identities. They are deleted when the identity is deleted.
They are visible only on the identity they belong to.
Use inline policies for permissions specific to one
Lambda function or service role.

### 3. cloudwatch:PutMetricData cannot be resource-scoped
CloudWatch metrics do not have individual ARNs.
PutMetricData must use Resource: * even in a
least privilege policy. This is a known AWS limitation.
The risk is acceptable because the action itself is
narrowly defined — it can only write metrics,
not read or modify other resources.

### 4. Document substitutions as production paths
When free tier limitations prevent implementing the
recommended service, document the substitution honestly
and note the production recommendation. This demonstrates
architectural maturity and shows the path forward.
It is not a gap — it is a documented design decision.

### 5. Scoped S3 policies are stronger than managed policies
AmazonS3ReadOnlyAccess grants access to all buckets.
A scoped inline policy granting access to one folder
in one bucket is significantly stronger. Always scope
S3 permissions to the minimum required prefix and bucket.
```
