"""Blueprint theme: ONE drawing sheet with four figures, delivered as four stacked images. Writes assets/*.svg and snippet.md here.

fig1.svg  FIG. 1  events per week (full-width chart with dimension lines)
fig2.svg  FIG. 2  contribution hatch map
fig3.svg  FIG. 3  schedules: weekday load, material schedule (languages), specifications
fig4.svg  FIG. 4  system diagram (build pipeline + repos) and the sheet's title block

Four images instead of one tall one, so each figure animates when it scrolls into view. They are drawn as a single sheet:
one shared frame, grid lines that continue across the seams (every height is a multiple of 50), dashed zone lines at the seams.
snippet.md is the paste-ready README for the repo root. Run: PROFILE_USER=you python themes/blueprint/generate.py
"""
import math, sys
from datetime import date
from html import escape as esc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from profile_data import *  # shared GitHub data: USER, days, total, streak, user, repos, langs, ...
from isocity import HEATMAP_CSS, sweep

BG, GRID, LN, TX, DM, AC = "#0c3a66", "#ffffff", "#e8f1ff", "#dbeafe", "#8fb4dd", "#ffd166"  # blue paper, white lines, one yellow "red-line" accent
CSS = (HEATMAP_CSS + ".dr{stroke-dasharray:1;animation:dd 1.4s ease-out both}@keyframes dd{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}"
       ".fi{animation:fi .6s ease-out 1s both}@keyframes fi{from{opacity:0}}@media (prefers-reduced-motion:reduce){.dr,.fi{animation:none}}")  # lines draw in once, callouts fade in last; nothing loops
DEFS = f'''<defs>
<pattern id="gm" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M10 0H0V10" fill="none" stroke="{GRID}" stroke-opacity="0.07"/></pattern>
<pattern id="gM" width="50" height="50" patternUnits="userSpaceOnUse"><path d="M50 0H0V50" fill="none" stroke="{GRID}" stroke-opacity="0.16"/></pattern>
<pattern id="h1" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" stroke="{LN}" stroke-width="1"/></pattern>
<pattern id="h2" width="3.5" height="3.5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="3.5" stroke="{LN}" stroke-width="1"/></pattern>
<pattern id="h3" width="4.5" height="4.5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><path d="M0 0V4.5M0 0H4.5" stroke="{LN}" stroke-width="1"/></pattern>
<pattern id="h4" width="5" height="5" patternUnits="userSpaceOnUse"><circle cx="2.5" cy="2.5" r="0.9" fill="{LN}"/></pattern>
<pattern id="h5" width="5" height="5" patternUnits="userSpaceOnUse"><line x1="0" y1="2.5" x2="5" y2="2.5" stroke="{LN}" stroke-width="1"/></pattern>
<marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 1L10 5L0 9z" fill="{LN}"/></marker>
</defs>'''
HATCH = ["h1", "h2", "h3", "h4", "h5"]  # one hatch per language, like a materials legend
DATE = f"{now:%Y-%m-%d}"
ceil50 = lambda v: int(math.ceil(v / 50) * 50)  # every figure is a multiple of 50 tall so the grid lines up across the seams


def T(x, y, s, size=10, anchor="start", fill=TX, ls=0, extra=""):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" letter-spacing="{ls}" {extra}>{esc(str(s))}</text>'


def dim(x1, y1, x2, y2, label):
    """dimension line with arrowheads and a label sitting on a break in the line"""
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    w = 7 * len(label) + 12
    horiz = y1 == y2
    gap = f'<rect x="{cx - w / 2:.0f}" y="{cy - 7:.0f}" width="{w}" height="14" fill="{BG}"/>' if horiz else f'<rect x="{cx - 7:.0f}" y="{cy - w / 2:.0f}" width="14" height="{w}" fill="{BG}"/>'
    txt = T(cx, cy + 3.5, label, 10, "middle") if horiz else f'<text transform="translate({cx + 3.5:.0f},{cy:.0f}) rotate(-90)" font-size="10" fill="{TX}" text-anchor="middle">{esc(label)}</text>'
    return f'<line class="dr" pathLength="1" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{LN}" marker-start="url(#ar)" marker-end="url(#ar)"/>{gap}{txt}'


def cellbox(x, y, w, h, k, v, size=12):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{LN}"/>' + T(x + 8, y + 14, k, 8, "start", DM, 1) + T(x + 8, y + h - 10, v, size)


def callout_path(x, y, reach):
    """leader line from a circled point to a label, going left unless the point is near the left edge; returns (path d, label x)"""
    s = -1 if x > 220 else 1
    return f"M{x + s * 7:.0f},{y - 7:.0f} L{x + s * 40:.0f},{y - 22:.0f} H{x + s * reach:.0f}", (x - reach if s < 0 else x + 44)


# ---------- FIG. 1: events per week ----------
def fig1():
    BASE, TOP, X0, X1 = 300, 150, 34, 668
    n = len(vols)
    vm = max(vols) or 1
    px = lambda i: X0 + i * (X1 - X0) / max(n - 1, 1)
    py = lambda v: BASE - v / vm * (BASE - TOP)
    pts = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in enumerate(vols))
    first = {}
    for c in days:
        first.setdefault(c[1], c[2])
    seen, months = set(), ""
    for i, k in enumerate(sorted(first)):
        d = date.fromisoformat(first[k])
        if d.strftime("%Y-%m") not in seen and d.day < 14:  # label the week a month starts in
            seen.add(d.strftime("%Y-%m"))
            months += f'<line x1="{px(i):.0f}" x2="{px(i):.0f}" y1="{BASE}" y2="{BASE + 5}" stroke="{LN}"/>' + T(px(i), BASE + 16, f"{d:%b}".upper(), 8, "middle", DM)
    body = (T(34, 44, "ACTIVITY DRAWING", 16, "start", TX, 2) + T(34, 62, f"{TAGLINE} · {d0:%b %Y} TO {d1:%b %Y}".upper(), 10, "start", DM)
            + T(34, 92, "FIG. 1 · EVENTS PER WEEK", 12, "start", TX, 2)
            + f'<polygon points="{px(0):.1f},{BASE} {pts} {px(n - 1):.1f},{BASE}" fill="url(#h1)" opacity="0.55"/>'
            f'<polyline class="dr" pathLength="1" points="{pts}" fill="none" stroke="{LN}" stroke-width="1.6"/>'
            f'<line x1="{X0}" x2="{X1}" y1="{BASE}" y2="{BASE}" stroke="{LN}"/>{months}')
    if best[4]:  # circle the week that holds the busiest day
        bx, by = px(best[1]), py(vols[best[1]])
        d_, tx_ = callout_path(bx, by, 150)
        body += (f'<circle class="fi" cx="{bx:.1f}" cy="{by:.1f}" r="9" fill="none" stroke="{AC}" stroke-width="1.5"/><path class="fi" d="{d_}" fill="none" stroke="{AC}"/>'
                 + T(tx_, by - 26, f"(1) BUSIEST DAY: {best[4]} · {bd:%b %d}".upper(), 10, "start", AC, 0, 'class="fi"'))
    body += dim(X0, BASE + 34, X1, BASE + 34, f"{n} WK · {total:,} EVENTS") + dim(X1 + 22, TOP, X1 + 22, BASE, f"PEAK WK {vm}")
    body += "".join(f'<line x1="{xx}" x2="{xx}" y1="{BASE + 18}" y2="{BASE + 40}" stroke="{LN}" stroke-opacity="0.6"/>' for xx in (X0, X1))
    body += "".join(f'<line x1="{X1}" x2="{X1 + 28}" y1="{yy}" y2="{yy}" stroke="{LN}" stroke-opacity="0.6"/>' for yy in (TOP, BASE))
    return body, 350, f"Figure 1: weekly events for {USER}, {total} contributions over {n} weeks, peak week {vm}"


# ---------- FIG. 2: hatch map ----------
def fig2():
    ncols = max(c[1] for c in days) + 1
    P = min(13.0, 686 / ncols)  # cell pitch, so a 54-week calendar still fits inside the frame
    FILL = {0: "none", 1: "url(#h1)", 2: "url(#h2)", 3: "url(#h3)", 4: "url(#h3)"}
    cells = ""
    for r, c, d, lvl, cnt in days:
        hot = cnt >= high_min
        cells += (f'<rect class="h" {sweep(c, r)} x="{44 + c * P:.1f}" y="{70 + r * P:.1f}" width="{P - 2:.1f}" height="{P - 2:.1f}" fill="{AC if hot else FILL[lvl]}" fill-opacity="{0.85 if hot else 1}" '
                  f'stroke="{AC if hot else LN}" stroke-opacity="{1 if hot else 0.35}"/>')
    wl = "".join(T(24, 79 + i * P, WD[i][:3].upper(), 8, "start", DM) for i in (1, 3, 5))
    callout = ""
    legend = [(44, "none", "NONE"), (110, "url(#h1)", "LIGHT"), (180, "url(#h2)", "STEADY"), (262, "url(#h3)", "HEAVY")]
    if maxc >= high_min:  # a busy day exists: circle the busiest one and add it to the legend
        cx, cy = 44 + best[1] * P + (P - 2) / 2, 70 + best[0] * P + (P - 2) / 2
        s = -1 if cx > 220 else 1
        callout = (f'<circle class="fi" cx="{cx:.1f}" cy="{cy:.1f}" r="12" fill="none" stroke="{AC}" stroke-width="1.5"/>'
                   f'<path class="fi" d="M{cx:.1f},{cy + 12:.1f} V176 H{cx + s * 150:.1f}" fill="none" stroke="{AC}"/>'
                   + T(cx - 150 if s < 0 else cx + 4, 172, f"(2) PEAK · {maxc} · {bd:%b %d}".upper(), 10, "start", AC, 0, 'class="fi"'))
        legend.append((348, AC, f"BUSY DAY (≥ {int(high_min)})"))
    leg = "".join(f'<rect x="{x}" y="204" width="14" height="10" fill="{f}" stroke="{AC if f == AC else LN}" stroke-opacity="0.8"/>' + T(x + 20, 213, t, 8, "start", DM) for x, f, t in legend)
    body = T(34, 40, "FIG. 2 · CONTRIBUTION HATCH MAP", 12, "start", TX, 2) + T(34, 54, "ONE CELL PER DAY · HATCH DENSITY = ACTIVITY", 8, "start", DM, 1) + cells + wl + callout + leg
    return body, 250, f"Figure 2: contribution hatch map for {USER}, {total} contributions on {active} active days"


# ---------- FIG. 3: schedules ----------
def fig3():
    load = T(34, 84, "WEEKDAY LOAD", 10, "start", TX, 1.5) + f'<line x1="34" x2="262" y1="214" y2="214" stroke="{LN}"/>'
    for i, (name, v) in enumerate(zip(WD, wd)):  # outlined, hatched columns; the busiest weekday is cross-hatched and outlined in yellow
        h, x, peak = 100 * v / wmax, 44 + i * 30, v == wmax and v > 0
        load += (f'<rect class="h" style="animation-delay:{i * 70}ms" x="{x}" y="{214 - h:.0f}" width="20" height="{h:.0f}" fill="url(#{"h3" if peak else "h2"})" stroke="{AC if peak else LN}"/>'
                 + T(x + 10, 227, name[0].upper(), 10, "middle", DM) + T(x + 10, 208 - h, f"{v:,}", 10, "middle", AC if peak else TX))
    if lang_total:  # material schedule: one hatch per language (top 4 + "+N more" past five)
        shown = lang_rows if len(lang_rows) <= 5 else lang_rows[:4]
        entries = [(name[:8].upper(), 100 * b / lang_total, HATCH[i]) for i, (name, b) in enumerate(shown)]
        if len(lang_rows) > 5:
            entries.append((f"+{len(lang_rows) - 4} MORE", 100 * sum(b for _, b in lang_rows[4:]) / lang_total, "h5"))
    else:
        entries = []
    sched = T(284, 84, "MATERIAL SCHEDULE", 10, "start", TX, 1.5) + f'<rect x="284" y="94" width="220" height="20" fill="none" stroke="{LN}"/>'
    x = 284
    for name, pct, hatch in entries:
        sched += f'<rect x="{x:.1f}" y="94" width="{max(220 * pct / 100, 1):.1f}" height="20" fill="url(#{hatch})" stroke="{LN}"/>'
        x += 220 * pct / 100
    for i, (name, pct, hatch) in enumerate(entries):
        cx, cy = 284 + (i % 2) * 114, 128 + (i // 2) * 16  # two columns of legend
        sched += f'<rect x="{cx}" y="{cy}" width="16" height="10" fill="url(#{hatch})" stroke="{LN}"/>' + T(cx + 22, cy + 9, name, 10) + T(cx + 106, cy + 9, f"{pct:.0f}%", 10, "end", DM)
    sched += T(284, 214, "ONLY LANGUAGES WITH PUBLIC CODE" if entries else "NO PUBLIC CODE YET", 8, "start", DM)
    specs = [("EVENTS · 12M", f"{total:,}"), ("ACTIVE DAYS", str(active)), ("STREAK", f"{streak} D"), ("LONGEST", f"{longest} D"),
             ("REPOS", str(user["public_repos"])), ("STARS", str(stars)), ("FOLLOWERS", str(user["followers"])), ("JOINED", f"{joined:%b %Y}".upper())]
    SX, SY, SW, RH = 528, 70, 208, 18
    table = (f'<rect x="{SX}" y="{SY}" width="{SW}" height="{22 + 8 * RH}" fill="none" stroke="{LN}"/><rect x="{SX}" y="{SY}" width="{SW}" height="22" fill="{LN}" fill-opacity="0.14" stroke="{LN}"/>'
             + T(SX + 10, SY + 15, "SPECIFICATIONS", 10, "start", TX, 1.5))
    for i, (k, v) in enumerate(specs):
        y = SY + 22 + i * RH
        table += f'<line x1="{SX}" x2="{SX + SW}" y1="{y}" y2="{y}" stroke="{LN}" stroke-opacity="0.45"/>' + T(SX + 10, y + 13, k, 10, "start", DM) + T(SX + SW - 10, y + 13, v, 12, "end", TX)
    body = T(34, 40, "FIG. 3 · SCHEDULES", 12, "start", TX, 2) + T(34, 54, "WEEKDAY LOAD · MATERIALS · SPECIFICATIONS", 8, "start", DM, 1) + load + sched + table
    return body, 250, f"Figure 3: schedules for {USER}: weekday load, languages and specifications"


# ---------- FIG. 4: system diagram + title block ----------
TAGS = {"featured": "FEATURED", "active": "ACTIVE", "idle": "IDLE"}


def node(x, y, w, h, title, sub, kind):
    col = {"featured": AC, "active": LN, "idle": DM, "reserved": DM}[kind]
    dash = ' stroke-dasharray="5 4"' if kind == "reserved" else ""
    out = f'<rect x="{x - 4}" y="{y - 4}" width="{w + 8}" height="{h + 8}" fill="none" stroke="{AC}"/>' if kind == "featured" else ""  # featured repos get a double border
    return (out + f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{BG}" stroke="{col}" stroke-width="1.4"{dash}/>' + T(x + 12, y + 22, title, 12, "start", DM if kind == "reserved" else TX) + T(x + 12, y + 40, sub, 10, "start", DM)
            + f'<rect x="{x + w - 78}" y="{y + 10}" width="66" height="16" fill="none" stroke="{col}"{dash}/>' + T(x + w - 45, y + 21.5, "EMPTY" if kind == "reserved" else TAGS[kind], 8, "middle", col, 1))


def fig4():
    nodes = []
    for r in ranked[:5]:
        pushed = date.fromisoformat(r["pushed_at"][:10])
        stars_ = r["stargazers_count"]
        nodes.append((r["name"].upper() if len(r["name"]) <= 30 else r["name"].upper()[:29] + "…",
                      f'{(r["language"] or "NO LANGUAGE").upper()} · {stars_} STAR{"" if stars_ == 1 else "S"} · PUSHED {pushed:%b %d}'.upper(), repo_status(r)))
    while len(nodes) < 3:  # always at least three rows, like the other themes
        nodes.append(("— RESERVED —", "NEXT PROJECT SLOT", "reserved"))
    ny, hubh = 118, max(60, 70 * len(nodes) - 16)
    body = T(34, 40, "FIG. 4 · SYSTEM DIAGRAM", 12, "start", TX, 2)
    for i, step in enumerate(["GITHUB API", "ACTIONS · 3H", "GENERATE.PY", "README.MD"]):  # the real build pipeline
        x = 34 + i * 178
        body += f'<rect x="{x}" y="58" width="140" height="26" fill="none" stroke="{LN}"/>' + T(x + 70, 75, step, 10, "middle")
        if i < 3:
            body += f'<line class="dr" pathLength="1" x1="{x + 140}" y1="71" x2="{x + 178}" y2="71" stroke="{LN}" marker-end="url(#ar)"/>'
    body += T(34, ny - 10, "REPOSITORIES", 8, "start", DM, 2)
    body += f'<rect x="34" y="{ny}" width="150" height="{hubh}" fill="none" stroke="{LN}" stroke-width="1.6"/>' + T(109, ny + hubh / 2 - 4, "OWNER", 8, "middle", DM, 2) + T(109, ny + hubh / 2 + 12, USER.upper()[:14], 10, "middle")
    for i, (title, sub, kind) in enumerate(nodes):
        y = ny + i * 70
        body += node(300, y, 436, 54, title, sub, kind)
        body += f'<path class="dr" pathLength="1" d="M184,{ny + hubh / 2:.0f} H242 V{y + 27} H300" fill="none" stroke="{LN}" marker-end="url(#ar)"' + (' stroke-dasharray="5 4"' if kind == "reserved" else "") + "/>"
    ty = ny + hubh + 36  # the sheet's title block
    body += (cellbox(30, ty, 330, 50, "PROJECT", f"{USER.upper()[:22]} · PROFILE", 14 if len(USER) <= 14 else 12) + cellbox(360, ty, 120, 50, "DRAWN BY", "GITHUB ACTIONS", 10) + cellbox(480, ty, 100, 50, "DATE", DATE) +
             cellbox(580, ty, 70, 50, "REV", "A") + cellbox(650, ty, 80, 50, "SHEET", "1 OF 1") + T(30, ty + 68, "AUTO-REVISED EVERY 3 HOURS FROM LIVE GITHUB DATA", 8, "start", DM, 1))
    return body, ceil50(ty + 68 + 26), f"Figure 4: system diagram of {USER}'s {len(ranked)} public repos, with the sheet title block"


# ---------- compose: one sheet, four images ----------
def paper(h, first, last, r=6):
    t, b = r if first else 0, r if last else 0
    return (f"M{t},0 H{760 - t} " + (f"A{t},{t} 0 0 1 760,{t} " if first else "") + f"V{h - b} " + (f"A{b},{b} 0 0 1 {760 - b},{h} " if last else "")
            + f"H{b} " + (f"A{b},{b} 0 0 1 0,{h - b} " if last else "") + f"V{t} " + (f"A{t},{t} 0 0 1 {t},0 " if first else "") + "Z")


def layer(i, body, h, y0, total_h, label):
    first, last = i == 0, i == 3
    ticks = "".join(f'<text x="{x}" y="11" font-size="8" fill="{DM}" text-anchor="middle">{k + 1}</text>' for k, x in enumerate(range(95, 760, 190))) if first else ""
    ticks += "".join(f'<text x="5" y="{p - y0 + 3:.0f}" font-size="8" fill="{DM}" text-anchor="middle">{c}</text>' for c, p in zip("ABCD", [total_h * k / 5 for k in range(1, 5)]) if y0 <= p < y0 + h)  # reference letters run down the whole sheet
    top, bot = (12 if first else 0), (h - 12 if last else h)
    ti, bi = (17 if first else 0), (h - 17 if last else h)
    frame = (f'<path d="M12,{top} V{bot} M748,{top} V{bot}' + (" M12,12 H748" if first else "") + (f" M12,{h - 12} H748" if last else "") + f'" fill="none" stroke="{LN}" stroke-width="1.6"/>'
             f'<path d="M17,{ti} V{bi} M743,{ti} V{bi}' + (" M17,17 H743" if first else "") + (f" M17,{h - 17} H743" if last else "") + f'" fill="none" stroke="{LN}" stroke-opacity="0.5"/>')
    seam = "" if last else f'<line x1="17" x2="743" y1="{h - 0.5}" y2="{h - 0.5}" stroke="{LN}" stroke-opacity="0.55" stroke-dasharray="6 4"/>'  # dashed zone line between figures
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 {h}" width="760" height="{h}" role="img" aria-label="{esc(label)}" font-family="{MONO}" font-size="10">
<style>text{{white-space:pre}}{CSS}</style>{DEFS}<clipPath id="pp"><path d="{paper(h, first, last)}"/></clipPath>
<g clip-path="url(#pp)"><rect width="760" height="{h}" fill="{BG}"/><rect width="760" height="{h}" fill="url(#gm)"/><rect width="760" height="{h}" fill="url(#gM)"/></g>
{frame}{seam}{ticks}{body}</svg>
'''


figs = [fig1(), fig2(), fig3(), fig4()]
total_h = sum(h for _, h, _ in figs)
y0 = 0
for i, (body, h, label) in enumerate(figs):
    write(f"assets/fig{i + 1}.svg", layer(i, body, h, y0, total_h, label))
    y0 += h

A = "./themes/blueprint/assets"
write("snippet.md", f'''<p align="center">
  <img src="{A}/fig1.svg" alt="Blueprint figure 1: weekly events chart for {esc(USER)}" width="100%" /><br/>
  <img src="{A}/fig2.svg" alt="Blueprint figure 2: contribution hatch map" width="100%" /><br/>
  <img src="{A}/fig3.svg" alt="Blueprint figure 3: weekday load, languages and specifications" width="100%" /><br/>
  <a href="https://github.com/{esc(USER)}?tab=repositories"><img src="{A}/fig4.svg" alt="Blueprint figure 4: system diagram of {esc(USER)}'s repositories, with the title block" width="100%" /></a>
</p>
''')
print(f"{USER}: total={total} active={active} streak={streak} weeks={len(vols)} repos={len(repos)} langs={len(lang_rows)} sheet={total_h}px in {len(figs)} figs")
