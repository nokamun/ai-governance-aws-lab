# AXIOM AI Governance AWS Lab

**AI Governance | Security Architecture | Data Protection | Cloud Security**

This repository explores how modern systems can safely integrate AI assistants without exposing sensitive data. The labs demonstrate governance-first security architecture using principles such as least privilege, data boundaries, and monitoring controls to protect organizational information.

Each lab simulates real-world scenarios where AI capabilities must operate within defined security and governance boundaries.

---

## Scenarios

| # | Scenario | Key Services | Status |
|---|---|---|---|
| 01 | [Data Boundary Governance](scenarios/scenario-01-data-boundary-governance/README.md) | S3, IAM, Lambda, Bedrock, S3 Vectors | ✅ Complete |
| 02 | Query Guardrails | Bedrock Guardrails, Macie, WAF, CloudWatch Alarms | ✅ Complete |
| 03 | OWASP LLM Attack Defense | Bedrock Guardrails, WAF, S3 Object Lock, S3 Versioning | 🔄 In Progress  |
| 04 | Zero Trust AI Assistant | Verified Access, Cognito, Bedrock Agents | 📋 Planned |
| 05 | Audit and Detection | GuardDuty, Security Hub, Detective, CloudTrail | 📋 Planned |
| 06 | Governed Data Lake | Lake Formation, Glue, S3 | 📋 Planned |

---

## The Learning Arc

Each scenario closes a gap the previous one left open:

```
Scenario 01 — Keep bad data out
              S3 ingestion boundaries + IAM tag-based access control

Scenario 02 — Filter bad queries and responses in real time
              Runtime guardrails + PII redaction + anomaly detection

Scenario 03 — Defend against deliberate attacks on the AI itself
              Prompt injection defense + data poisoning prevention
              Based on OWASP Top 10 for Large Language Models

Scenario 04 — Lock down identity and access completely
              Zero trust architecture for AI assistant interactions

Scenario 05 — Detect and investigate what slips through
              Full audit trail correlation and threat detection

Scenario 06 — Govern the data lake feeding everything
              Classification, access control, and lineage at scale
```

---

## Research Focus

- **Data access boundaries** — Restricting AI assistants to approved knowledge sources using identity controls and ingestion boundaries
- **Governance controls for automated systems** — Enforcing least privilege on AI model execution roles and service identities
- **Monitoring and audit visibility** — Capturing allow and deny events across CloudTrail and CloudWatch for full audit trails
- **Security risks introduced by autonomous workflows** — Understanding how AI systems interact with cloud services and where governance gaps emerge
- **OWASP LLM attack defense** — Protecting AI models from prompt injection, data poisoning, and adversarial inputs

---

## Architecture Principles

Each scenario is built around three core principles:

```
Prevention    → Boundaries enforced before access is attempted
Detection     → All activity logged and auditable
Defense Depth → Multiple independent controls covering the same boundary
```

---

## Repository Structure

```
ai-governance-aws-lab/
├── README.md                              ← you are here
│
├── scenario-01-basic-data-boundary/
│   ├── README.md                          ← architecture and validation
│   ├── iam-permissions.md                 ← permissions log and lessons learned
│   ├── lambda/
│   │   ├── driftlock-ai-assistant.py      ← Track B: S3 direct access
│   │   └── driftlock-bedrock-assistant.py ← Track A: Bedrock KB queries
│   └── policies/
│       ├── S3DataBoundaryPolicy.json       ← tag-based IAM policy
│       └── driftlock-bedrock-kb-policy.json← Bedrock query permissions
│
├── scenario-02-query-guardrails/
│   └── (in progress)
│
├── scenario-03-owasp-llm-defense/
│   └── (coming soon)
│
├── scenario-04-zero-trust-ai-assistant/
│   └── (coming soon)
│
├── scenario-05-audit-and-detection/
│   └── (coming soon)
│
└── scenario-06-governed-data-lake/
    └── (coming soon)
```

---

## License

This project is licensed under the MIT License.

Copyright (c) 2026 Wynoka Munlyn
