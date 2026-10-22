# Project 04: SRE & Cloud Architect Interview Deep-Dive Q&A

### Architecture Focus: Private Microservice Ingress with Internal ALB & Security Group Chaining

---

### Question 1: Why is opening a backend microservice's Security Group to the VPC CIDR (`10.0.0.0/16`) an architectural vulnerability? How does Security Group Chaining eliminate this risk?

#### The SRE / Architect Answer:
* **The Vulnerability (Lateral Movement):** 
  - If a backend microservice allows inbound port `8080` from `cidr_blocks = ["10.0.0.0/16"]`, **any workload in that VPC** can establish a TCP connection directly to the microservice.
  - If an attacker compromises a non-critical dev instance, a compromised CI runner, or an internet-facing bastion host within that CIDR, they can bypass the load balancer, bypass WAF rate limits, and directly exploit backend API vulnerabilities or database ports.
* **The Solution (Security Group Chaining):**
  - Instead of IP CIDRs, the microservice defines `security_groups = [aws_security_group.alb.id]`.
  - **Nitro Hypervisor Validation:** When a packet reaches the microservice ENI, AWS Nitro inspects the security group tags of the sending ENI. Even if an attacker on `10.0.11.25` (the exact same subnet) attempts to ping port `8080`, the hypervisor kernel drops the packet immediately because the source ENI does not possess the ALB security group identity.
  - This establishes an immutable Zero-Trust boundary between tiers.

---

### Question 2: Layer 4 (NLB) vs. Layer 7 (ALB) — When should an SRE choose an ALB over an NLB, and what are the trade-offs?

#### The SRE / Architect Answer:
* **Application Load Balancer (ALB - Layer 7):**
  - **Protocol Awareness:** Inspects HTTP/HTTPS headers, URLs, cookies, and query strings.
  - **Capabilities:** Path-based routing (`/api/*`), host-based routing (`api.domain.com`), HTTP $\rightarrow$ HTTPS 301 redirection, edge fixed-responses, OIDC authentication, and AWS WAF integration.
  - **Latency:** $\sim 1\text{ms} - 5\text{ms}$ (due to full Layer 7 proxying and TLS termination).
* **Network Load Balancer (NLB - Layer 4):**
  - **Protocol Awareness:** Only handles raw TCP/UDP packets. Completely blind to HTTP semantics.
  - **Capabilities:** Ultra-low ultra-consistent latency ($\sim 100\mu\text{s} - 500\mu\text{s}$), handles tens of millions of requests per second, preserves client source IP natively without `X-Forwarded-For`, and supports static Elastic IPs per AZ.
* **The SRE Verdict:** Use an **ALB** for microservice REST APIs, GraphQL, and web apps requiring intelligent routing and WAF protection. Use an **NLB** for raw TCP/UDP protocols (gaming, MQTT IoT, financial low-latency trading) or when static public IP allowlisting is mandatory.

---

### Question 3: How do you tune Target Group Health Checks to prevent "flapping" and cascading fleet failure during traffic spikes?

#### The SRE / Architect Answer:
* **The "Flapping" Antipattern:**
  - If `timeout` is too close to `interval` (e.g., timeout = 4s, interval = 5s), a temporary CPU spike on the backend causes the container to reply in 4.1s.
  - The ALB marks the container unhealthy. All traffic shifts to the surviving containers, overloading them and causing them to also time out on health checks. The entire fleet collapses in a **cascading health check death spiral**!
* **The Production Tuning Standard:**
  1. **`interval = 15s`**: Gives instances breathing room between health probes.
  2. **`timeout = 5s`**: Fast fail detection without hair-trigger sensitivity.
  3. **`healthy_threshold = 2`**: Target must succeed twice consecutively before receiving traffic (ensuring application initialization is fully complete).
  4. **`unhealthy_threshold = 3`**: Requires 3 consecutive failures ($3 \times 15\text{s} = 45\text{s}$) before eviction, absorbing temporary transient CPU spikes without evicting healthy instances.
  5. **Separate Health Check Endpoint:** The `/health` endpoint must check basic process liveness (shallow check), while a `/ready` probe checks downstream database dependencies to avoid false positive evictions.

---

### Question 4: What are the 5 Action Types supported by ALB Listener Rules? Provide a production scenario for each.

#### The SRE / Architect Answer:
1. **`forward`**: Routes requests across private subnets to a target group (e.g., routing `/api/v1/*` to our microservice fleet).
2. **`fixed-response`**: Returns static text, JSON, or HTML directly from the ALB edge in $< 1\text{ms}$ without touching backends (e.g., edge `/health` probes, or returning `503 Service Unavailable` with a branded maintenance page during migrations).
3. **`redirect`**: Instructs the client browser to reload over a different protocol or URL (e.g., Port 80 HTTP $\rightarrow$ Port 443 HTTPS 301 Permanent Redirect).
4. **`authenticate-oidc`**: Authenticates users against corporate Identity Providers (Okta, Google Workspace, Azure AD) directly at the ALB layer before forwarding requests to internal admin portals.
5. **`authenticate-cognito`**: Authenticates consumer mobile/web users against AWS Cognito user pools before routing to the application.

---

### Question 5: How does an "Internal" ALB scheme resolve and route traffic without public IP addresses?

#### The SRE / Architect Answer:
* When an ALB is created with `internal = true`, AWS Elastic Load Balancing:
  1. Requests private IPv4 addresses from the private subnets specified in the configuration (e.g., `10.0.11.45` in AZ-a, `10.0.12.89` in AZ-b).
  2. Provisions managed Elastic Network Interfaces (ENIs) with those private IPs.
  3. Publishes an internal DNS record (e.g., `private-microservice-alb-xxxx.elb.us-east-1.amazonaws.com`) to the VPC Route 53 Resolver (`10.0.0.2`).
* When an internal microservice or on-premises client queries this DNS name, Route 53 returns **only the private IPs**. The client connects over internal VPC routing or Direct Connect with zero internet gateway involvement.

---

### Question 6: Security Groups are "Stateful" while Network ACLs are "Stateless". What does this mean for ALB and microservice egress rules?

#### The SRE / Architect Answer:
* **Stateful Security Groups:**
  - If an inbound packet is allowed via an **Ingress Rule** (e.g., port 80 into the ALB), AWS Nitro tracks the TCP connection tuple in memory.
  - The return traffic (response packet from ALB to client) is **automatically permitted out**, regardless of any egress rules configured on the security group!
  - Therefore, you never need to configure reverse ephemeral port egress rules on security groups.
* **Stateless Network ACLs (NACLs):**
  - NACLs do **not** maintain connection state tables.
  - If you allow inbound port 80 on a NACL, you **must explicitly create an outbound rule** allowing the ephemeral port range (`1024-65535`) for the response packets, otherwise the response is dropped at the subnet boundary!
