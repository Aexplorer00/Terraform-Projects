import os
os.environ["PATH"] += r";C:\Program Files\Graphviz\bin"

from diagrams import Cluster, Diagram, Edge
from diagrams.aws.security import KMS
from diagrams.aws.storage import S3
from diagrams.aws.integration import SQS
from diagrams.onprem.client import User

graph_attr = {
    "fontsize": "20",
    "bgcolor": "white",
    "pad": "0.5",
    "splines": "spline",
}

node_attr = {
    "fontsize": "12",
}

edge_attr = {
    "fontsize": "11",
}

with Diagram(
    "Project 01: Resilient S3 to SQS Ingestion Pipeline with DLQ & KMS",
    show=False,
    filename="architecture_diagram",
    direction="LR",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
):
    producer = User("Client / Producer\n(Document Ingestion)")

    with Cluster("1. Security & Key Management"):
        kms = KMS("KMS CMK\n(Envelope Encryption\n+ Key Auto-Rotation)")

    with Cluster("2. Storage Layer"):
        s3 = S3("S3 Ingestion Vault\n(Versioning + SSE-KMS)")

    with Cluster("3. Resilient Messaging Tier"):
        sqs_primary = SQS("Primary SQS Queue\n(Visibility Timeout: 30s)")
        sqs_dlq = SQS("Dead-Letter Queue (DLQ)\n(14-Day Forensic Retention)")

        sqs_primary >> Edge(color="crimson", style="dashed", label="Poison Pill / maxReceiveCount > 3") >> sqs_dlq

    # Ingestion flow
    producer >> Edge(color="forestgreen", label="1. PutObject (invoice.pdf)") >> s3
    s3 >> Edge(color="darkblue", label="2. s3:ObjectCreated:*\n(via SQS Queue Policy)") >> sqs_primary

    # Encryption linkages
    kms >> Edge(color="darkorange", style="dotted", label="SSE-KMS") >> s3
    kms >> Edge(color="darkorange", style="dotted", label="KmsMasterKeyId") >> sqs_primary
