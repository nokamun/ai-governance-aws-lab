# Scenario 01 – Data Boundary Governance

> Restrict an AI assistant to approved knowledge sources using tag-based IAM controls, preventing access to sensitive internal data.

---

## What This Demonstrates

An AI research assistant that can only retrieve documents classified as `public-research`. Attempts to access `sensitive-internal` documents are denied and logged — enforced at the identity layer, not just folder structure.

---

## Architecture

```
User Query
    └── Lambda (AI Assistant)
            ├── IAM Policy [tag condition check]
            │       ├── ALLOW → public-research/*
            │       └── DENY  → sensitive-internal/*
            └── S3 (driftlock-ai-knowledge-lab)
                    ├── public-research/
                    │       ├── ai_governance_notes.txt
                    │       └── market_trends.txt
                    └── sensitive-internal/
                            ├── pricing_strategy.txt
                            └── product_roadmap.txt

All requests logged → CloudTrail + CloudWatch
```

---

## AWS Services

| Service | Role |
|---|---|
| AWS Lambda | AI assistant function |
| Amazon S3 | Knowledge repository with object tagging |
| AWS IAM | Tag-based access policy on Lambda execution role |
| AWS CloudTrail | API-level audit logging |
| Amazon CloudWatch | Execution logs and monitoring |

---

## Controls Implemented

**Tag-Based Data Classification**
S3 objects are tagged with `data-classification: public-research` or `data-classification: sensitive`. The IAM policy evaluates these tags at request time — not folder location.

**Least Privilege Identity**
The Lambda execution role only permits `s3:GetObject` on objects explicitly tagged `public-research`. No wildcard access.

**Deny by Classification**
A dedicated `Deny` statement blocks any retrieval of `sensitive`-tagged objects regardless of other permissions.

**Audit Visibility**
Both allowed and denied requests are captured in CloudTrail and surfaced in CloudWatch Logs.

---

## IAM Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowPublicResearch",
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::driftlock-ai-knowledge-lab/*",
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
      "Resource": "arn:aws:s3:::driftlock-ai-knowledge-lab/*",
      "Condition": {
        "StringEquals": {
          "s3:ExistingObjectTag/data-classification": "sensitive"
        }
      }
    }
  ]
}
```

---

## Validation Results

Four test cases run against the Lambda function:

| Document | Classification | Result |
|---|---|---|
| ai_governance_notes.txt | public-research | ✅ ALLOWED |
| market_trends.txt | public-research | ✅ ALLOWED |
| pricing_strategy.txt | sensitive-internal | ❌ DENIED (AccessDenied) |
| product_roadmap.txt | sensitive-internal | ❌ DENIED (AccessDenied) |

---

## Key Design Decision

Boundary enforcement uses **object tags + IAM conditions** rather than bucket or folder separation. This means governance travels with the data — a sensitive document remains protected regardless of where it is stored.

---

## Known Limitations

- A permissive bucket policy could override the role-level deny. A production implementation would add a matching bucket policy as a second enforcement layer.
- Lambda currently simulates queries via hardcoded test cases. A future iteration connects Amazon Bedrock Knowledge Bases to test real model retrieval behavior against these boundaries.

---

## Next Steps

- **Track A**: Connect Amazon Bedrock + Knowledge Bases to test real AI model retrieval against these boundaries
- **Scenario 02**: Implement query-level guardrails using Amazon Bedrock Guardrails
