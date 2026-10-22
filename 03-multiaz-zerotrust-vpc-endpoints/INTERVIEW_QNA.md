# Project 03: SRE & Cloud Architect Interview Deep-Dive Q&A

### Architecture Focus: Multi-AZ Zero-Trust VPC & Private Gateway Endpoints

---

### Question 1: In high-throughput architectures processing tens of terabytes of S3 logs or DynamoDB queries, why is routing traffic through a NAT Gateway considered an architectural anti-pattern? What is the FinOps calculation?

#### The SRE / Architect Answer:
* **The Cost Driver:** AWS NAT Gateways charge both an **hourly flat fee** (~$0.045/hr per AZ = ~$32.40/month/AZ) and a **per-GB data processing fee** (~$0.045 per GB).
* **FinOps Calculation:**
  - If a distributed cluster in private subnets uploads/downloads **20 TB of data per month** to S3 through a NAT Gateway:
    $$\text{Data Fee} = 20{,}000 \text{ GB} \times \$0.045/\text{GB} = \$900.00/\text{month}$$
  - Plus NAT Gateway hourly instances across 2 AZs: $\sim\$65/\text{month}$.
  - Total NAT Cost: **$\sim\$965/month** just for internal AWS storage traffic!
* **The Solution (Gateway Endpoints):**
  - **AWS VPC Gateway Endpoints for S3 and DynamoDB are completely FREE ($0.00/hr and $0.00/GB processed)**.
  - Traffic never leaves the AWS private network backbone, bypassing NAT Gateways and the public internet entirely, reducing network latency, eliminating data egress costs, and minimizing internet-facing attack surfaces.

---

### Question 2: How does a VPC Gateway Endpoint route traffic under the hood without using an Elastic Network Interface (ENI)?

#### The SRE / Architect Answer:
* Unlike **Interface Endpoints** (which provision an Elastic Network Interface with a private IP inside your subnets), **Gateway Endpoints work at the VPC Route Table layer**.
* **Under the Hood Mechanics:**
  1. AWS maintains managed **Prefix Lists** containing the public IP CIDR ranges of S3 and DynamoDB for each region (e.g., `pl-63a5400a` for `com.amazonaws.us-east-1.s3`).
  2. When you attach a Gateway Endpoint to a Route Table (`aws_route_table.private`), AWS automatically injects the prefix list target pointing to `vpce-xxxx`.
  3. When an EC2 instance or Lambda in the private subnet resolves `s3.us-east-1.amazonaws.com`, it receives a public AWS S3 IP address.
  4. However, the VPC route table's **most specific route matching rule (Longest Prefix Match)** evaluates the destination IP against the prefix list.
  5. The AWS Nitro System / Hypervisor intercepts the packet and routes it directly across the AWS internal hardware fabric directly into S3, never touching an IGW or NAT Gateway.

---

### Question 3: Can a VPC Gateway Endpoint be accessed from an on-premises data center over AWS Direct Connect or a VPN? Why or why not?

#### The SRE / Architect Answer:
* **No.** Gateway Endpoints **cannot** be accessed from on-premises networks over AWS Direct Connect, Site-to-Site VPN, or even VPC Peering.
* **Why:**
  - Gateway Endpoints only exist as route table entries inside the specific VPC. Route tables within a VPC are not propagated over Direct Connect virtual interfaces (VIFs) or Transit Gateways (TGW).
* **The Solution if On-Premises Access is Required:**
  - Use **AWS PrivateLink (Interface Endpoint for S3)**. 
  - Interface Endpoints create ENIs with private IP addresses (e.g., `10.0.11.45`) in your private subnets. Because they have standard private IP addresses within the VPC CIDR block, on-premises systems can route traffic directly to them across Direct Connect or VPN tunnels using private DNS.

---

### Question 4: How do you enforce Zero-Trust security and prevent data exfiltration when using VPC Endpoints?

#### The SRE / Architect Answer:
* By default, a VPC Endpoint allows full access (`"Action": "*", "Resource": "*"`) to any S3 bucket or DynamoDB table across any AWS account. This creates a severe **data exfiltration vulnerability** (a compromised insider or malicious process in your VPC could copy sensitive proprietary data to an external, attacker-controlled S3 bucket!).
* **Zero-Trust Mitigation (VPC Endpoint Policies):**
  - Attach an **Endpoint Policy** to the `aws_vpc_endpoint` that restricts requests strictly to company-owned resources and principal accounts:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowOnlyCompanyBuckets",
      "Effect": "Allow",
      "Principal": "*",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::company-production-data",
        "arn:aws:s3:::company-production-data/*"
      ],
      "Condition": {
        "StringEquals": {
          "aws:PrincipalAccount": "123456789012"
        }
      }
    }
  ]
}
```
* Even if an attacker has stolen valid IAM credentials for an external bucket, the VPC endpoint will block any request destined outside the authorized bucket allowlist.

---

### Question 5: When allocating CIDR blocks in AWS subnets (e.g., `/24`), why do you get 251 usable IPs instead of 256? What are the reserved IP addresses?

#### The SRE / Architect Answer:
* In any IPv4 subnet in an AWS VPC, **AWS always reserves 5 IP addresses**:
  1. `10.0.1.0`: **Network Address** (the CIDR base address).
  2. `10.0.1.1`: **VPC Router** (internal default gateway for the subnet).
  3. `10.0.1.2`: **DNS Resolver** (`AmazonProvidedDNS` / Route 53 Resolver).
  4. `10.0.1.3`: **Future Use** (reserved by AWS for protocol expansion).
  5. `10.0.1.255`: **Network Broadcast Address** (AWS VPC networks do not support standard broadcast, but this address is still reserved).
* For a `/24` subnet: $2^{(32 - 24)} = 256$ total addresses $- 5 \text{ reserved} = \mathbf{251}$ usable private IPs.

---

### Question 6: What is the primary FinOps hazard when enabling VPC Flow Logs with CloudWatch Logs? How do you remediate it?

#### The SRE / Architect Answer:
* **The Hazard:** By default, AWS CloudWatch Log Groups have a retention policy of **"Never Expire"**. In a high-traffic production VPC with multiple microservices and databases, VPC Flow Logs generate gigabytes of log lines daily. Over 1–2 years, retaining raw flow logs indefinitely creates a massive, continuously compounding CloudWatch storage bill ($0.03 per GB/month).
* **The Remediation:**
  1. **Hot Ingestion Capping:** Always set `retention_in_days` (e.g., 7 or 14 days) in Terraform to automatically purge transient flow logs from CloudWatch once the operational troubleshooting window has passed.
  2. **Cold Tiering to S3:** For compliance audits (e.g., PCI-DSS requiring 365 days of network traffic history), configure an AWS Flow Log subscription or direct S3 export in Apache Parquet format with an S3 Lifecycle rule transitioning logs to S3 Glacier Instant Retrieval after 30 days.

---

### Question 7: Walk through the security handshake between AWS VPC Flow Logs and CloudWatch. Why can't the Flow Log service write directly to CloudWatch without an IAM role?

#### The SRE / Architect Answer:
* Under the AWS Shared Responsibility Model and Zero-Trust architecture, internal AWS services are completely isolated from customer data planes. The VPC Flow Log engine runs as a hypervisor daemon on AWS Nitro physical hosts.
* **The Handshake:**
  1. The Flow Log service cannot assume customer identity without explicit permission. We define an IAM Role with a **Trust Policy** declaring `Principal = { Service = "vpc-flow-logs.amazonaws.com" }`.
  2. When the Flow Log daemon needs to write a batch of packet records, it calls AWS Security Token Service (`sts:AssumeRole`) using that specific role ARN.
  3. STS verifies the trust policy and returns short-lived, temporary session credentials to the daemon.
  4. The daemon uses these credentials to call `logs:CreateLogStream` (one per ENI) and `logs:PutLogEvents` into the customer's `/aws/vpc/xxx-flow-logs` log group.
  5. If the IAM role is deleted or misconfigured, the Flow Log engine fails closed, protecting the customer from unauthorized data injection.
