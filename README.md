# AI Governance AWS Lab

**AI Governance | Security Architecture | Data Protection | Cloud Security**

This repository explores how modern systems can safely integrate AI assistants without exposing sensitive data. The labs demonstrate governance-first security architecture using principles such as least privilege, data boundaries, and monitoring controls to protect organizational information.

Each lab simulates real-world scenarios where AI capabilities must operate within defined security and governance boundaries.

---

## Scenarios

| # | Scenario | Key Services | Status |
|---|---|---|---|
| 01 | [Data Boundary Governance](scenarios/scenario-01-data-boundary-governance/README.md) | S3, IAM, Lambda, Bedrock, S3 Vectors | ✅ Complete |
| 02 | Query Guardrails | Bedrock Guardrails, WAF, Macie | 🔄 Planned |
| 03 | Zero Trust AI Assistant | Verified Access, Cognito, Bedrock Agents | 🔄 Planned |
| 04 | Audit and Detection | GuardDuty, Security Hub, Detective | 🔄 Planned |
| 05 | Governed Data Lake | Lake Formation, Glue, S3 | 🔄 Planned |

---

## Research Focus

- **Data access boundaries** — Restricting AI assistants to approved knowledge sources using identity controls and ingestion boundaries
- **Governance controls for automated systems** — Enforcing least privilege on AI model execution roles and service identities
- **Monitoring and audit visibility** — Capturing allow and deny events across CloudTrail and CloudWatch for full audit trails
- **Security risks introduced by autonomous workflows** — Understanding how AI systems interact with cloud services and where governance gaps emerge

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
├── README.md                              
├── scenario-01-basic-data-boundary/
│   ├── README.md                          ← architecture and validation
│   ├── iam-permissions.md                 ← permissions log and lessons learned
│   ├── lambda/
│   │   ├── driftlock-ai-assistant.py      ← Track B: S3 direct access
│   │   └── driftlock-bedrock-assistant.py ← Track A: Bedrock KB queries
│   └── policies/
│       ├── S3DataBoundaryPolicy.json       ← tag-based IAM policy
│       └── driftlock-bedrock-kb-policy.json← Bedrock query permissions
├── scenario-02-query-guardrails/
│   └── (coming soon)
├── scenario-03-zero-trust-ai-assistant/
│   └── (coming soon)
├── scenario-04-audit-and-detection/
│   └── (coming soon)
└── scenario-05-governed-data-lake/
    └── (coming soon)
```

---

## License

This project is licensed under the MIT License.

Copyright (c) 2026 Wynoka Munlyn
