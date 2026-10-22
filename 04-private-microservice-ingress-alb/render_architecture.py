"""Generate a precise SVG and fully editable diagrams.net drawing.

Usage: python render_architecture.py [--config project.json] [--png]
SVG/drawio generation uses only the Python standard library. Optional PNG:
    python -m pip install cairosvg
No Graphviz installation or Windows PATH modification is required.
"""
from pathlib import Path
import argparse
import base64
import json
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent
W, H = 1600, 1230
INK, MUTED = '#172B45', '#52647A'
BLUE, PURPLE, GREEN = '#2463AA', '#7653B6', '#16846C'
SVG_NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', SVG_NS)

class Canvas:
    """One scene produces SVG and native editable draw.io objects."""
    def __init__(self):
        self.svg = ET.Element(f'{{{SVG_NS}}}svg', width=str(W), height=str(H), viewBox=f'0 0 {W} {H}')
        ET.SubElement(self.svg, 'title').text = 'Internal microservice ingress architecture'
        ET.SubElement(self.svg, 'desc').text = 'Internal client to ALB to target group with EC2 targets in two Availability Zones. Security groups are resource policies.'
        defs = ET.SubElement(self.svg, 'defs')
        for color in [BLUE, PURPLE, GREEN]:
            marker = ET.SubElement(defs, 'marker', id='arrow'+color[1:], viewBox='0 0 10 10', refX='9', refY='5', markerWidth='8', markerHeight='8', orient='auto-start-reverse')
            ET.SubElement(marker, 'path', d='M 0 0 L 10 5 L 0 10 z', fill=color)
        self.mx = ET.Element('mxfile', host='app.diagrams.net', type='device')
        diagram = ET.SubElement(self.mx, 'diagram', name='Architecture', id='architecture')
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

    def rect(self, x,y,w,h,fill='#FFFFFF',stroke='#CBD5E1',radius=12,dash=False,width=1.5):
        a = dict(x=str(x),y=str(y),width=str(w),height=str(h),rx=str(radius),fill=fill,stroke=stroke,**{'stroke-width':str(width)})
        if dash: a['stroke-dasharray']='7 5'
        ET.SubElement(self.svg,'rect',a)
        self.cell(f'rounded={int(radius>0)};arcSize=8;whiteSpace=wrap;html=0;fillColor={fill};strokeColor={stroke};strokeWidth={width};dashed={int(dash)};',x,y,w,h)

    def text(self,x,y,value,size=18,color=INK,bold=False,w=600,align='left'):
        # y denotes top edge; explicit text objects remain editable in draw.io.
        tx = x if align=='left' else x+w/2
        el = ET.SubElement(self.svg,'text',x=str(tx),y=str(y+size),fill=color,**{'font-family':'DejaVu Sans, Arial, sans-serif','font-size':str(size),'font-weight':'700' if bold else '400','text-anchor':'start' if align=='left' else 'middle'})
        el.text=value
        self.cell(f'text;html=0;strokeColor=none;fillColor=none;align={align};verticalAlign=top;whiteSpace=wrap;rounded=0;fontFamily=Arial;fontSize={size};fontColor={color};fontStyle={1 if bold else 0};spacing=0;',x,y,w,size*1.4,value)

    def icon(self,name,x,y,size):
        data=base64.b64encode((BASE/'assets'/f'{name}.png').read_bytes()).decode()
        ET.SubElement(self.svg,'image',x=str(x),y=str(y),width=str(size),height=str(size),href='data:image/png;base64,'+data)
        self.cell('shape=image;verticalLabelPosition=bottom;verticalAlign=top;imageAspect=1;aspect=fixed;image=data:image/png,'+data+';',x,y,size,size)

    def line(self,points,color=BLUE,dash=False,arrow=True,width=2.5):
        a={'points':' '.join(f'{x},{y}' for x,y in points),'fill':'none','stroke':color,'stroke-width':str(width),'stroke-linejoin':'round'}
        if dash: a['stroke-dasharray']='7 5'
        if arrow: a['marker-end']='url(#arrow'+color[1:]+')'
        ET.SubElement(self.svg,'polyline',a)
        self.n+=1
        c=ET.SubElement(self.root,'mxCell',id=str(self.n),style=f'edgeStyle=none;rounded=0;html=0;strokeColor={color};strokeWidth={width};dashed={int(dash)};endArrow={"block" if arrow else "none"};endFill=1;',edge='1',parent='1')
        g=ET.SubElement(c,'mxGeometry',relative='1',**{'as':'geometry'})
        ET.SubElement(g,'mxPoint',x=str(points[0][0]),y=str(points[0][1]),**{'as':'sourcePoint'})
        ET.SubElement(g,'mxPoint',x=str(points[-1][0]),y=str(points[-1][1]),**{'as':'targetPoint'})
        arr=ET.SubElement(g,'Array',**{'as':'points'})
        for x,y in points[1:-1]: ET.SubElement(arr,'mxPoint',x=str(x),y=str(y))

    def save(self,stem,png=False):
        svg=BASE/f'{stem}.svg'
        ET.indent(self.svg)
        ET.ElementTree(self.svg).write(svg,encoding='utf-8',xml_declaration=True)
        ET.indent(self.mx)
        ET.ElementTree(self.mx).write(BASE/f'{stem}.drawio',encoding='utf-8',xml_declaration=True)
        if png:
            import cairosvg
            cairosvg.svg2png(url=str(svg),write_to=str(BASE/f'{stem}.png'),scale=2)
        print(f'Created {stem}.svg and {stem}.drawio'+(' and .png' if png else ''))

def render(cfg,png=False):
    c=Canvas()
    c.text(48,27,cfg['title'],34,bold=True,w=1480)
    c.text(48,78,'Internal ALB  /  path-based routing  /  security-group references  /  two Availability Zones',19,MUTED,w=1490)
    c.rect(48,119,70,5,'#FF9900','none',0)
    c.rect(40,150,1520,865,'#FFFFFF','#8795A8',14)
    c.text(66,168,'AWS CLOUD',16,bold=True,w=160)
    c.text(238,168,'Region  '+cfg['region'],16,MUTED,w=400)
    c.text(1110,168,'LOGICAL REQUEST FLOW',14,MUTED,bold=True,w=420)
    c.rect(66,211,1468,780,'#FAFCFF','#6B9B81',10)
    c.text(90,229,'CUSTOM VPC  '+cfg['vpc_cidr'],18,'#32684B',True,w=700)
    c.text(1060,231,'Internal client and private targets',16,MUTED,w=430)

    # Resource cards and attached policy annotations.
    c.rect(105,310,235,145,'#FFFFFF','#B5C4D6')
    c.icon('user',124,328,46)
    c.text(184,328,'VPC client',21,bold=True,w=145)
    c.text(125,389,'Service / consumer',17,MUTED,w=205)
    c.text(125,417,'Uses internal ALB DNS',15,MUTED,w=205)

    c.rect(440,280,620,235,'#F6F2FC','#9674C5')
    c.icon('alb',462,300,55)
    c.text(535,296,'Internal Application Load Balancer',22,bold=True,w=500)
    c.text(535,330,'HTTP :80  •  private addresses  •  sg-alb attached',16,MUTED,w=505)
    c.rect(463,373,574,49,'#FFFFFF','#D8CBEA',7)
    c.text(479,386,'10',17,PURPLE,True,w=40)
    c.text(521,386,'/api/v1/*',18,bold=True,w=150)
    c.text(703,387,'Forward to target group',17,PURPLE,w=320)
    c.rect(463,433,574,49,'#EDF8F3','#B7DCCE',7)
    c.text(479,446,'20',17,GREEN,True,w=40)
    c.text(521,446,'/health',18,bold=True,w=150)
    c.text(703,446,'Fixed 200 OK from ALB',17,GREEN,w=320)
    c.text(463,490,'One logical ALB across both AZs; subnet mappings to confirm.',14,MUTED,w=580)

    c.rect(1120,280,375,235,'#FFF8EF','#E7C48C')
    c.text(1142,299,'ATTACHED POLICY  ·  sg-alb',17,'#92601C',True,w=335)
    c.text(1142,340,'Inbound',15,MUTED,True,w=330)
    c.text(1142,365,'TCP 80 from '+cfg['vpc_cidr'],17,w=330)
    c.text(1142,404,'Outbound — recommended',15,MUTED,True,w=330)
    c.text(1142,429,'TCP 8080 to sg-app',17,w=330)
    c.text(1142,472,'Policy attachment, not a traffic hop',14,MUTED,w=335)
    c.line([(1060,316),(1120,316)],'#7653B6',dash=True,arrow=False,width=1.5)

    c.line([(340,355),(440,355)],BLUE)
    c.text(346,323,'HTTP :80',15,BLUE,w=95)
    c.line([(440,472),(385,472),(385,487),(220,487),(220,455)],GREEN,dash=True)
    c.text(109,500,'/health response: no backend call',14,GREEN,w=320)

    c.line([(750,515),(750,559)],PURPLE)
    c.text(772,528,'API requests',15,PURPLE,w=220)
    c.rect(570,560,360,108,'#FFFFFF','#9674C5')
    c.text(590,576,cfg['target_group'],22,PURPLE,True,w=320,align='center')
    c.text(590,612,'Target group  •  HTTP :8080',17,w=320,align='center')
    c.text(590,640,'Logical target set',14,MUTED,w=320,align='center')
    c.text(984,578,'BACKEND HEALTH CHECKS',15,GREEN,True,w=480)
    c.text(984,607,'ALB probes each registered target.',17,w=490)
    c.text(984,636,'Expected: 200  •  backend path: confirm',16,MUTED,w=490)
    c.line([(930,616),(963,616)],GREEN,dash=True,arrow=False,width=1.5)

    # Target group is a logical grouping, not another network appliance.
    c.text(795,680,'HTTP :8080 to either target',15,PURPLE,w=370)
    for x,az in zip([140,820],cfg['availability_zones']):
        c.rect(x,723,580,230,'#F6F9FC','#A6B5C7',10,True)
        c.text(x+20,737,'AVAILABILITY ZONE  '+az['name'],17,bold=True,w=540)
        c.rect(x+20,772,540,162,'#EFF7EF','#A7C6A9',8)
        c.text(x+38,782,'PRIVATE SUBNET  '+az['subnet'],16,'#386B45',True,w=505)
        c.rect(x+50,820,480,94,'#FFFFFF','#E7B86B',8)
        c.icon('ec2',x+65,837,52)
        c.text(x+135,830,az['replica'],21,bold=True,w=325)
        c.text(x+135,863,az['target']+'  •  sg-app attached',16,MUTED,w=330)
    # Keep the branch in the central gutter, clear of AZ/subnet headings.
    c.line([(750,668),(750,866),(670,866)],PURPLE)
    c.line([(750,866),(870,866)],PURPLE)
    c.text(190,960,'sg-app on both replicas: inbound TCP 8080 only from sg-alb',17,'#92601C',True,w=1210,align='center')

    # Documentation notes remain outside the resource boundary.
    c.rect(40,1040,745,115,'#F2F7FC','#D2DFEC',10)
    c.text(61,1056,'READ THIS DIAGRAM',16,BLUE,True,w=700)
    c.text(61,1085,'Solid arrows: requests   ·   Green dashed: fixed response',17,w=700)
    c.text(61,1114,'Security groups filter traffic on the ALB and EC2 interfaces.',16,MUTED,w=700)
    c.rect(805,1040,755,115,'#FFFAF0','#EAD7AC',10)
    c.text(826,1056,'CONFIRM IN YOUR DEPLOYMENT',16,'#92601C',True,w=710)
    c.text(826,1085,'ALB subnet mappings  ·  target health-check path',17,w=710)
    c.text(826,1114,'Default listener action  ·  actual outbound security-group rules',16,MUTED,w=710)
    c.text(48,1183,'Project documentation  •  based on supplied design, not a live AWS inspection',14,MUTED,w=1300)
    c.save(cfg.get('output','project-04-architecture'),png)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,default=BASE/'project.json')
    p.add_argument('--png',action='store_true')
    args=p.parse_args()
    render(json.loads(args.config.read_text(encoding='utf-8')),args.png)
