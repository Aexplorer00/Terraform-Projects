# Project 02: SRE / Cloud Architect Interview Masterclass
## Topic: Resilient Serverless Transaction Engine (API Gateway -> Lambda -> DynamoDB)

---

### Q1: How does API / Database Idempotency work, and how did we implement it?
**Answer:**
- **The Problem:** In distributed systems, networks are unreliable. A client sends a payment request, the backend processes it, but the client experiences a connection drop before receiving `200 OK`. The client retries. Without idempotency, the customer gets charged twice.
- **The Solution:**
  1. The client provides a unique `transaction_id` (Idempotency Key).
  2. We use DynamoDB's **Conditional PutItem**:
     ```python
     table.put_item(
         Item=item,
         ConditionExpression="attribute_not_exists(transaction_id)"
     )
     ```
  3. If the record already exists, DynamoDB returns `ConditionalCheckFailedException`, and our Lambda returns `HTTP 409 Conflict` (or returns the previously cached response) without re-executing business logic.

---

### Q2: What is the difference between a DynamoDB Global Secondary Index (GSI) and a Local Secondary Index (LSI)?
**Answer:**
| Feature | Global Secondary Index (GSI) | Local Secondary Index (LSI) |
| :--- | :--- | :--- |
| **Partition Key** | Can have a **different** Partition Key from the main table. | **Must share** the exact same Partition Key as the main table. |
| **Creation Time** | Can be created or deleted **at any time** (even on live production tables). | **Must be created at table creation time**; cannot be added later. |
| **Capacity (RCU/WCU)** | Has its own independent read/write capacity units. | Consumes capacity units from the main table. |
| **Consistency** | **Eventually Consistent** only. | Supports both Strongly Consistent and Eventually Consistent reads. |
| **Size Limit** | No partition size limits. | Limited to 10 GB per partition key value. |

*In our architecture:* We used a GSI on `customer_id` so we can query all transactions for a customer across any partition.

---

### Q3: When should you choose DynamoDB On-Demand (`PAY_PER_REQUEST`) vs Provisioned Capacity?
**Answer:**
- **Choose On-Demand (`PAY_PER_REQUEST`):**
  - Unpredictable or spiky traffic workloads (e.g. flash sales, new product launches).
  - Unknown baseline traffic patterns.
  - Idle applications (you pay $0 when there are zero read/write requests).
- **Choose Provisioned Capacity with Auto Scaling:**
  - Predictable, steady-state baseline traffic.
  - Cost optimization at scale: Provisioned capacity is ~6x to 7x cheaper per request than On-Demand when traffic is constant and well-utilized.

---

### Q4: How does DynamoDB Time-To-Live (TTL) work under the hood?
**Answer:**
- **The Mechanism:** You designate an attribute (e.g. `ttl`) containing a Unix epoch timestamp in seconds.
- **Asynchronous Purging:** DynamoDB's internal background sweeper identifies and deletes expired items typically within 48 hours of expiration.
- **Cost & Capacity:** Deletions caused by TTL consume **ZERO Read Capacity Units (RCUs) and ZERO Write Capacity Units (WCUs)**. It is completely free automated data purging.
- **Audit/Streams Note:** If DynamoDB Streams are enabled, TTL deletions emit a stream record with `userIdentity.type = "Service"` and `principalId = "dynamodb.amazonaws.com"`, allowing you to archive expired records into S3 Glacier before deletion.

---

### Q5: How do you mitigate AWS Lambda "Cold Starts" in production?
**Answer:**
1. **Execution Context & Connection Reuse:** Initialize database connections, AWS SDK clients (`boto3.resource("dynamodb")`), and HTTP sessions outside the `lambda_handler`. Warm containers reuse established TCP/TLS sockets.
2. **Provisioned Concurrency:** Pre-initializes a fixed pool of execution environments so invocations never wait for container spin-up.
3. **Minimize Package Size:** Keep deployment packages lean; use native runtimes or compiled binaries rather than heavy dependencies.
4. **Memory Allocation:** Increasing Lambda memory proportionally allocates more CPU cores and network bandwidth, drastically speeding up initialization time.

---

### Q6: What is the API Gateway "Token Bucket" algorithm for throttling?
**Answer:**
- **Rate & Burst:** API Gateway uses the Token Bucket algorithm to protect backend microservices from being overwhelmed:
  - **Rate Limit (Steady State):** The average number of requests per second allowed continuously (e.g. 100 req/sec). Tokens refill into the bucket at this rate.
  - **Burst Limit:** The maximum capacity of the bucket (e.g. 200 tokens). Allows short-lived traffic spikes to be processed without rejection.
- When the bucket is empty, API Gateway immediately rejects excess requests with **HTTP 429 Too Many Requests**, protecting downstream Lambda and databases.
