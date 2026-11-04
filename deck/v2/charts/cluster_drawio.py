"""Generate the clustering-concept draw.io diagram (pastel house style). Usage: python cluster_drawio.py out.drawio"""
import random
import sys
from xml.sax.saxutils import escape

random.seed(7)
cells = []
nid = [2]


def cid():
    nid[0] += 1
    return f"c{nid[0]}"


def box(x, y, w, h, text, style):
    i = cid()
    cells.append(f'<mxCell id="{i}" value="{escape(text)}" style="{style}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
    return i


def arrow(a, b):
    cells.append(f'<mxCell id="{cid()}" style="endArrow=block;endFill=1;strokeColor=#000000;strokeWidth=1.5;html=1;" edge="1" parent="1" source="{a}" target="{b}"><mxGeometry relative="1" as="geometry"/></mxCell>')


GROUP = "rounded=1;arcSize=4;dashed=1;fillColor=none;strokeColor=#999999;html=1;verticalAlign=top;align=left;spacingLeft=12;spacingTop=8;fontSize=17;fontStyle=1;"
BLUE = "fillColor=#dae8fc;strokeColor=#6c8ebf;"
GREEN = "fillColor=#d5e8d4;strokeColor=#82b366;"
YELLOW = "fillColor=#fff2cc;strokeColor=#d6b656;"
TXT = "text;html=1;align=center;verticalAlign=middle;fontSize=15;whiteSpace=wrap;"
DOT = "ellipse;html=1;strokeWidth=1;"

# Panel 1: messages
g1 = box(20, 20, 300, 440, "1  Messages", GROUP)
for _ in range(60):
    box(45 + random.random() * 245, 75 + random.random() * 290, 13, 13, "", DOT + "fillColor=#f5f5f5;strokeColor=#666666;")
box(30, 385, 280, 60, "209,109 train prompts<br>user text only, no labels", TXT)

# Panel 2: embedding
g2 = box(380, 20, 300, 440, "2  Embedding · Jina v5 nano", GROUP)
centers2 = [(470, 120), (600, 110), (450, 230), (590, 220), (500, 330), (630, 320), (420, 340), (540, 170)]
for cx, cy in centers2:
    for _ in range(7):
        box(cx + random.gauss(0, 14), cy + random.gauss(0, 12), 13, 13, "", DOT + BLUE)
box(390, 372, 280, 80, "<b>jina-embeddings-v5-text-nano</b>, run locally;<br>similar meaning lands close;<br>vectors kept in <b>Qdrant</b>", TXT + "fontSize=14;")

# Panel 3: 8 topic clusters
g3 = box(740, 20, 520, 440, "3  K-means → 8 topics", GROUP)
names = ["Short fragments", "Account & tech support", "Relationships & emotions", "Humanities & religion",
         "Science & maths", "Payments & finance", "General short chat", "Health & medicine"]
pal = [("#dae8fc", "#6c8ebf"), ("#d5e8d4", "#82b366"), ("#ffe6cc", "#d79b00"), ("#e1d5e7", "#9673a6"),
       ("#fff2cc", "#d6b656"), ("#f8cecc", "#b85450"), ("#f5f5f5", "#666666"), ("#d0e0e3", "#0e8088")]
for k, (nm, (fc, sc)) in enumerate(zip(names, pal)):
    col, row = k % 2, k // 2
    x, y = 760 + col * 250, 70 + row * 92
    box(x, y, 235, 80, "", f"rounded=1;arcSize=12;html=1;fillColor={fc};strokeColor={sc};")
    for d in range(6):
        box(x + 12 + (d % 3) * 18 + random.random() * 4, y + 14 + (d // 3) * 22 + random.random() * 4, 12, 12, "", DOT + f"fillColor={sc};strokeColor={sc};")
    box(x + 72, y + 10, 160, 60, f"<b>{nm}</b>", "text;html=1;align=left;verticalAlign=middle;fontSize=14;whiteSpace=wrap;")

# Panel 4: fingerprint report card
g4 = box(1320, 20, 400, 440, "4  Fingerprint Ψ per topic", GROUP)
rows = [("Model", "Error, Health & medicine"), ("DeepSeek", "22%  ✓ best value"), ("Sonnet", "22%  (24× the price)"),
        ("Luna", "28%"), ("Gemini", "32%")]
for r, (a, b) in enumerate(rows):
    st = ("fillColor=#fff2cc;strokeColor=#d6b656;" if r == 1 else "fillColor=#ffffff;strokeColor=#999999;") + "html=1;fontSize=14;" + ("fontStyle=1;" if r in (0, 1) else "")
    box(1340, 70 + r * 46, 120, 46, a, st)
    box(1460, 70 + r * 46, 240, 46, b, st + "align=left;spacingLeft=10;")
box(1335, 315, 370, 130, "New message → nearest topic →<br>lowest <b>Ψ + λ·cost</b> wins", TXT + "fontSize=16;")

arrow(g1, g2); arrow(g2, g3); arrow(g3, g4)

# bottom note
box(20, 490, 1700, 64, "<b>New model?</b> It answers the same 800 validation questions once → one new column in Ψ for every topic. No retraining; the topics stay.",
    TXT + YELLOW + "rounded=1;fontSize=17;whiteSpace=wrap;")

xml = ('<mxfile><diagram name="clustering"><mxGraphModel dx="1800" dy="600" grid="0" page="0"><root>'
       '<mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(cells) + "</root></mxGraphModel></diagram></mxfile>")
open(sys.argv[1], "w").write(xml)
