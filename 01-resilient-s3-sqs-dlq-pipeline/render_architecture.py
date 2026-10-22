"""Generate an editable diagrams.net (.drawio) and SVG architecture diagram for Project 01."""
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
        ET.SubElement(self.svg, 'title').text = 'Project 01: Resilient S3-SQS-DLQ Pipeline'
        defs = ET.SubElement(self.svg, 'defs')
        for color in [BLUE, PURPLE, GREEN, ORANGE, RED]:
            marker = ET.SubElement(defs, 'marker', id='arrow'+color[1:], viewBox='0 0 10 10', refX='9', refY='5', markerWidth='8', markerHeight='8', orient='auto-start-reverse')
            ET.SubElement(marker, 'path', d='M 0 0 L 10 5 L 0 10 z', fill=color)

        self.mx = ET.Element('mxfile', host='app.diagrams.net', type='device')
        diagram = ET.SubElement(self.mx, 'diagram', name='Architecture', id='project-01')
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
    c.text(48, 27, 'Project 01 · Resilient S3-SQS-DLQ Ingestion Pipeline', 34, bold=True, w=1480)
    c.text(48, 78, 'Event-Driven Storage  /  SSE-KMS CMK  /  Confused Deputy Defense  /  Poison Pill Isolation', 19, MUTED, w=1490)
    c.rect(48, 119, 70, 5, ORANGE, 'none', 0)

    # AWS Cloud Region Box
    c.rect(40, 150, 1520, 810, '#FFFFFF', '#8795A8', 14)
    c.text(66, 168, 'AWS CLOUD', 16, bold=True, w=160)
    c.text(238, 168, 'Region: us-east-1', 16, MUTED, w=400)
    c.text(1110, 168, 'EVENT-DRIVEN INGESTION FLOW', 14, MUTED, bold=True, w=420)

    # 1. Producer / Client
    c.rect(70, 270, 210, 160, '#FFFFFF', '#B5C4D6')
    c.icon('user', 90, 290, 50)
    c.text(150, 292, 'Client Producer', 20, bold=True, w=120)
    c.text(85, 360, 'External Ingestion Source', 15, MUTED, w=180)
    c.text(85, 388, 'PUT raw payload objects', 14, MUTED, w=180)

    # 2. S3 Storage Tier
    c.rect(360, 240, 310, 220, '#F2F8FD', '#8ABAE2')
    c.icon('s3', 380, 260, 55)
    c.text(450, 258, 'Amazon S3', 22, bold=True, w=200)
    c.text(450, 292, 'resilient-ingestion-bucket', 15, MUTED, w=210)
    c.rect(375, 335, 280, 40, '#FFFFFF', '#B8D5E5', 6)
    c.text(388, 345, 'Event: s3:ObjectCreated:*', 15, BLUE, True, w=250)
    c.rect(375, 385, 280, 55, '#EDF6ED', '#A4D1A4', 6)
    c.text(388, 393, 'SSE-KMS: Customer Managed Key', 14, '#246324', True, w=250)
    c.text(388, 413, 'Key rotation enabled (365d)', 13, MUTED, w=250)

    # 3. KMS Security Policy Tier
    c.rect(360, 500, 310, 160, '#FFFBF0', '#E5CE8E')
    c.icon('kms', 380, 520, 50)
    c.text(445, 518, 'KMS CMK', 21, bold=True, w=210)
    c.text(445, 550, 'kms-s3-sqs-key', 15, MUTED, w=210)
    c.text(380, 585, 'Envelope encryption for S3 & SQS', 14, MUTED, w=270)
    c.text(380, 610, 'Strict Service Principal Key Policy', 14, ORANGE, True, w=270)

    # Encryption links (dotted)
    c.line([(515, 500), (515, 460)], ORANGE, dash=True, arrow=False)
    c.line([(670, 580), (750, 580), (750, 440), (770, 440)], ORANGE, dash=True, arrow=False)

    # 4. Primary SQS Ingestion Queue
    c.rect(770, 240, 360, 220, '#F5F3FF', '#C4B5FD')
    c.icon('sqs', 790, 260, 55)
    c.text(860, 258, 'Primary Ingestion Queue', 22, PURPLE, True, w=260)
    c.text(860, 292, 'resilient-ingestion-queue', 15, MUTED, w=260)
    c.rect(785, 335, 330, 45, '#FFFFFF', '#DDD6FE', 6)
    c.text(798, 347, 'Confused Deputy: aws:SourceArn', 14, PURPLE, True, w=300)
    c.rect(785, 390, 330, 55, '#FFF8EF', '#FCD34D', 6)
    c.text(798, 398, 'Redrive Policy Attached:', 14, ORANGE, True, w=300)
    c.text(798, 418, 'maxReceiveCount = 3 failures', 14, INK, False, w=300)

    # 5. SQS Dead Letter Queue (DLQ)
    c.rect(770, 520, 360, 180, '#FEF2F2', '#FCA5A5')
    c.icon('sqs', 790, 540, 55)
    c.text(860, 538, 'Dead Letter Queue (DLQ)', 21, RED, True, w=260)
    c.text(860, 570, 'resilient-ingestion-dlq', 15, MUTED, w=260)
    c.text(790, 615, '• Poison Pill Isolation: isolates corrupt data', 14, INK, w=320)
    c.text(790, 640, '• 14-Day Extended Message Retention', 14, INK, w=320)
    c.text(790, 665, '• CloudWatch Alarm on Visible Messages', 14, RED, True, w=320)

    # 6. Consumer / Worker Fleet
    c.rect(1220, 270, 280, 160, '#FFFFFF', '#B5C4D6')
    c.icon('worker', 1240, 290, 50)
    c.text(1305, 292, 'SRE Worker Fleet', 20, bold=True, w=180)
    c.text(1240, 360, 'Asynchronous Consumer', 16, MUTED, w=240)
    c.text(1240, 388, 'Processes validated messages', 14, GREEN, True, w=240)

    # Connections
    # 1. Client to S3
    c.line([(280, 350), (360, 350)], BLUE)
    c.text(285, 325, 'PUT S3 Object', 14, BLUE, w=80)

    # 2. S3 Notification to SQS
    c.line([(670, 350), (770, 350)], PURPLE)
    c.text(675, 325, 's3:ObjectCreated', 14, PURPLE, w=90)

    # 3. Queue to Worker
    c.line([(1130, 350), (1220, 350)], GREEN)
    c.text(1135, 325, 'Pull & Process', 14, GREEN, w=85)

    # 4. Redrive Failure to DLQ
    c.line([(950, 460), (950, 520)], RED)
    c.text(960, 480, '3 Consecutive Failures', 14, RED, True, w=200)

    # Documentation and Interview Reference Notes
    c.rect(40, 980, 745, 130, '#F2F7FC', '#D2DFEC', 10)
    c.text(61, 996, 'ZERO-TRUST ARCHITECTURAL GUARDRAILS', 16, BLUE, True, w=700)
    c.text(61, 1025, '• Confused Deputy Defense: SQS policy restricts aws:SourceArn to bucket ARN.', 15, w=700)
    c.text(61, 1052, '• Envelope Encryption: KMS CMK encrypts payload data at rest in S3 and SQS.', 15, w=700)
    c.text(61, 1079, '• Automated Redrive: Corrupted payloads isolated to prevent consumer crashes.', 15, MUTED, w=700)

    c.rect(805, 980, 755, 130, '#FFFAF0', '#EAD7AC', 10)
    c.text(826, 996, 'SRE INCIDENT RESPONSE PLAYBOOK', 16, ORANGE, True, w=710)
    c.text(826, 1025, '• Poison Pill Alert: CloudWatch Alarm fires when DLQ ApproximateNumberOfMessages > 0.', 15, w=710)
    c.text(826, 1052, '• Inspection & Debug: SRE inspects DLQ message payload to identify schema errors.', 15, w=710)
    c.text(826, 1079, '• Redrive to Source: SQS StartMessageMoveTask replays healed messages to primary queue.', 15, MUTED, w=710)

    c.save('project-01-architecture')

if __name__ == '__main__':
    render()
