"""Generate an editable diagrams.net (.drawio) and SVG architecture diagram for Project 02."""
from pathlib import Path
import base64
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent
W, H = 1600, 1150
INK, MUTED = '#172B45', '#52647A'
BLUE, PURPLE, GREEN, ORANGE, RED = '#2463AA', '#7653B6', '#16846C', '#D97706', '#DC2626'
SVG_NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', SVG_NS)

class Canvas:
    def __init__(self):
        self.svg = ET.Element(f'{{{SVG_NS}}}svg', width=str(W), height=str(H), viewBox=f'0 0 {W} {H}')
        ET.SubElement(self.svg, 'title').text = 'Project 02: Resilient Serverless Transaction Engine'
        defs = ET.SubElement(self.svg, 'defs')
        for color in [BLUE, PURPLE, GREEN, ORANGE, RED]:
            marker = ET.SubElement(defs, 'marker', id='arrow'+color[1:], viewBox='0 0 10 10', refX='9', refY='5', markerWidth='8', markerHeight='8', orient='auto-start-reverse')
            ET.SubElement(marker, 'path', d='M 0 0 L 10 5 L 0 10 z', fill=color)

        self.mx = ET.Element('mxfile', host='app.diagrams.net', type='device')
        diagram = ET.SubElement(self.mx, 'diagram', name='Architecture', id='project-02')
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
    c.text(48, 27, 'Project 02 · Resilient Serverless Transaction Engine', 34, bold=True, w=1480)
    c.text(48, 78, 'API Gateway (REST)  /  Lambda Proxy (Python 3.11)  /  Idempotent PutItem  /  DynamoDB GSI & TTL', 19, MUTED, w=1490)
    c.rect(48, 119, 70, 5, ORANGE, 'none', 0)

    # AWS Cloud Region Box
    c.rect(40, 150, 1520, 810, '#FFFFFF', '#8795A8', 14)
    c.text(66, 168, 'AWS CLOUD', 16, bold=True, w=160)
    c.text(238, 168, 'Region: us-east-1', 16, MUTED, w=400)
    c.text(1110, 168, 'SYNCHRONOUS SERVERLESS PIPELINE', 14, MUTED, bold=True, w=420)

    # 1. API Client
    c.rect(70, 270, 210, 160, '#FFFFFF', '#B5C4D6')
    c.icon('user', 90, 290, 50)
    c.text(150, 292, 'API Client', 20, bold=True, w=120)
    c.text(85, 360, 'E-Commerce Consumer', 15, MUTED, w=180)
    c.text(85, 388, 'POST /prod/transactions', 14, BLUE, True, w=180)

    # 2. Edge Ingress: API Gateway
    c.rect(340, 240, 310, 220, '#FDF2F8', '#F472B6')
    c.icon('apigateway', 360, 260, 55)
    c.text(430, 258, 'API Gateway', 22, bold=True, w=200)
    c.text(430, 292, 'REST API: serverless-api', 15, MUTED, w=210)
    c.rect(355, 335, 280, 40, '#FFFFFF', '#FBCFE8', 6)
    c.text(368, 345, 'Validation: Request Body Validator', 14, '#9D174D', True, w=250)
    c.rect(355, 385, 280, 55, '#F5F3FF', '#DDD6FE', 6)
    c.text(368, 393, 'Integration: AWS_PROXY', 14, PURPLE, True, w=250)
    c.text(368, 413, 'Pass-through JSON context', 13, MUTED, w=250)

    # 3. Serverless Compute: Lambda
    c.rect(710, 240, 340, 220, '#FFF7ED', '#FB923C')
    c.icon('lambda', 730, 260, 55)
    c.text(800, 258, 'Transaction Lambda', 21, ORANGE, True, w=240)
    c.text(800, 292, 'Runtime: Python 3.11', 15, MUTED, w=240)
    c.rect(725, 335, 310, 45, '#FFFFFF', '#FED7AA', 6)
    c.text(738, 347, 'Idempotent: attribute_not_exists', 14, RED, True, w=280)
    c.rect(725, 390, 310, 55, '#EDF6ED', '#A4D1A4', 6)
    c.text(738, 398, 'Connection Reuse: boto3 resource', 14, '#246324', True, w=280)
    c.text(738, 418, 'Global client initialization', 13, MUTED, w=280)

    # 4. Persistent NoSQL: DynamoDB
    c.rect(1110, 240, 420, 240, '#EFF6FF', '#60A5FA')
    c.icon('dynamodb', 1130, 260, 55)
    c.text(1200, 258, 'Amazon DynamoDB', 22, BLUE, True, w=300)
    c.text(1200, 292, 'Table: transactions', 15, MUTED, w=300)
    c.rect(1125, 330, 390, 40, '#FFFFFF', '#BFDBFE', 6)
    c.text(1138, 340, 'Primary Key: transaction_id (String)', 14, INK, True, w=360)
    c.rect(1125, 375, 390, 45, '#F5F3FF', '#DDD6FE', 6)
    c.text(1138, 385, 'GSI: customer_id-index (customer_id)', 14, PURPLE, True, w=360)
    c.rect(1125, 425, 390, 45, '#FEF2F2', '#FECACA', 6)
    c.text(1138, 435, 'TTL: expires_at (90-Day Auto-Purge)', 14, RED, True, w=360)

    # 5. Security & Cryptography: KMS CMK
    c.rect(1110, 520, 420, 160, '#FFFBF0', '#E5CE8E')
    c.icon('kms', 1130, 540, 50)
    c.text(1195, 538, 'KMS Customer Managed Key', 21, bold=True, w=320)
    c.text(1195, 570, 'Server-Side Encryption (SSE-KMS)', 15, MUTED, w=320)
    c.text(1130, 605, '• Envelope encryption protecting financial data', 14, MUTED, w=380)
    c.text(1130, 630, '• Annual automatic key rotation enabled', 14, ORANGE, True, w=380)

    # Encryption Link (dotted)
    c.line([(1320, 520), (1320, 480)], ORANGE, dash=True, arrow=False)

    # Traffic Connections
    # 1. Client to API Gateway
    c.line([(280, 350), (340, 350)], BLUE)
    c.text(285, 325, '1. HTTPS POST', 14, BLUE, w=80)

    # 2. API Gateway to Lambda
    c.line([(650, 350), (710, 350)], PURPLE)
    c.text(655, 325, '2. Lambda Proxy', 14, PURPLE, w=85)

    # 3. Lambda to DynamoDB
    c.line([(1050, 350), (1110, 350)], GREEN)
    c.text(1055, 325, '3. PutItem', 14, GREEN, w=85)

    # Response return (dashed)
    c.line([(710, 400), (650, 400)], '#9D174D', dash=True)
    c.text(655, 410, '200 OK / 409 Conflict', 13, '#9D174D', w=120)

    c.line([(340, 400), (280, 400)], BLUE, dash=True)
    c.text(285, 410, 'JSON Response', 13, BLUE, w=80)

    # Documentation and Architectural Deep-Dive
    c.rect(40, 980, 745, 130, '#F2F7FC', '#D2DFEC', 10)
    c.text(61, 996, 'IDEMPOTENCY & FINANCIAL DATA INTEGRITY', 16, BLUE, True, w=700)
    c.text(61, 1025, '• Double-Charge Defense: ConditionalCheckFailedException prevents duplicate orders.', 15, w=700)
    c.text(61, 1052, '• Client Retries Safe: Network drops cause client retries; DynamoDB rejects duplicates with HTTP 409.', 15, w=700)
    c.text(61, 1079, '• TTL Data Lifecycle: Ephemeral transaction state auto-purged after 90 days at zero write cost.', 15, MUTED, w=700)

    c.rect(805, 980, 755, 130, '#FFFAF0', '#EAD7AC', 10)
    c.text(826, 996, 'SERVERLESS PERFORMANCE & SRE TUNING', 16, ORANGE, True, w=710)
    c.text(826, 1025, '• TCP Connection Reuse: Initializing boto3.resource outside handler eliminates SSL handshakes.', 15, w=710)
    c.text(826, 1052, '• DynamoDB GSI Indexing: Queries by customer_id use Sparse GSI without costly full-table scans.', 15, w=710)
    c.text(826, 1079, '• Least Privilege Execution: Lambda IAM role scoped strictly to Table and Index ARNs.', 15, MUTED, w=710)

    c.save('project-02-architecture')

if __name__ == '__main__':
    render()
