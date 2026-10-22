# 2026 Production SRE & DevOps Terraform Architecture Roadmap

A structured, industry-aligned curriculum of daily real-time production projects. Every architecture is built using HashiCorp Terraform, validated locally against **Floci** (AWS Emulator), accompanied by an automated Python Graphviz architecture diagram, and deep-dived with an SRE / Cloud Architect interview Q&A guide.

---

## Pedagogical Pillars (2026 Standards)

1. **Zero-Trust Security by Default:** Least privilege IAM, KMS Customer Managed Keys (CMKs), VPC Interface/Gateway Endpoints to eliminate internet traversal, and Confused Deputy protections.
2. **FinOps & Cost Governance:** Architectural decisions that reduce NAT Gateway costs, optimize S3 storage tiers, and leverage serverless / auto-scaling elasticity.
3. **Resilience & High Availability:** Multi-AZ redundancy, Dead Letter Queues (DLQ), exponential backoff, circuit breaking, idempotency, and graceful degradation.
4. **First-Principles Observability:** Telemetry as code, composite alarms, metric filters, synthetics, and actionable alerting.

---

## 30-Day Master Project Matrix

| Phase | Project ID | Project Name | Key AWS Services | Real-World SRE & DevOps Focus | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **Phase 1: Ingestion & Serverless Core** | **01** | **[Resilient S3-SQS-DLQ Ingestion Pipeline](./01-resilient-s3-sqs-dlq-pipeline)** | S3, SQS, DLQ, KMS CMK | Poison pill isolation, redrive policies, confused deputy defense | **Completed** |
| | **02** | **[Resilient Serverless API & DynamoDB](./02-resilient-serverless-api-dynamodb)** | API Gateway, Lambda, DynamoDB, KMS | Idempotent PutItem (`attribute_not_exists`), GSI, TTL auto-purge | **Completed** |
| **Phase 2: Resilient Networking & Zero-Trust** | **03** | **[Multi-AZ Zero-Trust VPC & Private Endpoints](./03-multiaz-zerotrust-vpc-endpoints)** | VPC, Multi-AZ Subnets, Route Tables, IGW, S3/DynamoDB Gateway Endpoints | Eliminating NAT data transfer costs, private routing, egress lockdown | **Completed** |
| | **04** | **[Private Microservice Ingress with Internal ALB](./04-private-microservice-ingress-alb)** | ALB, Private Target Groups, Security Groups, Listener Rules | Least-privilege SG chaining, zero public IP footprint, health checks | **Completed** |
| **Phase 3: Event-Driven & Decoupling** | **05** | **EventBridge Event Bus & Content-Based Routing** | EventBridge Bus, Rule Patterns, SQS Targets, CloudWatch DLQ | Decoupled event mesh, schema matching, filter rules without compute | *Next Up* |
| | **06** | **SNS Multi-Consumer Fan-Out with Message Filtering** | SNS Topic, SQS Subscriptions, Subscription Filter Policies, KMS | Fan-out pub/sub, subscription attribute filtering, cross-service decoupling | Upcoming |
| | **07** | **Step Functions Distributed Saga Orchestration** | Step Functions, Lambda, DynamoDB, SNS | Two-phase commit / compensation transactions, retry blocks, catch states | Upcoming |
| **Phase 4: Containerized Platforms & Autoscaling** | **08** | **ECS Fargate Resilient Web Service** | ECS Fargate, ECR, Task Definitions, ALB, CloudWatch Logs | Container orchestration, task execution IAM roles, rolling deployments | Upcoming |
| | **09** | **ECS Target Tracking Autoscaling with Stress Simulator** | ECS Service, CloudWatch CPU/Memory Alarms, Application Auto Scaling | Predictive/target tracking scaling, scale-in cooldowns, connection draining | Upcoming |
| **Phase 5: Observability as Code** | **10** | **CloudWatch Composite Alarms & SRE Alert Routing** | CloudWatch Alarms, Composite Alarm (AND/OR logic), SNS, Lambda | Alert fatigue reduction, symptom vs root-cause suppression | Upcoming |
| | **11** | **Log Metric Filters & Real-Time Security Alerting** | CloudWatch Log Groups, Metric Filters, CloudWatch Dashboards, SNS | Parsing 5xx error spikes and unauthorized 403 API calls via regex | Upcoming |
| **Phase 6: Data Tier High Availability & Caching** | **12** | **Multi-AZ RDS Aurora PostgreSQL with Read Replicas** | RDS Multi-AZ, Subnet Groups, Secrets Manager, KMS | Synchronous replication failover, read offloading, automated parameter tuning | Upcoming |
| | **13** | **ElastiCache Redis Read-Aside Caching Layer** | ElastiCache Redis, Lambda, DynamoDB, VPC | Sub-millisecond latency, cache invalidation, cache-stampede mitigation | Upcoming |
| | **14** | **DynamoDB Streams & Event-Driven Change Data Capture** | DynamoDB Streams, Lambda Consumer, OpenSearch / S3 Archive | Real-time CDC (Change Data Capture), audit logging, event-sourcing pattern | Upcoming |
| **Phase 7: Security Governance & Secrets** | **15** | **Zero-Downtime Secrets Manager Auto-Rotation** | Secrets Manager, Rotation Lambda, RDS/DynamoDB, IAM | 30-day credential rotation, two-step version staging (`AWSPENDING`/`AWSCURRENT`) | Upcoming |
| | **16** | **IAM Permission Boundaries & Least-Privilege Delegated Admin** | IAM Policies, Permission Boundaries, Cross-Account Roles | Guardrailing developer roles, preventing privilege escalation | Upcoming |
| **Phase 8: Edge Delivery & Static Resilience** | **17** | **CloudFront CDN with S3 Origin Access Control (OAC)** | CloudFront, S3 Bucket, OAC, KMS, Route 53 | Edge caching, blocking direct S3 access, TLS 1.3 enforcement | Upcoming |
| | **18** | **API Gateway Rate Limiting, Throttling & Usage Plans** | API Gateway, Usage Plans, API Keys, CloudWatch Metrics | Throttling burst vs rate limits, DDoS / noisy neighbor protection | Upcoming |
| **Phase 9: Reliability & Chaos Engineering** | **19** | **Circuit Breaker Pattern with Lambda & DynamoDB** | Lambda, DynamoDB (State Tracking), SQS, CloudWatch | Closed/Open/Half-Open state transitions, failing fast during downstream degradation | Upcoming |
| | **20** | **Disaster Recovery: Active-Passive S3 Cross-Region Replication** | S3 CRR, KMS Multi-Region Keys, IAM Replication Role | RPO & RTO minimization, asynchronous replication, compliance retention | Upcoming |

---

## Daily Project Standard Structure

Every project folder inside this repository maintains a unified, production-grade directory layout:

```text
NN-project-slug/
├── main.tf                 # Core AWS resource definitions
├── variables.tf            # Configurable inputs with strict type constraints & descriptions
├── outputs.tf              # Essential infrastructure outputs (ARNs, Endpoints, IDs)
├── providers.tf            # Terraform & AWS provider config pointed to Floci (localhost:4566)
├── terraform.tfvars        # Default local test values
├── lambda_src/             # (Optional) Application code (Python 3.11)
├── generate_diagram.py     # Automated Python Graphviz architecture visualizer
├── architecture_diagram.png# Generated PNG diagram embedded into README
├── INTERVIEW_QNA.md        # 5+ First-principles SRE & Cloud Architect interview scenarios
└── README.md               # Step-by-step verification, architectural why, and Floci screenshots
```

---

## Local Verification Commands

```powershell
# 1. Start Floci Engine & Web UI
wsl -d podman-machine-default env XDG_RUNTIME_DIR=/run/user/1000 podman start floci floci-ui

# 2. Verify Floci Status
curl.exe http://localhost:4500/api/clouds/aws/status

# 3. Initialize & Apply Project
terraform init
terraform plan
terraform apply -auto-approve

# 4. Generate Architecture Diagram
python generate_diagram.py

# 5. Clean Up
terraform destroy -auto-approve
```
