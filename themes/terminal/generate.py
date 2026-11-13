"""Terminal theme: one zsh window per section. Writes assets/*.svg and snippet.md into this folder.

session.svg (whoami, stats, streaks, weekday bars, languages), heatmap.svg (calendar), repos.svg (ls -la), prompt.svg (footer).
snippet.md is the paste-ready README for the repo root. Run: PROFILE_USER=you python themes/terminal/generate.py
"""
import sys
from datetime import date
from html import escape as esc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from profile_data import *  # shared GitHub data: USER, days, total, streak, user, repos, langs, ...
from isocity import HEATMAP_CSS, sweep

BG, BAR, LINE, TXT, DIM, G, AMB, CY = "#0b0f0d", "#161b18", "#1f2823", "#c9d1c8", "#5b6b5f", "#4ade80", "#fbbf24", "#5eead4"
LH = 19  # one text line; sizes are 12 (body) and 10 (secondary), regular weight only


def window(h, title, body, label, css=""):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 {h}" width="760" height="{h}" role="img" aria-label="{esc(label)}" font-family="{MONO}" font-size="12">
<style>text{{white-space:pre}}{css}</style>
<rect x="1" y="1" width="758" height="{h - 2}" rx="10" fill="{BG}" stroke="{LINE}"/>
<path d="M1 11a10 10 0 0 1 10-10h738a10 10 0 0 1 10 10v20H1z" fill="{BAR}"/>
<circle cx="20" cy="16" r="5" fill="#ff5f57"/><circle cx="38" cy="16" r="5" fill="#febc2e"/><circle cx="56" cy="16" r="5" fill="#28c840"/>
<text x="380" y="20" text-anchor="middle" fill="{DIM}" font-size="10">{esc(title)}</text>
{body}</svg>'''


def line(y, parts, x=20):  # parts: [(text, colour)]
    return f'<text x="{x}" y="{y}">' + "".join(f'<tspan fill="{c}">{esc(t)}</tspan>' for t, c in parts) + "</text>"


def prompt(y, cmd="", cursor=False):
    return line(y, [(f"{USER}@github", G), (":", DIM), ("~", CY), ("$ ", DIM), (cmd, TXT)] + ([("█", G)] if cursor else []))  # cursor is a glyph, so it lands right in any font


TITLE = f"{USER}@github: ~/profile — zsh"

# ---------- session ----------
out, y = [], 52


def put(parts, gap=LH):
    global y
    out.append(line(y, parts)); y += gap


def cmd(c):
    global y
    out.append(prompt(y, c)); y += LH


cmd("whoami")
put([(USER, TXT), (f" · {TAGLINE}", DIM)], LH + 8)
if FOCUS:
    cmd("echo $FOCUS")
    put([(" · ".join(FOCUS), CY)], LH + 8)
cmd('git shortlog --since="1 year ago" --summary')
put([(f"{total:>6,}", G), ("  commits across ", DIM), (str(active), TXT), (f" active days · {len(wk)} weeks", DIM)], LH + 8)
cmd("streak --current --longest")
put([("  current  ", DIM), (f"{streak}d", G if streak else DIM), (f"   {cur_range}", DIM)])
put([("  longest  ", DIM), (f"{longest}d", AMB), (f"   {long_range}", DIM)], LH + 8)
cmd("activity --by weekday")
for n, v in zip(WD, wd):
    k = round(20 * v / wmax)
    put([(f"  {n}  ", DIM), ("█" * k, AMB if v == wmax else G), ("░" * (20 - k), LINE), (f"  {v:>5,}", TXT)])
y += 8
cmd("nmap -sV --top-languages")
if lang_total:
    put([("  PORT       STATE  SERVICE       SHARE", DIM)])
    for (name, b), port in zip(lang_rows[:4], ["443", "80", "22", "8080"]):
        put([(f"  {port + '/tcp':<11}", TXT), ("open   ", G), (f"{name[:12]:<14}", CY), (f"{100 * b / lang_total:>3.0f}%", TXT)])
    if len(lang_rows) > 4:
        put([(f"  +{len(lang_rows) - 4} more", DIM)])
else:
    put([("  no open ports", DIM)])
y += 8
out.append(prompt(y, cursor=True)); y += 14
write("assets/session.svg", window(y + 6, TITLE, "".join(out), f"Terminal session for {USER}: {total} contributions, {active} active days, {streak} day streak"))

# ---------- heatmap: contribution calendar, cells sweep in left to right ----------
ncols = max(c[1] for c in days) + 1
CW = min(12.0, (740 - 52) / ncols)
SHADE = {0: "#1c2520", 1: "#2f7d4f", 2: "#3fae6a", 3: "#4ade80", 4: "#4ade80"}
cells = "".join(
    f'<rect class="h" {sweep(c, r)} x="{52 + c * CW:.1f}" y="{76 + r * 14}" width="{CW - 3:.1f}" height="9" rx="1.5" fill="{AMB if n >= high_min else SHADE[lvl]}"/>'
    for r, c, d, lvl, n in days)
seen, months = set(), ""
for r, c, d, lvl, n in days:
    k = d[:7]
    if r == 0 and k not in seen:
        seen.add(k)
        months += f'<text x="{52 + c * CW:.1f}" y="68" fill="{DIM}" font-size="10">{date.fromisoformat(d):%b}</text>'
wdl = "".join(f'<text x="20" y="{84 + i * 14}" fill="{DIM}" font-size="10">{WD[i]}</text>' for i in (1, 3, 5))
legend = [(20, SHADE[0], "none"), (80, SHADE[1], "light"), (140, SHADE[2], "steady"), (210, SHADE[3], "heavy")]
if maxc >= high_min:
    legend.append((278, AMB, f"busy days · peak {maxc} ({bd:%b} {bd.day})"))
leg = "".join(f'<rect x="{x}" y="187" width="9" height="9" rx="1.5" fill="{c}"/><text x="{x + 14}" y="196" fill="{DIM}" font-size="10">{esc(t)}</text>' for x, c, t in legend)
write("assets/heatmap.svg", window(212, TITLE, prompt(50, "git log --graph --calendar") + months + cells + wdl + leg,
                                   f"Contribution calendar for {USER}: {total} contributions, {active} active days", HEATMAP_CSS))

# ---------- repos: ls -la ----------
shown = ranked[:5]
rows = [prompt(50, "ls -la ~/repos"), line(50 + LH, [(f"total {len(ranked)}", DIM)]),
        line(50 + 2 * LH, [(f"{'perms':<12}{'stars':<5}  {'lang':<10} {'pushed':<7} name", DIM)])]
for i, r in enumerate(shown):
    st = r["stargazers_count"]
    pushed = date.fromisoformat(r["pushed_at"][:10])
    fav = is_fav(r)
    desc = r["description"] or ""
    desc = desc if len(desc) <= 38 else desc[:37] + "…"
    rows.append(line(50 + (3 + i) * LH, [
        (f"{'drwxr-xr-x':<12}", DIM), (f"{st:>4}★  ", TXT), (f"{(r['language'] or '—')[:10]:<10} ", CY), (f"{pushed:%b} {pushed.day:>2}  ", DIM),
        (r["name"] + "/", AMB if fav else G), (("  [featured]" if fav else "") + (f"  # {desc}" if desc else ""), AMB if fav else DIM)]))
for i in range(max(0, 2 - len(shown))):  # always show a couple of rows, like the other themes
    rows.append(line(50 + (3 + len(shown) + i) * LH, [(f"{'drwxr-xr-x':<12}{'—':>5}  {'—':<10} {'—':<7}  ", DIM), ("next-project/", DIM), ("  # coming soon", DIM)]))
nrows = max(len(shown), 2)
write("assets/repos.svg", window(50 + (3 + nrows) * LH + 6, f"{USER}@github: ~/repos — zsh", "".join(rows), f"Repositories of {USER}: {len(ranked)} public"))

# ---------- prompt footer ----------
write("assets/prompt.svg", window(96, f"{USER}@github: ~ — zsh",
                                  prompt(50, "date; echo $?") +
                                  line(50 + LH, [(f"{now:%a %b %d %Y}", TXT), (" · exit status ", DIM), ("0", G), (" · auto-refreshes every 3 hours · github actions", DIM)]) +
                                  prompt(50 + 2 * LH + 6, cursor=True),
                                  f"{USER} · {TAGLINE} · last updated {now:%b} {now.day}, {now.year}"))

A = "./themes/terminal/assets"
write("snippet.md", f'''<p align="center">
  <img src="{A}/session.svg" alt="Terminal session with stats, streaks, weekday activity and languages for {esc(USER)}" width="100%" />
</p>

<br/>

<p align="center">
  <img src="{A}/heatmap.svg" alt="Contribution calendar heatmap" width="100%" />
</p>

<br/>

<p align="center">
  <a href="https://github.com/{esc(USER)}?tab=repositories"><img src="{A}/repos.svg" alt="Repositories of {esc(USER)}" width="100%" /></a>
</p>

<br/>

<p align="center">
  <a href="https://github.com/{esc(USER)}"><img src="{A}/prompt.svg" alt="{esc(USER)} · {esc(TAGLINE)}" width="100%" /></a>
</p>
''')
print(f"{USER}: total={total} active={active} streak={streak} weeks={len(wk)} repos={len(repos)} langs={len(lang_rows)}")
