import os
os.environ["PATH"] += r";C:\Program Files\Graphviz\bin"

from diagrams import Cluster, Diagram, Edge
from diagrams.aws.network import ALB, ElbApplicationLoadBalancer
from diagrams.aws.compute import EC2
from diagrams.aws.security import Shield
from diagrams.onprem.client import User

graph_attr = {
    "fontsize": "22",
    "bgcolor": "white",
    "pad": "0.5",
    "splines": "ortho",
}

node_attr = {
    "fontsize": "11",
}

edge_attr = {
    "fontsize": "10",
}

with Diagram(
    "Project 04: Production Microservice Ingress (Internal ALB & SG Chaining)",
    show=False,
    filename="architecture_diagram",
    direction="LR",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
):
    client = User("Internal VPC Client\n(Service / Consumer)")

    with Cluster("AWS Custom VPC: 10.0.0.0/16"):

        with Cluster("Ingress Tier: Internal Load Balancer"):
            alb_sg = Shield("ALB Security Group\n[sg-alb]\n(Port 80 Ingress from VPC)")
            alb = ElbApplicationLoadBalancer("Internal ALB\n(Scheme: internal)\n(No Public IPs)")

            with Cluster("Layer 7 Listener (Port 80)"):
                rule_api = ALB("Rule: /api/v1/*\n(Priority 10: Forward)")
                rule_health = ALB("Rule: /health\n(Priority 20: Fixed 200 OK)\n[Terminated at Edge]")

        with Cluster("Zero-Trust Security Perimeter"):
            app_sg = Shield("Chained App Security Group\n[sg-app]\n(Ingress: Port 8080 ONLY from sg-alb)")

            with Cluster("Availability Zone: us-east-1a\n[Subnet 1: 10.0.11.0/24]"):
                backend_az1 = EC2("Microservice Replica 1\n(Target: 10.0.11.x:8080)\n[Health Check: 200 OK]")

            with Cluster("Availability Zone: us-east-1b\n[Subnet 2: 10.0.12.0/24]"):
                backend_az2 = EC2("Microservice Replica 2\n(Target: 10.0.12.x:8080)\n[Health Check: 200 OK]")

    # Traffic Flow
    client >> Edge(color="darkblue", label="1. HTTP Port 80") >> alb_sg
    alb_sg >> alb

    # Layer 7 Inspection
    alb >> Edge(color="forestgreen", label="Path: /health") >> rule_health
    rule_health >> Edge(color="forestgreen", style="dashed", label="Edge 200 OK") >> client

    alb >> Edge(color="purple", label="Path: /api/v1/*") >> rule_api
    rule_api >> Edge(color="purple", label="Forward") >> app_sg

    # Chained SG dispatch to Multi-AZ replicas
    app_sg >> Edge(color="purple", label="Port 8080") >> backend_az1
    app_sg >> Edge(color="purple", label="Port 8080") >> backend_az2
