# IAM Permissions Log — Scenario 01
# Data Boundary Governance

This document tracks every IAM permission added during Scenario 01,
why it was added, and the governance principle it demonstrates.

---

## Identities Created

| Identity | Type | Purpose |
|---|---|---|
| driftlock-dev | IAM User | Development identity — replaces root for all day-to-day operations |
| driftlock-ai-assistant-role | IAM Role | Lambda execution role for Track B (S3 direct access) |
| driftlock-bedrock-assistant-role | IAM Role | Lambda execution role for Track A (Bedrock KB access) |
| AmazonBedrockExecutionRole-driftlock-kb | IAM Role | Bedrock service role for Knowledge Base operations |

---

## IAM User: driftlock-dev

### Why this user was created
AWS explicitly blocks certain Bedrock operations when performed as the
root user. This is an intentional AWS security control. All development
work for this project is performed as driftlock-dev, never as root.

### Root User Policy
```
Root user is reserved for account-level settings and billing only.
All development work is performed as driftlock-dev.
This follows AWS best practices for identity governance.
```

### Permissions Log

| # | Permission | Type | Reason Added |
|---|---|---|---|
| 1 | AmazonBedrockFullAccess | Managed Policy | Required for Knowledge Base creation and management |
| 2 | AmazonS3ReadOnlyAccess | Managed Policy | Read access to S3 knowledge repository |
| 3 | IAMFullAccess | Managed Policy | Required to create and manage service roles during KB setup |
| 4 | AWSLambda_ReadOnlyAccess | Managed Policy | Bedrock KB wizard requires lambda:ListFunctions during setup |
| 5 | driftlock-s3vectors-policy | Inline Policy | Bedrock KB requires full S3 Vectors permission set to provision vector store |

### Lesson Learned — Setup vs Operational Permissions
During Knowledge Base creation, the full S3 Vectors permission set was
required. Individual permissions caused repeated timeouts mid-wizard.

This reflects a real-world governance principle:

```
During setup/provisioning  → broader permissions acceptable
After setup is complete    → scope down to operational minimum
```

This is called just-in-time permissions in enterprise governance.
A future improvement would be to scope driftlock-s3vectors-policy
down to operational permissions only after setup completes:

```
Operational minimum (post-setup):
├── s3vectors:PutVectors
├── s3vectors:GetVectors
├── s3vectors:QueryVectors
└── s3vectors:ListVectors
```

---

## Lambda Execution Role: driftlock-ai-assistant-role
### Track B — Direct S3 Access with Tag-Based Conditions

### Permissions Log

| # | Permission | Type | Reason Added |
|---|---|---|---|
| 1 | CloudWatchLogsPolicy | Managed Policy | Basic Lambda execution — write logs to CloudWatch |
| 2 | S3DataBoundaryPolicy-Scenario01 | Inline Policy | Tag-based data classification boundary on S3 access |

### S3DataBoundaryPolicy-Scenario01

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowPublicResearch",
            "Effect": "Allow",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::driftlock-ai-knowledge-lab-east1/*",
            "Condition": {
                "StringEquals": {
                    "s3:ExistingObjectTag/data-classification": "public-research"
                }
            }
        },
        {
            "Sid": "DenySensitiveData",
            "Effect": "Deny",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::driftlock-ai-knowledge-lab-east1/*",
            "Condition": {
                "StringEquals": {
                    "s3:ExistingObjectTag/data-classification": "sensitive"
                }
            }
        }
    ]
}
```

### Why tag-based conditions instead of folder separation
Folder-based separation is a coarse control — moving a file breaks
the boundary. Tag-based conditions mean governance travels with the
data regardless of where it is stored. A sensitive document remains
protected even if moved to a different folder or bucket.

---

## Lambda Execution Role: driftlock-bedrock-assistant-role
### Track A — Bedrock Knowledge Base Access

### Permissions Log

| # | Permission | Type | Reason Added |
|---|---|---|---|
| 1 | CloudWatchLogsPolicy | Managed Policy | Basic Lambda execution — write logs to CloudWatch |
| 2 | driftlock-bedrock-kb-policy | Inline Policy | Required to query Bedrock Knowledge Base and invoke Nova Lite model |

### driftlock-bedrock-kb-policy

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
                "arn:aws:bedrock:us-east-1:605893375580:knowledge-base/2FC12FO9Q8",
                "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-lite-v1:0"
            ]
        }
    ]
}
```

### Why resource-scoped ARNs
Instead of granting access to all Bedrock resources (*), this policy
scopes permissions to the specific Knowledge Base ID and model ARN.
This means the Lambda can only query this specific Knowledge Base
and invoke this specific model — nothing else in Bedrock.

---

## Bedrock Service Role: AmazonBedrockExecutionRole-driftlock-kb
### Auto-generated by AWS during Knowledge Base creation

### Why auto-generation was used
Manual role creation repeatedly failed due to incomplete permission
sets causing Knowledge Base creation timeouts. AWS auto-generation
produces a role with the exact permissions Bedrock requires.

### Lesson Learned — When to use auto-generated roles
When a managed service offers to create its own service role,
allowing auto-generation is often the right call because:

```
Manual creation  → risk of missing permissions
                 → timeouts and errors mid-provisioning
                 → frustrating iteration cycle

Auto-generation  → AWS knows exact permission requirements
                 → provisioning completes successfully
                 → inspect afterward to understand what was needed
```

The correct governance approach is:
1. Allow auto-generation to complete setup successfully
2. Inspect the generated role to understand what was created
3. Document the permissions for future reference
4. Consider manual recreation with scoped permissions post-setup

### Trust Policy Applied
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "bedrock.amazonaws.com"
            },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {
                    "aws:SourceAccount": "605893375580"
                }
            }
        }
    ]
}
```

The SourceAccount condition prevents other AWS accounts from
assuming this role even if they reference it — a security
best practice for service role trust policies.

---

## Key Governance Lessons

### 1. Never operate as root
AWS blocks sensitive operations for root users intentionally.
Always create a named IAM user for development work.

### 2. Least privilege is incremental
Start with minimum permissions, add only what errors require,
document every addition. The final policy tells an honest story
of exactly what each service needs.

### 3. Setup permissions vs operational permissions
Provisioning often requires broader permissions than ongoing
operation. Grant broad access to complete setup, then scope
down to operational minimum afterward.

### 4. IAM policies don't protect vector stores
IAM tag conditions on S3 apply to direct S3 access only.
Bedrock Knowledge Bases query the vector store directly,
bypassing IAM tag conditions entirely. Governance must be
applied at ingestion — scope the data source S3 URI to
approved folders only.

### 5. Resource naming tombstone period
Deleted AWS resource names may be temporarily unavailable
for reuse even across regions. Always have a naming fallback
ready (append -v2, -kb, -01, etc.).

### 6. Region alignment is mandatory
S3 buckets and Bedrock Knowledge Bases must be in the same
region. Cross-region access produces authorization errors
that are not immediately obvious from the error message.

---

## AWS Resource Inventory

| Resource | Type | Region | Purpose |
|---|---|---|---|
| driftlock-ai-knowledge-lab-east1 | S3 Bucket | us-east-1 | Knowledge repository |
| driftlock-knowledge-base-v2 | Bedrock KB | us-east-1 | AI research assistant KB |
| driftlock-ai-assistant | Lambda | us-east-1 | Track B validation function |
| driftlock-bedrock-assistant | Lambda | us-east-1 | Track A Bedrock query function |

## Cleanup Required

| Resource | Type | Reason |
|---|---|---|
| driftlock-knowledge-base | Bedrock KB | Original KB created without data source |
| driftlock-knowledge-kb | Bedrock KB | us-east-2 attempt — wrong region |
| bedrock-knowledge-base-brwmbj | S3 Vectors | Orphaned vector store from failed creation |
