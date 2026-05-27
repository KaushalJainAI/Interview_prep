"""Final batch: JOB-SEARCH diagrams + topic-overview master diagram."""
from pathlib import Path

ROOT = Path(r"C:\Users\91700\Desktop\Interview notes")

STYLE = """
<style>
  .title { font: bold 16px sans-serif; fill: #1a1a1a; }
  .label { font: 12px sans-serif; fill: #333; }
  .small { font: 10px sans-serif; fill: #555; }
  .mono  { font: 13px 'Consolas','Courier New',monospace; fill: #111; }
  .box   { fill: #f6f8fa; stroke: #444; stroke-width: 1.2; }
  .box2  { fill: #e6f0ff; stroke: #1f6feb; stroke-width: 1.5; }
  .box3  { fill: #fff3cd; stroke: #b58900; stroke-width: 1.5; }
  .box4  { fill: #d4edda; stroke: #1a7f37; stroke-width: 1.5; }
  .box5  { fill: #fce7f3; stroke: #be185d; stroke-width: 1.5; }
  .arrow { stroke: #444; stroke-width: 1.6; fill: none; marker-end: url(#arr); }
  .arrow2{ stroke: #1f6feb; stroke-width: 2; fill: none; marker-end: url(#arrB); }
</style>
<defs>
  <marker id="arr"  viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#444"/></marker>
  <marker id="arrB" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#1f6feb"/></marker>
</defs>
"""
def svg(w,h,body,title=None):
    t = f'<text x="{w//2}" y="22" text-anchor="middle" class="title">{title}</text>' if title else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{STYLE}{t}{body}</svg>'

def d_funnel():
    body = ''
    stages = [
        ("Applications sent",  600, 80,  "box"),
        ("Recruiter calls",    440, 140, "box2"),
        ("Tech screens",       320, 200, "box3"),
        ("On-site / final",    200, 260, "box4"),
        ("Offers",              90, 320, "box5"),
    ]
    counts = ["100","20","8","3","1"]
    cx = 380
    for i,(label,w,y,cls) in enumerate(stages):
        body += f'<rect x="{cx-w/2}" y="{y-22}" width="{w}" height="44" class="{cls}"/>'
        body += f'<text x="{cx}" y="{y+5}" text-anchor="middle" class="mono">{label}</text>'
        body += f'<text x="{cx+w/2+15}" y="{y+5}" class="mono">≈ {counts[i]}</text>'
    body += '<text x="40" y="390" class="label">Conversion rates (typical for mid-level AI roles, India 2026):</text>'
    body += '<text x="60" y="410" class="mono">app→recruiter ~20%, recruiter→screen ~40%, screen→onsite ~40%, onsite→offer ~30%</text>'
    body += '<text x="40" y="438" class="small">Aim for 100+ targeted apps; referrals push conversion well past these baselines.</text>'
    return svg(820, 470, body, "Job-Search Funnel — Apps to Offers")

def d_cadence():
    body = ''
    days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    for i,d in enumerate(days):
        x = 60 + i*100
        body += f'<rect x="{x}" y="60" width="90" height="36" class="box2"/>'
        body += f'<text x="{x+45}" y="84" text-anchor="middle" class="mono">{d}</text>'
    # daily blocks
    activities = [
        ("LinkedIn alerts → apply",     "box"),
        ("3 cold emails",               "box3"),
        ("LinkedIn post / comment",     "box4"),
        ("1 LeetCode / project hour",   "box5"),
    ]
    for r,(act,cls) in enumerate(activities):
        y = 110 + r*54
        for i in range(7):
            x = 60 + i*100
            # weekend lighter
            opacity = 0.4 if i>=5 else 1
            body += f'<rect x="{x}" y="{y}" width="90" height="42" class="{cls}" opacity="{opacity}"/>'
            body += f'<text x="{x+45}" y="{y+25}" text-anchor="middle" class="small">{act}</text>'
    # weekly block
    body += '<rect x="60" y="350" width="730" height="50" class="box2" opacity="0.9"/>'
    body += '<text x="425" y="380" text-anchor="middle" class="mono">Weekly: update tracker · 25 new connections · ask 2 seniors for referrals · 1 project post</text>'
    body += '<text x="40" y="430" class="small">45 min/day routine; protect this slot. Bursts (8-12hr application sessions) feel productive but compound less.</text>'
    return svg(820, 460, body, "Weekly Job-Search Cadence")

def d_interview_stages():
    body = ''
    stages = [
        ("Phone screen",        80, "box2", "fit + intro + light tech"),
        ("Tech screen 1",      170, "box3", "DSA / coding live"),
        ("Tech screen 2",      260, "box3", "ML / system design"),
        ("Project deep-dive",  350, "box4", "your work — AIAAS / NGU"),
        ("Behavioural / values", 440, "box5", "STAR stories"),
        ("Bar-raiser / hiring mgr", 530, "box", "calibration"),
    ]
    for label, y, cls, desc in stages:
        body += f'<rect x="80" y="{y-22}" width="180" height="44" class="{cls}"/>'
        body += f'<text x="170" y="{y-2}" text-anchor="middle" class="mono">{label}</text>'
        body += f'<text x="170" y="{y+15}" text-anchor="middle" class="small">{desc}</text>'
        body += f'<text x="290" y="{y+5}" class="small">→ prepare:  {desc}</text>'
    body += '<text x="40" y="600" class="mono">3-5 rounds typical; spread over 2-4 weeks. Recruiter usually previews format.</text>'
    body += '<text x="40" y="624" class="small">Drop-off lowest at later rounds — push for clarity on next step before ending each call.</text>'
    return svg(820, 660, body, "Typical Interview Pipeline (5-6 rounds)")

def d_overview():
    body = ''
    body += '<text x="430" y="60" text-anchor="middle" class="label">Where each topic lives — interview prep map</text>'
    nodes = {
        "Core CS":    (430, 130, "box2"),
        "DSA":        (130, 230, "box4"),
        "DBMS/SQL":   (250, 230, "box4"),
        "OOP":        (370, 230, "box4"),
        "Python":     (490, 230, "box4"),
        "AI/ML":      (430, 330, "box2"),
        "ML algos":   (140, 430, "box3"),
        "DL basics":  (260, 430, "box3"),
        "CNN/RNN":    (380, 430, "box3"),
        "Transformers":(500, 430, "box3"),
        "Agents":     (620, 430, "box3"),
        "Engineering":(430, 540, "box2"),
        "Backend":    (110, 640, "box5"),
        "Frontend":   (230, 640, "box5"),
        "Deploy":     (350, 640, "box5"),
        "Git/Test":   (470, 640, "box5"),
        "SysDesign":  (590, 640, "box5"),
        "Security":   (710, 640, "box5"),
    }
    for name,(x,y,cls) in nodes.items():
        w = max(110, len(name)*9+10)
        body += f'<rect x="{x-w/2}" y="{y-20}" width="{w}" height="40" class="{cls}"/>'
        body += f'<text x="{x}" y="{y+5}" text-anchor="middle" class="mono">{name}</text>'
    edges = [("Core CS","DSA"),("Core CS","DBMS/SQL"),("Core CS","OOP"),("Core CS","Python"),
             ("AI/ML","ML algos"),("AI/ML","DL basics"),("AI/ML","CNN/RNN"),("AI/ML","Transformers"),("AI/ML","Agents"),
             ("Engineering","Backend"),("Engineering","Frontend"),("Engineering","Deploy"),
             ("Engineering","Git/Test"),("Engineering","SysDesign"),("Engineering","Security")]
    for a,b in edges:
        x1,y1,_ = nodes[a]; x2,y2,_ = nodes[b]
        body += f'<line x1="{x1}" y1="{y1+20}" x2="{x2}" y2="{y2-20}" stroke="#888" stroke-width="1.2"/>'
    return svg(860, 680, body, "Interview Prep Overview")

# Write
(ROOT / "JOB-SEARCH" / "diagrams").mkdir(parents=True, exist_ok=True)
(ROOT / "JOB-SEARCH" / "diagrams" / "01-funnel.svg").write_text(d_funnel(), encoding="utf-8")
(ROOT / "JOB-SEARCH" / "diagrams" / "02-cadence.svg").write_text(d_cadence(), encoding="utf-8")
(ROOT / "JOB-SEARCH" / "diagrams" / "03-interview-pipeline.svg").write_text(d_interview_stages(), encoding="utf-8")

(ROOT / "diagrams").mkdir(exist_ok=True)
(ROOT / "diagrams" / "00-topic-map.svg").write_text(d_overview(), encoding="utf-8")
print("done")
