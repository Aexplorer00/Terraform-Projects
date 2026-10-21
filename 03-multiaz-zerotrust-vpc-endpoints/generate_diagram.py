import os
os.environ["PATH"] += r";C:\Program Files\Graphviz\bin"

from diagrams import Cluster, Diagram, Edge
from diagrams.aws.network import VPC, InternetGateway, RouteTable, Endpoint
from diagrams.aws.storage import S3
from diagrams.aws.database import Dynamodb
from diagrams.aws.compute import EC2
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
    "Project 03: Multi-AZ Zero-Trust VPC & Private Gateway Endpoints",
    show=False,
    filename="architecture_diagram",
    direction="TB",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
):
    internet = User("Public Traffic\n(Internet)")

    with Cluster("AWS Cloud - Region: us-east-1"):
        igw = InternetGateway("Internet Gateway\n(0.0.0.0/0 Ingress/Egress)")
        s3 = S3("Amazon S3\n(AWS Internal Backbone)")
        ddb = Dynamodb("Amazon DynamoDB\n(AWS Internal Backbone)")

        with Cluster("Custom VPC (10.0.0.0/16)"):
            with Cluster("Availability Zone: us-east-1a"):
                pub_subnet_1 = RouteTable("Public Subnet 1\n(10.0.1.0/24)")
                priv_subnet_1 = EC2("Private Workload 1\n(10.0.11.0/24)")

            with Cluster("Availability Zone: us-east-1b"):
                pub_subnet_2 = RouteTable("Public Subnet 2\n(10.0.2.0/24)")
                priv_subnet_2 = EC2("Private Workload 2\n(10.0.12.0/24)")

            with Cluster("Zero-Trust Private Routing Tier"):
                priv_rt = RouteTable("Private Route Table\n(Isolated: No 0.0.0.0/0 Route)")
                vpce_s3 = Endpoint("S3 Gateway Endpoint\n($0.00/hr, Free Data)")
                vpce_ddb = Endpoint("DynamoDB Gateway Endpoint\n($0.00/hr, Free Data)")

    # Public flow
    internet >> Edge(color="blue", label="Public Ingress") >> igw
    igw >> Edge(color="blue") >> pub_subnet_1
    igw >> Edge(color="blue") >> pub_subnet_2

    # Private workloads associate with private routing
    priv_subnet_1 >> Edge(color="darkgray", style="dashed") >> priv_rt
    priv_subnet_2 >> Edge(color="darkgray", style="dashed") >> priv_rt

    # Private routing to Gateway Endpoints
    priv_rt >> Edge(color="purple", label="Prefix List (pl-s3)") >> vpce_s3
    priv_rt >> Edge(color="purple", label="Prefix List (pl-ddb)") >> vpce_ddb

    # Gateway Endpoints route directly to AWS Services without NAT or Internet
    vpce_s3 >> Edge(color="forestgreen", label="Direct Internal Transfer") >> s3
    vpce_ddb >> Edge(color="forestgreen", label="Direct Internal Queries") >> ddb
