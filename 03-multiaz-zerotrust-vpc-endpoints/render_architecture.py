"""Generate an editable diagrams.net (.drawio) and SVG architecture diagram for Project 03."""
from pathlib import Path
import base64
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent
W, H = 1600, 1200
INK, MUTED = '#172B45', '#52647A'
BLUE, PURPLE, GREEN, ORANGE, RED = '#2463AA', '#7653B6', '#16846C', '#D97706', '#DC2626'
SVG_NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', SVG_NS)

class Canvas:
    def __init__(self):
        self.svg = ET.Element(f'{{{SVG_NS}}}svg', width=str(W), height=str(H), viewBox=f'0 0 {W} {H}')
        ET.SubElement(self.svg, 'title').text = 'Project 03: Multi-AZ Zero-Trust VPC with Gateway Endpoints & Observability'
        defs = ET.SubElement(self.svg, 'defs')
        for color in [BLUE, PURPLE, GREEN, ORANGE, RED]:
            marker = ET.SubElement(defs, 'marker', id='arrow'+color[1:], viewBox='0 0 10 10', refX='9', refY='5', markerWidth='8', markerHeight='8', orient='auto-start-reverse')
            ET.SubElement(marker, 'path', d='M 0 0 L 10 5 L 0 10 z', fill=color)

        self.mx = ET.Element('mxfile', host='app.diagrams.net', type='device')
        diagram = ET.SubElement(self.mx, 'diagram', name='Architecture', id='project-03')
        model = ET.SubElement(diagram, 'mxGraphModel', dx=str(W), dy=str(H), grid='1', gridSize='10', guides='1', tooltips='1', connect='1', arrows='1', fold='1', page='1', pageScale='1', pageWidth=str(W), pageHeight=str(H), math='0', shadow='0')
        self.root = ET.SubElement(model, 'root')
        ET.SubElement(self.root, 'mxCell', id='0')
        ET.SubElement(self.root, 'mxCell', id='1', parent='0')
        self.n = 1
        self.rect(0, 0, W, H, '#FFFFFF', 'none', radius=0)

    def cell(self, style, x, y, w, h, value=''):
        self.n += 1
        c = ET.SubElement(self.root, 'mxCell', id=str(self.n), value=value, style=style, vertex='1', parent='1')
        ET.SubElement(c, 'mxGeometry', x=str(x), y=str(y), width=str(w), height=str(h), **{'as':'geometry'})
        return c

    def rect(self, x, y, w, h, fill='#FFFFFF', stroke='#CBD5E1', radius=12, dash=False, width=1.5):
        a = dict(x=str(x), y=str(y), width=str(w), height=str(h), rx=str(radius), fill=fill, stroke=stroke, **{'stroke-width':str(width)})
        if dash: a['stroke-dasharray']='7 5'
        ET.SubElement(self.svg, 'rect', a)
        self.cell(f'rounded={int(radius>0)};arcSize=8;whiteSpace=wrap;html=0;fillColor={fill};strokeColor={stroke};strokeWidth={width};dashed={int(dash)};', x, y, w, h)

    def text(self, x, y, value, size=18, color=INK, bold=False, w=600, align='left'):
        tx = x if align=='left' else x+w/2
        el = ET.SubElement(self.svg, 'text', x=str(tx), y=str(y+size), fill=color, **{'font-family':'DejaVu Sans, Arial, sans-serif','font-size':str(size),'font-weight':'700' if bold else '400','text-anchor':'start' if align=='left' else 'middle'})
        el.text = value
        self.cell(f'text;html=0;strokeColor=none;fillColor=none;align={align};verticalAlign=top;whiteSpace=wrap;rounded=0;fontFamily=Arial;fontSize={size};fontColor={color};fontStyle={1 if bold else 0};spacing=0;', x, y, w, size*1.4, value)

    def icon(self, name, x, y, size):
        data = base64.b64encode((BASE/'assets'/f'{name}.png').read_bytes()).decode()
        ET.SubElement(self.svg, 'image', x=str(x), y=str(y), width=str(size), height=str(size), href='data:image/png;base64,'+data)
        self.cell('shape=image;verticalLabelPosition=bottom;verticalAlign=top;imageAspect=1;aspect=fixed;image=data:image/png,'+data+';', x, y, size, size)

    def line(self, points, color=BLUE, dash=False, arrow=True, width=2.5):
        a = {'points':' '.join(f'{x},{y}' for x,y in points), 'fill':'none', 'stroke':color, 'stroke-width':str(width), 'stroke-linejoin':'round'}
        if dash: a['stroke-dasharray']='7 5'
        if arrow: a['marker-end']='url(#arrow'+color[1:]+')'
        ET.SubElement(self.svg, 'polyline', a)
        self.n += 1
        c = ET.SubElement(self.root, 'mxCell', id=str(self.n), style=f'edgeStyle=none;rounded=0;html=0;strokeColor={color};strokeWidth={width};dashed={int(dash)};endArrow={"block" if arrow else "none"};endFill=1;', edge='1', parent='1')
        g = ET.SubElement(c, 'mxGeometry', relative='1', **{'as':'geometry'})
        ET.SubElement(g, 'mxPoint', x=str(points[0][0]), y=str(points[0][1]), **{'as':'sourcePoint'})
        ET.SubElement(g, 'mxPoint', x=str(points[-1][0]), y=str(points[-1][1]), **{'as':'targetPoint'})
        arr = ET.SubElement(g, 'Array', **{'as':'points'})
        for x,y in points[1:-1]: ET.SubElement(arr, 'mxPoint', x=str(x), y=str(y))

    def save(self, stem):
        svg = BASE / f'{stem}.svg'
        ET.indent(self.svg)
        ET.ElementTree(self.svg).write(svg, encoding='utf-8', xml_declaration=True)
        ET.indent(self.mx)
        ET.ElementTree(self.mx).write(BASE / f'{stem}.drawio', encoding='utf-8', xml_declaration=True)
        print(f'Created {stem}.svg and {stem}.drawio')

def render():
    c = Canvas()
    c.text(48, 27, 'Project 03 · Multi-AZ Zero-Trust VPC with Gateway Endpoints & Observability', 34, bold=True, w=1480)
    c.text(48, 78, 'Multi-AZ Subnets  /  VPC Gateway Endpoints ($0 NAT Tax)  /  S3 Zero-Trust Policy  /  VPC Flow Logs', 19, MUTED, w=1490)
    c.rect(48, 119, 70, 5, ORANGE, 'none', 0)

    # AWS Cloud Region Box
    c.rect(40, 150, 1520, 850, '#FFFFFF', '#8795A8', 14)
    c.text(66, 168, 'AWS CLOUD', 16, bold=True, w=160)
    c.text(238, 168, 'Region: us-east-1', 16, MUTED, w=400)
    c.text(1110, 168, 'ZERO-TRUST NETWORK TOPOLOGY', 14, MUTED, bold=True, w=420)

    # Custom VPC Box
    c.rect(66, 210, 1020, 765, '#FAFCFF', '#6B9B81', 10)
    c.text(90, 226, 'CUSTOM VPC: 10.0.0.0/16', 18, '#32684B', True, w=600)
    c.text(800, 228, 'Dynamic cidrsubnet() Allocation', 15, MUTED, w=270)

    # Public Tier
    c.rect(90, 265, 970, 155, '#F8FAFC', '#CBD5E1', 8)
    c.text(110, 275, 'Tier 1: Public Subnets (Attached to Internet Gateway 0.0.0.0/0)', 16, bold=True, w=600)
    
    # Public Subnet 1
    c.rect(110, 305, 450, 95, '#FFFFFF', '#94A3B8', 6)
    c.text(125, 317, 'Public Subnet 1 (us-east-1a)', 16, BLUE, True, w=400)
    c.text(125, 345, 'CIDR: 10.0.1.0/24  •  map_public_ip_on_launch = true', 14, MUTED, w=420)
    c.text(125, 370, 'Route: 0.0.0.0/0 -> igw-xxxx (Internet Gateway)', 13, BLUE, w=420)

    # Public Subnet 2
    c.rect(590, 305, 450, 95, '#FFFFFF', '#94A3B8', 6)
    c.text(605, 317, 'Public Subnet 2 (us-east-1b)', 16, BLUE, True, w=400)
    c.text(605, 345, 'CIDR: 10.0.2.0/24  •  map_public_ip_on_launch = true', 14, MUTED, w=420)
    c.text(605, 370, 'Route: 0.0.0.0/0 -> igw-xxxx (Internet Gateway)', 13, BLUE, w=420)

    # Private Tier (Isolated - Zero Route to IGW)
    c.rect(90, 445, 970, 250, '#EFF7EF', '#A7C6A9', 8)
    c.text(110, 458, 'Tier 2: Private Isolated Subnets (ZERO Route to Internet Gateway)', 16, '#246324', True, w=650)
    
    # Private Subnet 1
    c.rect(110, 490, 450, 185, '#FFFFFF', '#86EFAC', 6)
    c.icon('ec2', 130, 510, 48)
    c.text(190, 508, 'Private Workload 1', 18, bold=True, w=350)
    c.text(190, 536, 'us-east-1a  •  10.0.11.0/24', 14, MUTED, w=350)
    c.rect(125, 575, 420, 85, '#F8FAFC', '#CBD5E1', 6)
    c.text(138, 585, 'Private Route Table Association:', 13, INK, True, w=390)
    c.text(138, 608, '• Prefix List (pl-s3) -> S3 Gateway Endpoint', 13, PURPLE, True, w=390)
    c.text(138, 630, '• Prefix List (pl-ddb) -> DynamoDB Gateway Endpoint', 13, GREEN, True, w=390)

    # Private Subnet 2
    c.rect(590, 490, 450, 185, '#FFFFFF', '#86EFAC', 6)
    c.icon('ec2', 610, 510, 48)
    c.text(670, 508, 'Private Workload 2', 18, bold=True, w=350)
    c.text(670, 536, 'us-east-1b  •  10.0.12.0/24', 14, MUTED, w=350)
    c.rect(605, 575, 420, 85, '#F8FAFC', '#CBD5E1', 6)
    c.text(618, 585, 'Private Route Table Association:', 13, INK, True, w=390)
    c.text(618, 608, '• Prefix List (pl-s3) -> S3 Gateway Endpoint', 13, PURPLE, True, w=390)
    c.text(618, 630, '• Prefix List (pl-ddb) -> DynamoDB Gateway Endpoint', 13, GREEN, True, w=390)

    # Observability Tier inside VPC (VPC Flow Logs Sensor)
    c.rect(90, 715, 970, 240, '#F5F3FF', '#C4B5FD', 8)
    c.text(110, 728, 'Tier 3: Observability as Code (VPC Flow Logs Telemetry)', 16, PURPLE, True, w=650)
    c.text(110, 760, 'Hardware sensor captures every IP packet: srcAddr -> dstAddr:port [action: ACCEPT/REJECT]', 14, MUTED, w=900)
    
    c.rect(110, 795, 450, 140, '#FFFFFF', '#DDD6FE', 6)
    c.text(125, 808, 'IAM AssumeRole Trust Handshake', 16, PURPLE, True, w=400)
    c.text(125, 836, 'Role: zerotrust-network-flow_log_role', 14, MUTED, w=400)
    c.text(125, 862, 'Principal: Service = "vpc-flow-logs.amazonaws.com"', 13, '#4C1D95', True, w=400)
    c.text(125, 888, 'Permissions: logs:CreateLogStream, logs:PutLogEvents', 13, INK, w=400)

    c.rect(590, 795, 450, 140, '#FFFFFF', '#DDD6FE', 6)
    c.icon('cloudwatch', 610, 815, 48)
    c.text(670, 812, 'CloudWatch Log Group', 18, bold=True, w=350)
    c.text(670, 838, 'name: /aws/vpc/zerotrust-network-flow-logs', 13, MUTED, w=350)
    c.rect(605, 875, 420, 45, '#FEF2F2', '#FECACA', 6)
    c.text(618, 885, 'FinOps Retention Capping: 7 Days (Purges old logs)', 13, RED, True, w=390)

    # Right Column: AWS Backbone Services & Gateway Endpoints ($0.00 NAT Bypass)
    # S3 Gateway Endpoint Card
    c.rect(1120, 240, 410, 230, '#FDF4FF', '#E879F9')
    c.icon('s3', 1140, 260, 52)
    c.text(1205, 258, 'Amazon S3 Gateway Endpoint', 20, PURPLE, True, w=310)
    c.text(1205, 288, 'vpce-s3 (Prefix List: pl-s3)', 14, MUTED, w=310)
    c.rect(1135, 330, 380, 50, '#FFFFFF', '#F0ABFC', 6)
    c.text(1148, 338, 'FinOps: $0.00/hr, $0.00/GB Data Transfer', 14, GREEN, True, w=350)
    c.text(1148, 358, 'Bypasses NAT Gateway ($0.045/GB saved!)', 13, MUTED, w=350)
    c.rect(1135, 390, 380, 65, '#FEF2F2', '#FECACA', 6)
    c.text(1148, 398, 'Zero-Trust Endpoint Policy Attached:', 14, RED, True, w=350)
    c.text(1148, 418, 'Allow strictly: arn:aws:s3:::zerotrust-network-*', 13, INK, True, w=350)

    # DynamoDB Gateway Endpoint Card
    c.rect(1120, 490, 410, 200, '#EFF6FF', '#60A5FA')
    c.icon('dynamodb', 1140, 510, 52)
    c.text(1205, 508, 'DynamoDB Gateway Endpoint', 20, BLUE, True, w=310)
    c.text(1205, 538, 'vpce-dynamodb (Prefix List: pl-ddb)', 14, MUTED, w=310)
    c.rect(1135, 580, 380, 50, '#FFFFFF', '#93C5FD', 6)
    c.text(1148, 588, 'FinOps: $0.00/hr, $0.00/GB Data Transfer', 14, GREEN, True, w=350)
    c.text(1148, 608, 'Internal AWS hardware backbone routing', 13, MUTED, w=350)
    c.text(1140, 648, 'Direct NoSQL access with sub-ms internal latency', 14, INK, w=370)

    # Flow lines
    # Private to Endpoints
    c.line([(560, 570), (1120, 355)], PURPLE)
    c.text(780, 435, 'Prefix List Route to S3', 14, PURPLE, True, w=220)

    c.line([(560, 630), (1120, 590)], GREEN)
    c.text(780, 605, 'Prefix List Route to DDB', 14, GREEN, True, w=220)

    # Telemetry flow to CloudWatch
    c.line([(560, 865), (590, 865)], PURPLE)

    # Bottom Architectural Mastery Box
    c.rect(40, 1020, 745, 150, '#F2F7FC', '#D2DFEC', 10)
    c.text(61, 1036, 'FINOPS & ZERO-TRUST ENTERPRISE IMPACT', 16, BLUE, True, w=700)
    c.text(61, 1065, '• NAT Gateway Elimination: 20 TB monthly S3 transfer through NAT costs $965/mo. Gateway Endpoint = $0.00!', 15, w=700)
    c.text(61, 1092, '• Exfiltration Defense: Default endpoints allow traffic to ANY external S3 bucket. Our policy blocks all foreign buckets.', 15, w=700)
    c.text(61, 1120, '• Longest Prefix Match (LPM): Nitro hypervisor matches pl-s3 automatically without modifying instance code.', 15, MUTED, w=700)

    c.rect(805, 1020, 755, 150, '#FFFAF0', '#EAD7AC', 10)
    c.text(826, 1036, 'SRE NETWORK INCIDENT OBSERVABILITY', 16, ORANGE, True, w=710)
    c.text(826, 1065, '• REJECT Packet Detection: VPC Flow Logs capture dropped firewall packets without installing server agents.', 15, w=710)
    c.text(826, 1092, '• Retention Discipline: CloudWatch Log Group capped at 7 days to eliminate $0.03/GB compounding storage debt.', 15, w=710)
    c.text(826, 1120, '• STS Security Handshake: VPC Flow Log daemon assumes customer role strictly to write to defined log stream.', 15, MUTED, w=710)

    c.save('project-03-architecture')

if __name__ == '__main__':
    render()
