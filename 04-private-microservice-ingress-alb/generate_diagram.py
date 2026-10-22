import os
os.environ["PATH"] += r";C:\Program Files\Graphviz\bin"

from diagrams import Cluster, Diagram, Edge
from diagrams.aws.network import VPC, ALB, RouteTable
from diagrams.aws.compute import EC2
from diagrams.aws.security import Shield
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
    "Project 04: Private Microservice Ingress with Internal ALB & Security Group Chaining",
    show=False,
    filename="architecture_diagram",
    direction="TB",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
):
    internal_client = User("VPC Consumer / App\n(Port 80 HTTP)")

    with Cluster("AWS Custom VPC (10.0.0.0/16)"):

        with Cluster("Tier 1: Load Balancing Ingress (Internal)"):
            alb_sg = Shield("ALB Security Group\n(Port 80 Ingress from VPC)")
            alb = ALB("Internal ALB\n(Scheme: internal)\n(No Public IPs)")

        with Cluster("Multi-AZ Private Subnet Placement"):
            with Cluster("Availability Zone: us-east-1a"):
                sn_1 = RouteTable("Private Subnet 1\n(10.0.11.0/24)")
            with Cluster("Availability Zone: us-east-1b"):
                sn_2 = RouteTable("Private Subnet 2\n(10.0.12.0/24)")

        with Cluster("Layer 7 Routing Engine (aws_lb_listener)"):
            rule_health = ALB("Rule: /health (Priority 20)\n[Fixed Response 200 OK]\n(Answered at Edge)")
            rule_api = ALB("Rule: /api/v1/* (Priority 10)\n[Action: Forward]")

        with Cluster("Tier 2: Private Backend Compute (Zero-Trust Chaining)"):
            app_sg = Shield("Microservice SG\n(Port 8080 Ingress ONLY from alb_sg!)")
            with Cluster("Target Group: private-microservice-tg"):
                pod_1 = EC2("Microservice Node 1\n(Port 8080 / Health: 200)")
                pod_2 = EC2("Microservice Node 2\n(Port 8080 / Health: 200)")

    # Client to ALB
    internal_client >> Edge(color="blue", label="HTTP GET /api/v1/*\nor GET /health") >> alb_sg
    alb_sg >> alb

    # ALB deployed across multi-AZ subnets
    alb >> Edge(color="gray", style="dotted") >> sn_1
    alb >> Edge(color="gray", style="dotted") >> sn_2

    # Layer 7 routing logic
    alb >> Edge(color="darkgreen", label="Path = /health") >> rule_health
    rule_health >> Edge(color="darkgreen", label="Instant 200 OK 'HEALTHY-ALB-EDGE'") >> internal_client

    alb >> Edge(color="purple", label="Path = /api/v1/*") >> rule_api
    rule_api >> Edge(color="purple", label="Forward") >> app_sg

    # Security Group Chained ingress to backend pods
    app_sg >> Edge(color="purple") >> pod_1
    app_sg >> Edge(color="purple") >> pod_2
