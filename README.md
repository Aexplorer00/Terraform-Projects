# Production AWS Terraform Projects (Simulated on Floci)

A comprehensive, production-grade repository of daily Infrastructure as Code (IaC) architectures built with HashiCorp Terraform and validated against **Floci** (Local AWS Emulator).

Each project includes end-to-end Terraform code, automated visual architecture diagrams, and a dedicated SRE / Cloud Architect interview deep-dive guide.

---

## Project Catalog

| Day / Project | Architecture Focus | Core AWS Services | Architecture Diagram | Interview Q&A |
| :--- | :--- | :--- | :---: | :---: |
| **[01-resilient-s3-sqs-dlq-pipeline](./01-resilient-s3-sqs-dlq-pipeline)** | Resilient Event-Driven Ingestion Pipeline with DLQ & Poison Pill Protection | `S3`, `SQS`, `KMS CMK`, `Bucket Notifications`, `Queue Policies` | [View Diagram](./01-resilient-s3-sqs-dlq-pipeline/architecture_diagram.png) | [INTERVIEW_QNA.md](./01-resilient-s3-sqs-dlq-pipeline/INTERVIEW_QNA.md) |

---

## Local Verification Architecture

All projects run against **Floci** locally with zero AWS cloud costs:
* **Floci AWS Engine:** `http://localhost:4566`
* **Floci Web Console:** `http://localhost:4500`
