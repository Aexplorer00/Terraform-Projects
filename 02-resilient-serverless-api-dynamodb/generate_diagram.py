import os
os.environ["PATH"] += r";C:\Program Files\Graphviz\bin"

from diagrams import Cluster, Diagram, Edge
from diagrams.aws.network import APIGateway
from diagrams.aws.compute import Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.security import KMS
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
    "Project 02: Resilient Serverless Transaction Engine (API Gateway -> Lambda -> DynamoDB)",
    show=False,
    filename="architecture_diagram",
    direction="LR",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
):
    client = User("API Client / Consumer\n(POST /transactions)")

    with Cluster("1. Edge Ingress Tier"):
        api = APIGateway("API Gateway (REST)\n(Request Validation\n+ Proxy Integration)")

    with Cluster("2. Serverless Compute Tier"):
        fn = Lambda("Order Processing Lambda\n(Idempotent PutItem\n+ Connection Reuse)")

    with Cluster("3. Persistent NoSQL Tier"):
        db = Dynamodb("DynamoDB Table\n(PK: transaction_id)\n(GSI: customer_id-index)\n(TTL: 90 Days Auto-Purge)")

    with Cluster("4. Security & Cryptography"):
        kms = KMS("KMS CMK\n(Envelope Encryption\n+ Key Auto-Rotation)")

    # Encryption links
    kms >> Edge(color="darkorange", style="dotted", label="SSE-KMS Encryption") >> db

    # Request pipeline
    client >> Edge(color="forestgreen", label="1. HTTPS POST /transactions") >> api
    api >> Edge(color="darkblue", label="2. Lambda Proxy Event") >> fn
    fn >> Edge(color="purple", label="3. Conditional PutItem\nattribute_not_exists") >> db
