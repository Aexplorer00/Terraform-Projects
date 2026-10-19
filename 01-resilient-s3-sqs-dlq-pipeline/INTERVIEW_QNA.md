# Project 01: SRE / Cloud Architect Interview Masterclass
## Topic: Resilient Event-Driven Ingestion Pipeline (S3 + SQS + DLQ + KMS)

---

### Q1: How does AWS KMS Envelope Encryption work, and why does S3 use it instead of encrypting data directly with the CMK?
**Answer:**
- **The Problem:** Encrypting large payloads (e.g. 5 GB files) directly in KMS would create massive network bottlenecks and exhaust KMS API rate limits.
- **Envelope Encryption Pattern:**
  1. S3 calls `kms:GenerateDataKey` with the CMK ARN.
  2. KMS generates and returns a **Plaintext Data Encryption Key (DEK)** and an **Encrypted DEK** (encrypted by the CMK).
  3. S3 uses the Plaintext DEK to encrypt the object payload locally in memory using **AES-256-GCM**.
  4. S3 immediately wipes the Plaintext DEK from RAM and writes the **ciphertext object + Encrypted DEK (as metadata)** to disk.
- **Key Takeaway:** The master Customer Managed Key (CMK) **never leaves the KMS Hardware Security Module (HSM)**.

---

### Q2: What is the SQS Visibility Timeout, and what failure occurs if processing time exceeds it?
**Answer:**
- **The Mechanism:** When a consumer pulls a message, SQS sets a lease timer (`visibility_timeout_seconds`, e.g. 30s) during which the message is hidden from all other workers.
- **The Failure Mode:** If a worker takes 45s to process, the lease expires at second 31. SQS assumes the worker crashed and makes the message visible again. A second worker pulls the same message, causing **duplicate concurrent processing** and race conditions.
- **Production Solutions:**
  1. *Infrastructure:* Configure `visibility_timeout_seconds` to at least **6x the average processing duration**.
  2. *Application Heartbeat:* The worker calls `ChangeMessageVisibility` periodically while still actively processing long jobs.

---

### Q3: What is a "Poison Pill" message, and how does a Dead-Letter Queue (DLQ) protect the system?
**Answer:**
- **The Hazard:** A malformed payload (e.g. invalid JSON, missing schema field) that crashes consumer workers every time it is read.
- **Without a DLQ:** The worker crashes $\rightarrow$ timeout expires $\rightarrow$ worker retries $\rightarrow$ crashes again indefinitely. This causes **Head-of-Line (HoL) Blocking** and a **Retry Storm**, preventing valid messages from being processed and spiking compute costs.
- **With a DLQ & Redrive Policy (`maxReceiveCount = 3`):** After 3 failed attempts, SQS automatically moves the message to the DLQ with **14-day retention** (`dlq_message_retention_seconds = 1209600`), allowing SREs to inspect the payload, fix bugs, and redrive the message safely.

---

### Q4: Why did we choose SQS Standard instead of SQS FIFO for this pipeline?
**Answer:**
- **Throughput:** Standard SQS offers **virtually unlimited Transactions Per Second (TPS)**, whereas FIFO is capped at 300 msg/sec (or 3,000 with batching).
- **Ordering Requirement:** Independent file uploads do not require strict sequential ordering. Processing Invoice B 2 seconds before Invoice A has zero business impact.
- **When FIFO is Required:** Only when strict sequencing is mandatory—e.g. **financial ledger debits/credits** or **stock trading order books**.

---

### Q5: Why is the `aws:SourceArn` condition mandatory in the SQS Queue Policy?
**Answer:**
- **The Security Risk (Confused Deputy Problem):** S3 uses a resource-based policy (`sqs:SendMessage` granted to `"s3.amazonaws.com"`). Without a condition, an attacker in another AWS account could create an S3 bucket and point its event notifications to your queue ARN, spamming or DDOSing your consumers.
- **The Defense:** Adding `Condition = { ArnEquals = { "aws:SourceArn" = aws_s3_bucket.ingestion_bucket.arn } }` ensures only your specific bucket can publish to the queue.

---

### Q6: Why did we specify `depends_on = [aws_sqs_queue_policy.allow_s3_ingestion]` on the `aws_s3_bucket_notification`?
**Answer:**
- Terraform builds its dependency graph through implicit resource attribute references. The notification references the SQS queue ARN, but not the queue policy.
- When S3 creates a notification, AWS sends an immediate synchronous validation probe to the queue.
- If the policy hasn't finished applying, S3 rejects the notification with an `AccessDenied` or `InvalidArgument` error. `depends_on` guarantees strict sequencing.
