"""SOC dashboard theme: a security-operations console. Writes assets/*.svg and snippet.md into this folder.

dashboard.svg (KPIs, weekly event timeline, activity gauge, severity donut, weekday bars, assets, status bar),
calendar.svg (every day coloured by severity), feed.svg (repos as an asset table).
snippet.md is the paste-ready README for the repo root. Run: PROFILE_USER=you python themes/soc/generate.py
"""
import math, sys
from datetime import date
from html import escape as esc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from profile_data import *  # shared GitHub data: USER, days, total, streak, user, repos, langs, ...
from isocity import HEATMAP_CSS, sweep

BG, PN, LN, TX, DM, CY = "#070b14", "#0d1422", "#1b2740", "#e2e8f0", "#7b8aa5", "#22d3ee"
SEVC = {1: "#22c55e", 2: "#eab308", 3: "#f97316", 4: "#ef4444"}  # alert severity: low, medium, high, critical
SEVN = {1: "Low", 2: "Medium", 3: "High", 4: "Critical"}
ACT = ["#60a5fa", "#22d3ee", "#34d399", "#fbbf24"]  # activity gauge: calm blue -> cyan -> green -> amber, no reds
ACTN = ["QUIET", "STEADY", "BUSY", "PEAK"]
FADE = "@keyframes fade{from{opacity:0}}"
def sev(n):  # 0 none, 1 low .. 4 critical (critical = the shared "busy day" threshold)
    return 0 if n == 0 else 4 if n >= high_min else 3 if n >= 14 else 2 if n >= 5 else 1


def status(r):  # (label, colour) of a repo: used by the dashboard's asset panel and the feed, so they always agree
    recent = (now.date() - date.fromisoformat(r["pushed_at"][:10])).days <= 30
    return ("FEATURED", SEVC[2]) if is_fav(r) else ("ACTIVE", SEVC[1]) if recent else ("IDLE", DM)


def panel(x, y, w, h, title, inner):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{PN}" stroke="{LN}"/>'
            f'<text x="{x + 14}" y="{y + 20}" font-size="10" font-weight="700" letter-spacing="1.6" fill="{DM}">{title}</text>{inner}')


def arc(cx, cy, r, a0, a1):
    p = lambda a: (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
    (x0, y0), (x1, y1) = p(a0), p(a1)
    return f"M{x0:.1f},{y0:.1f} A{r},{r} 0 0 1 {x1:.1f},{y1:.1f}"


vm = max(vols) or 1
frac = 0.5 if chg is None else min(1, max(0, (chg + 50) / 200))  # -50%..+150% -> 0..1
zi = min(3, int(frac * 4))
zc = ACT[zi]
counts = {k: sum(1 for c in days if sev(c[4]) == k) for k in (1, 2, 3, 4)}

# ---------- dashboard ----------
kpis = [("EVENTS · 12M", f"{total:,}", TX, f"{len(vols)} weeks monitored"), ("ACTIVE DAYS", str(active), TX, f"{100 * active / len(days):.0f}% of days with events"),
        ("UPTIME STREAK", f"{streak}d", SEVC[1] if streak else DM, f"longest {longest}d"), ("PEAK SEVERITY", str(maxc), SEVC[4], f"{bd:%b} {bd.day} · busiest day")]
tiles = "".join(
    f'<rect x="{16 + i * 183}" y="64" width="175" height="62" rx="8" fill="{PN}" stroke="{LN}"/><rect x="{16 + i * 183}" y="64" width="3" height="62" rx="1.5" fill="{col}"/>'
    f'<text x="{32 + i * 183}" y="84" font-size="10" font-weight="700" letter-spacing="1.4" fill="{DM}">{k}</text>'
    f'<text x="{32 + i * 183}" y="106" font-size="24" font-weight="700" fill="{col}" font-family="{MONO}">{v}</text>'
    f'<text x="{32 + i * 183}" y="120" font-size="10" fill="{DM}">{esc(sub)}</text>' for i, (k, v, col, sub) in enumerate(kpis))

TX0, TX1, TY0, TY1 = 34, 480, 168, 318
px = lambda i: TX0 + 8 + i * (TX1 - TX0 - 16) / max(len(vols) - 1, 1)
py = lambda v: TY1 - (v / vm) * (TY1 - TY0 - 10)
pts = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in enumerate(vols))
crit = [i for i, w in enumerate(wk) if max(w) >= high_min]  # weeks that contain a critical day
timeline = (f'<g stroke="{LN}" stroke-dasharray="2 4">' + "".join(f'<line x1="{TX0}" x2="{TX1}" y1="{TY0 + k * (TY1 - TY0) / 3:.0f}" y2="{TY0 + k * (TY1 - TY0) / 3:.0f}"/>' for k in range(4)) + '</g>'
            f'<polygon class="ar" points="{px(0):.1f},{TY1} {pts} {px(len(vols) - 1):.1f},{TY1}" fill="{CY}" fill-opacity="0.12"/>'
            f'<polyline class="tl" pathLength="1" points="{pts}" fill="none" stroke="{CY}" stroke-width="1.6"/>'
            + '<g class="mk">' + "".join(f'<circle cx="{px(i):.1f}" cy="{py(vols[i]):.1f}" r="4" fill="{SEVC[4]}" stroke="{BG}" stroke-width="1.5"/>' for i in crit) + '</g>'
            f'<text x="{TX0}" y="{TY1 + 14}" font-size="10" fill="{DM}" font-family="{MONO}">{d0:%b %Y}</text><text x="{TX1}" y="{TY1 + 14}" font-size="10" fill="{DM}" text-anchor="end" font-family="{MONO}">{d1:%b %Y}</text>'
            f'<circle cx="{TX1 - 150}" cy="{TY0 - 18}" r="4" fill="{SEVC[4]}"/><text x="{TX1 - 142}" y="{TY0 - 15}" font-size="10" fill="{DM}">critical week</text>'
            f'<line x1="{TX1 - 70}" x2="{TX1 - 56}" y1="{TY0 - 18}" y2="{TY0 - 18}" stroke="{CY}" stroke-width="2"/><text x="{TX1 - 51}" y="{TY0 - 15}" font-size="10" fill="{DM}">events/wk</text>')

gx, gy, gr = 624, 268, 78
ang = math.radians(180 + 180 * frac)
gauge = ("".join(f'<path d="{arc(gx, gy, gr, 180 + i * 45, 180 + (i + 1) * 45 - 2)}" fill="none" stroke="{c}" stroke-width="12" stroke-opacity="{1 if i == zi else .3}"/>' for i, c in enumerate(ACT))
         + f'<g class="nd"><line x1="{gx}" y1="{gy}" x2="{gx + (gr - 18) * math.cos(ang):.1f}" y2="{gy + (gr - 18) * math.sin(ang):.1f}" stroke="{TX}" stroke-width="2.5" stroke-linecap="round"/></g><circle cx="{gx}" cy="{gy}" r="5" fill="{TX}"/>'
         + f'<text x="{gx}" y="{gy + 28}" font-size="17" font-weight="700" text-anchor="middle" fill="{zc}">{ACTN[zi]}</text>'
         + f'<text x="{gx}" y="{gy + 44}" font-size="10" text-anchor="middle" fill="{DM}">{f"4W events {chg:+.0f}% vs prior 4W" if chg is not None else "first 4 weeks of data"}</text>')

cx0, cy0, rr = 78, 432, 38
circ = 2 * math.pi * rr
tot_sev = sum(counts.values())
off, donut = 0, f'<circle cx="{cx0}" cy="{cy0}" r="{rr}" fill="none" stroke="{LN}" stroke-width="12"/>'
for k in (4, 3, 2, 1):
    ln = circ * counts[k] / (tot_sev or 1)
    donut += f'<circle cx="{cx0}" cy="{cy0}" r="{rr}" fill="none" stroke="{SEVC[k]}" stroke-width="12" stroke-dasharray="{ln:.1f} {circ - ln:.1f}" stroke-dashoffset="{-off:.1f}" transform="rotate(-90 {cx0} {cy0})"/>'
    off += ln
donut += f'<text x="{cx0}" y="{cy0 + 6}" font-size="17" font-weight="700" text-anchor="middle" fill="{TX}" font-family="{MONO}">{tot_sev}</text><text x="{cx0}" y="{cy0 + 18}" font-size="9" text-anchor="middle" fill="{DM}">alert days</text>'
legend = "".join(f'<rect x="136" y="{404 + i * 18}" width="8" height="8" rx="2" fill="{SEVC[k]}"/><text x="150" y="{412 + i * 18}" font-size="10" fill="{DM}">{SEVN[k]}</text><text x="236" y="{412 + i * 18}" font-size="10" fill="{TX}" text-anchor="end" font-family="{MONO}">{counts[k]}</text>' for i, k in enumerate((4, 3, 2, 1)))

wbars = "".join(f'<text x="280" y="{384 + i * 15}" font-size="10" fill="{DM}">{n}</text><rect x="312" y="{377 + i * 15}" width="140" height="7" rx="2" fill="{LN}"/><rect x="312" y="{377 + i * 15}" width="{140 * v / wmax:.0f}" height="7" rx="2" fill="{SEVC[4] if v == wmax else CY}"/><text x="488" y="{384 + i * 15}" font-size="10" fill="{TX}" text-anchor="end" font-family="{MONO}">{v:,}</text>' for i, (n, v) in enumerate(zip(WD, wd)))

assets = f'<text x="528" y="392" font-size="10" fill="{DM}" letter-spacing="1">ASSET</text><line x1="528" x2="728" y1="398" y2="398" stroke="{LN}"/>'
for i, r in enumerate(ranked[:2]):
    pushed = date.fromisoformat(r["pushed_at"][:10])
    nm = r["name"] if len(r["name"]) <= 14 else r["name"][:13] + "…"
    label, col = status(r)
    assets += (f'<rect x="528" y="{410 + i * 36}" width="56" height="14" rx="7" fill="{col}" fill-opacity="0.15"/><text x="556" y="{420 + i * 36}" font-size="9" font-weight="700" fill="{col}" text-anchor="middle">{label}</text>'
               f'<text x="592" y="{421 + i * 36}" font-size="11" font-weight="700" fill="{TX}" font-family="{MONO}">{esc(nm)}</text>'
               f'<text x="528" y="{440 + i * 36}" font-size="10" fill="{DM}">{esc(r["language"] or "no language")} · {r["stargazers_count"]} stars · seen {pushed:%b} {pushed.day}</text>')
if len(ranked) < 2:
    assets += f'<text x="528" y="{412 + 36 * len(ranked) + (30 if ranked else 0)}" font-size="10" fill="{DM}">— no further assets enrolled</text>'

write("assets/dashboard.svg", f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 530" width="760" height="530" role="img" aria-label="SOC dashboard for {esc(USER)}: {total} contributions, {active} active days, activity {ACTN[zi].lower()}" font-family="{SANS}">
<style>.nd{{transform-origin:{gx}px {gy}px;animation:sw 1.1s cubic-bezier(.2,.8,.2,1) both}}@keyframes sw{{from{{transform:rotate(-{180 * frac:.1f}deg)}}}}.tl{{stroke-dasharray:1;animation:draw 1.2s ease-out both}}@keyframes draw{{from{{stroke-dashoffset:1}}to{{stroke-dashoffset:0}}}}.ar{{animation:fade .8s ease-out .6s both}}.mk{{animation:fade .4s ease-out 1.1s both}}{FADE}@media (prefers-reduced-motion:reduce){{.nd,.tl,.ar,.mk{{animation:none}}}}</style>
<rect x="1" y="1" width="758" height="528" rx="14" fill="{BG}" stroke="{LN}"/>
<path d="M30 16l11 4v8c0 7-5 11-11 13-6-2-11-6-11-13v-8z" fill="none" stroke="{CY}" stroke-width="1.8"/><path d="M25 28l4 4 7-8" fill="none" stroke="{CY}" stroke-width="1.8"/>
<text x="54" y="29" font-size="14" font-weight="700" fill="{TX}" letter-spacing="1">SOC <tspan fill="{DM}">//</tspan> {esc(USER.upper())}</text>
<text x="54" y="44" font-size="10" fill="{DM}">{esc(TAGLINE)} · monitoring window {d0:%b %Y} to {d1:%b %Y}</text>
<circle cx="520" cy="30" r="7" fill="{SEVC[1]}" fill-opacity="0.16"/><circle cx="520" cy="30" r="3.5" fill="{SEVC[1]}"/><text x="532" y="34" font-size="10" font-weight="700" fill="{SEVC[1]}" letter-spacing="1">ONLINE</text>
<rect x="590" y="19" width="154" height="22" rx="11" fill="{zc}" fill-opacity="0.14" stroke="{zc}" stroke-opacity="0.5"/><text x="667" y="34" font-size="10" font-weight="700" fill="{zc}" text-anchor="middle" letter-spacing="1">ACTIVITY · {ACTN[zi]}</text>
{tiles}
{panel(16, 138, 480, 196, "EVENT TIMELINE · WEEKLY", timeline)}
{panel(504, 138, 240, 196, "ACTIVITY LEVEL", gauge)}
{panel(16, 346, 240, 150, "ALERT SEVERITY · DAYS", donut + legend)}
{panel(264, 346, 240, 150, "EVENTS BY WEEKDAY", wbars)}
{panel(512, 346, 232, 150, "WATCHED ASSETS", assets)}
<rect x="16" y="504" width="728" height="20" rx="6" fill="{PN}" stroke="{LN}"/><text x="28" y="518" font-size="10" fill="{DM}" font-family="{MONO}"><tspan fill="{SEVC[1]}">● ALL SYSTEMS NOMINAL</tspan>  ·  last sync {now:%b} {now.day} {now.year}  ·  next sync ≤ 3h  ·  github actions</text>
</svg>
''')

# ---------- calendar: every day coloured by severity, sweeping in left to right ----------
SW = 11
cal = "".join(
    f'<rect class="h" {sweep(c, r)} x="{38 + c * (SW + 2)}" y="{62 + r * (SW + 2)}" width="{SW}" height="{SW}" rx="2.5" fill="{LN if sev(n) == 0 else SEVC[sev(n)]}" fill-opacity="{0.18 if sev(n) == 0 else 0.95 if sev(n) > 1 else 0.7}"/>'
    for r, c, d, lvl, n in days)
wdl = "".join(f'<text x="14" y="{71 + i * 13}" font-size="10" fill="{DM}">{WD[i]}</text>' for i in (1, 3, 5))
cleg = "".join(f'<rect x="{360 + i * 78}" y="172" width="9" height="9" rx="2" fill="{SEVC[k]}"/><text x="{374 + i * 78}" y="180" font-size="10" fill="{DM}">{SEVN[k]}</text>' for i, k in enumerate((1, 2, 3, 4)))
write("assets/calendar.svg", f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 196" width="760" height="196" role="img" aria-label="Alert calendar for {esc(USER)}: {counts[4]} critical, {counts[3]} high, {counts[2]} medium, {counts[1]} low days" font-family="{SANS}">
<style>{HEATMAP_CSS}</style>
<rect x="1" y="1" width="758" height="194" rx="14" fill="{BG}" stroke="{LN}"/>
<text x="20" y="28" font-size="13" font-weight="700" fill="{TX}" letter-spacing="1">ALERT CALENDAR</text><text x="20" y="44" font-size="10" fill="{DM}">One cell per day · colour = severity of that day's event volume</text>
{cal}{wdl}{cleg}</svg>
''')

# ---------- feed: repos as assets ----------
RH = 40
rows = ""
for i, r in enumerate(ranked[:5]):
    y = 76 + i * RH
    pushed = date.fromisoformat(r["pushed_at"][:10])
    label, col = status(r)
    nm = r["name"].upper() if len(r["name"]) <= 24 else r["name"].upper()[:23] + "…"
    rows += (f'<rect x="20" y="{y}" width="66" height="18" rx="9" fill="{col}" fill-opacity="0.15"/><text x="53" y="{y + 13}" font-size="9" font-weight="700" fill="{col}" text-anchor="middle">{label}</text>'
             f'<text x="110" y="{y + 14}" font-size="13" font-weight="700" fill="{TX}" font-family="{MONO}">{esc(nm)}</text>'
             f'<text x="360" y="{y + 14}" font-size="12" fill="{TX}">{esc(r["language"] or "—")}</text>'
             f'<text x="480" y="{y + 14}" font-size="12" fill="{DM}" font-family="{MONO}">{r["stargazers_count"]}</text>'
             f'<text x="740" y="{y + 14}" font-size="11" fill="{DM}" text-anchor="end" font-family="{MONO}">{pushed:%b} {pushed.day}</text>'
             f'<line x1="16" x2="744" y1="{y + 28}" y2="{y + 28}" stroke="{LN}"/>')
n_ = min(len(ranked), 5)
if n_ < 3:
    rows += f'<text x="110" y="{76 + n_ * RH + 14}" font-size="12" fill="{DM}">— no further assets enrolled</text>'
    n_ += 1
FH = 76 + n_ * RH + 14
write("assets/feed.svg", f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 {FH}" width="760" height="{FH}" role="img" aria-label="Asset feed: {len(ranked)} public repos" font-family="{SANS}">
<rect x="1" y="1" width="758" height="{FH - 2}" rx="14" fill="{BG}" stroke="{LN}"/>
<text x="20" y="30" font-size="13" font-weight="700" fill="{TX}" letter-spacing="1">ASSET FEED</text>
<g font-size="10" font-weight="700" letter-spacing="1.4" fill="{DM}"><text x="20" y="56">STATUS</text><text x="110" y="56">ASSET</text><text x="360" y="56">LANGUAGE</text><text x="480" y="56">STARS</text><text x="740" y="56" text-anchor="end">LAST SEEN</text></g>
<line x1="16" x2="744" y1="64" y2="64" stroke="{LN}"/>
{rows}</svg>
''')

A = "./themes/soc/assets"
write("snippet.md", f'''<p align="center">
  <img src="{A}/dashboard.svg" alt="SOC dashboard with events, activity level and alert severity for {esc(USER)}" width="100%" />
</p>

<br/>

<p align="center">
  <img src="{A}/calendar.svg" alt="Alert calendar coloured by severity" width="100%" />
</p>

<br/>

<p align="center">
  <a href="https://github.com/{esc(USER)}?tab=repositories"><img src="{A}/feed.svg" alt="Asset feed of {esc(USER)}'s repositories" width="100%" /></a>
</p>
''')
print(f"{USER}: total={total} active={active} streak={streak} weeks={len(vols)} activity={ACTN[zi]} repos={len(repos)} langs={len(lang_rows)}")
