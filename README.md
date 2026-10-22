# Production AWS Terraform Projects (Simulated on Floci)

A comprehensive, production-grade repository of daily Infrastructure as Code (IaC) architectures built with HashiCorp Terraform and validated against **Floci** (Local AWS Emulator).

Each project includes end-to-end Terraform code, automated visual architecture diagrams, and a dedicated SRE / Cloud Architect interview deep-dive guide.

> **Full Curriculum & Roadmap:** See **[CURRICULUM_ROADMAP.md](./CURRICULUM_ROADMAP.md)** for the complete 2026 SRE & DevOps multi-phase project plan.

---

## Project Catalog

| Day / Project | Architecture Focus | Core AWS Services | Architecture Diagram | Interview Q&A |
| :--- | :--- | :--- | :---: | :---: |
| **[01-resilient-s3-sqs-dlq-pipeline](./01-resilient-s3-sqs-dlq-pipeline)** | Resilient Event-Driven Ingestion Pipeline with DLQ & Poison Pill Protection | `S3`, `SQS`, `KMS CMK`, `Bucket Notifications`, `Queue Policies` | [View SVG](./01-resilient-s3-sqs-dlq-pipeline/project-01-architecture.svg) | [INTERVIEW_QNA.md](./01-resilient-s3-sqs-dlq-pipeline/INTERVIEW_QNA.md) |
| **[02-resilient-serverless-api-dynamodb](./02-resilient-serverless-api-dynamodb)** | Resilient Serverless Transaction Engine with Idempotent PutItem & GSI | `API Gateway`, `Lambda`, `DynamoDB`, `KMS CMK`, `IAM Roles` | [View SVG](./02-resilient-serverless-api-dynamodb/project-02-architecture.svg) | [INTERVIEW_QNA.md](./02-resilient-serverless-api-dynamodb/INTERVIEW_QNA.md) |
| **[03-multiaz-zerotrust-vpc-endpoints](./03-multiaz-zerotrust-vpc-endpoints)** | Multi-AZ Zero-Trust VPC with S3 & DynamoDB Private Gateway Endpoints | `VPC`, `Subnets`, `Route Tables`, `IGW`, `VPC Endpoints` | [View SVG](./03-multiaz-zerotrust-vpc-endpoints/project-03-architecture.svg) | [INTERVIEW_QNA.md](./03-multiaz-zerotrust-vpc-endpoints/INTERVIEW_QNA.md) |
| **[04-private-microservice-ingress-alb](./04-private-microservice-ingress-alb)** | Private Microservice Ingress with Internal ALB & Security Group Chaining | `ALB`, `Target Groups`, `Security Groups`, `Listener Rules` | [View SVG](./04-private-microservice-ingress-alb/project-04-architecture.svg) | [INTERVIEW_QNA.md](./04-private-microservice-ingress-alb/INTERVIEW_QNA.md) |

---

## Local Verification Architecture

All projects run against **Floci** locally with zero AWS cloud costs:
* **Floci AWS Engine:** `http://localhost:4566`
* **Floci Web Console:** `http://localhost:4500`
