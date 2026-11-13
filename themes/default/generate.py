"""Default theme (trainer card): writes assets/*.svg and snippet.md into this folder.

snippet.md is the paste-ready README for the repo root. Run: PROFILE_USER=you python themes/default/generate.py
"""
import math, sys, textwrap
from html import escape as esc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from profile_data import *  # shared GitHub data: USER, days, total, streak, user, repos, langs, ...
from isocity import iso_city, CSS as CITY_CSS


# ---------- shared style ----------
RIM = '<linearGradient id="rim" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#99f6e4"/><stop offset="0.5" stop-color="#0f766e"/><stop offset="1" stop-color="#5eead4"/></linearGradient>'
PAL = {  # contribution level: (top, left, right)
    0: ("#15302e", "#0f2321", "#0b1a19"),
    1: ("#0f766e", "#0b5a54", "#08433f"),
    2: ("#14b8a6", "#0f8f82", "#0b6b61"),
    3: ("#2dd4bf", "#22a898", "#187d71"),
    4: ("#99f6e4", "#5fc4b2", "#3f9485"),
}
FALLBACK = ["#2dd4bf", "#14b8a6", "#5eead4", "#0f766e", "#99f6e4"]


def box(x, y, w, h, inner):
    return (f'<g transform="translate({x},{y})"><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="16" fill="url(#rim)"/>'
            f'<rect x="3" y="3" width="{w-6}" height="{h-6}" rx="14" fill="#0d1b1a"/>{inner}</g>')


# ---------- glass city ----------
HIGH = ("#fde68a", "#f59e0b", "#b45309")  # busy days stand out from the teal ramp
shapes, W, H, ox, oy = iso_city(days, maxc, PAL, HIGH, high_min)
legend = "".join(f'<rect x="{W-220+i*18:.0f}" y="{H-62:.0f}" width="12" height="12" rx="3" fill="{PAL[i][0]}"/>' for i in range(5))
legend += f'<rect x="{W-92:.0f}" y="{H-62:.0f}" width="12" height="12" rx="3" fill="{HIGH[1]}"/><text x="{W-74:.0f}" y="{H-52:.0f}" font-size="11" fill="#94a3b8">Peak</text>'
write("assets/city.svg", f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" height="{H:.0f}" role="img" aria-label="Isometric 3D contribution city for {esc(USER)}: {total} contributions, {active} active days">
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0a0f1a"/><stop offset="1" stop-color="#070b12"/></linearGradient>
<radialGradient id="gb" cx="0.12" cy="0" r="0.55"><stop offset="0" stop-color="#3b82f6" stop-opacity="0.45"/><stop offset="1" stop-color="#3b82f6" stop-opacity="0"/></radialGradient>
<radialGradient id="gg" cx="0.9" cy="0.25" r="0.5"><stop offset="0" stop-color="#22c55e" stop-opacity="0.28"/><stop offset="1" stop-color="#22c55e" stop-opacity="0"/></radialGradient>
<radialGradient id="gp" cx="0.55" cy="1" r="0.5"><stop offset="0" stop-color="#a855f7" stop-opacity="0.3"/><stop offset="1" stop-color="#a855f7" stop-opacity="0"/></radialGradient>
</defs>
<style>{CITY_CSS}</style>
<rect x="0.5" y="0.5" width="{W-1:.0f}" height="{H-1:.0f}" rx="22" fill="url(#bg)"/>
<rect x="0.5" y="0.5" width="{W-1:.0f}" height="{H-1:.0f}" rx="22" fill="url(#gb)"/>
<rect x="0.5" y="0.5" width="{W-1:.0f}" height="{H-1:.0f}" rx="22" fill="url(#gg)"/>
<rect x="0.5" y="0.5" width="{W-1:.0f}" height="{H-1:.0f}" rx="22" fill="url(#gp)"/>
<rect x="0.5" y="0.5" width="{W-1:.0f}" height="{H-1:.0f}" rx="22" fill="none" stroke="#3b6fb6" stroke-opacity="0.7"/>
<rect x="22" y="22" width="{W-44:.0f}" height="{H-44:.0f}" rx="18" fill="#ffffff" fill-opacity="0.025" stroke="#60a5fa" stroke-opacity="0.3"/>
<g transform="translate({ox:.1f},{oy:.1f})">
{chr(10).join(shapes)}
</g>
<g font-family="{SANS}">
<text x="44" y="68" font-size="30" font-weight="800" fill="#f8fafc">Contribution City</text>
<text x="44" y="94" font-size="14" font-weight="600" fill="#94a3b8">{total:,} contributions in the last year</text>
<text x="44" y="122" font-size="12" fill="#94a3b8">{active} active days · busiest day {best[4]} ({bd:%b} {bd.day})</text>
<text x="{W-226:.0f}" y="{H-52:.0f}" font-size="11" fill="#94a3b8" text-anchor="end">Less</text>
{legend}
<text x="{W-124:.0f}" y="{H-52:.0f}" font-size="11" fill="#94a3b8">More</text>
<text x="44" y="{H-34:.0f}" font-size="11" font-family="{MONO}" fill="#64748b">@{esc(USER)} · {d0:%b %Y} to {d1:%b %Y}</text>
</g>
</svg>
''')

# ---------- trainer card (rank, move names and colour follow the stats) ----------
RANKS = [  # (min total contributions, title, rim gradient stops, accent)
    (0, "Rookie Trainer", ("#e2e8f0", "#64748b", "#94a3b8"), "#cbd5e1"),
    (100, "Basic Trainer", ("#99f6e4", "#0f766e", "#5eead4"), "#5eead4"),
    (500, "Ace Trainer", ("#a5f3fc", "#0891b2", "#67e8f9"), "#67e8f9"),
    (1500, "Elite Trainer", ("#e9d5ff", "#7e22ce", "#c084fc"), "#c084fc"),
    (3000, "Champion", ("#fde68a", "#b45309", "#fbbf24"), "#fbbf24"),
]
ri = max(i for i, r in enumerate(RANKS) if total >= r[0])
_, rank_name, rim_stops, ACC = RANKS[ri]
next_txt = f"Next rank · {RANKS[ri + 1][0]:,}" if ri + 1 < len(RANKS) else "Max rank"


moves = [
    (pick(best[4], [10, 25], ["Spark Commit", "Commit Surge", "Commit Storm"]), str(best[4]), f"Busiest day: {bd:%b} {bd.day}, {bd:%Y}."),
    (pick(active, [30, 100], ["Warm Up", "Daily Grind", "Iron Routine"]), str(active), "Active days in the last year."),
    (pick(streak, [3, 7], ["Streak Starter", "Streak Keeper", "Streak Master"]), str(streak), f"Current streak in days. Total: {total:,} commits."),
]
mood_t = mood.upper()
mood_w = 24 + 6.9 * len(mood_t)  # pill width, right edge aligned with the art box at x=332
mood_l = 332 - mood_w
hp_x = 332 - 15.6 * len(str(total)) - 8  # "HP" label sits just left of the number
rows = ""
for i, (name, dmg, desc) in enumerate(moves):
    y = 334 + i * 56
    rows += f'''<circle cx="44" cy="{y-5}" r="9" fill="#12302e" stroke="#2dd4bf"/><circle cx="44" cy="{y-5}" r="3.5" fill="#5eead4"/>
<text x="64" y="{y}" font-size="16" font-weight="700" fill="#f8fafc">{name}</text>
<text x="326" y="{y}" font-size="22" font-weight="800" fill="{ACC}" text-anchor="end">{dmg}</text>
<text x="64" y="{y+17}" font-size="10.5" fill="#94a3b8">{desc}</text>
'''
    if i < 2:
        rows += f'<line x1="28" y1="{y+30}" x2="332" y2="{y+30}" stroke="#134e4a"/>'
card = f'''<defs>
<linearGradient id="rimc" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{rim_stops[0]}"/><stop offset="0.5" stop-color="{rim_stops[1]}"/><stop offset="1" stop-color="{rim_stops[2]}"/></linearGradient>
<linearGradient id="art" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#134e4a"/><stop offset="1" stop-color="#0b1f1e"/></linearGradient>
<linearGradient id="shine" x1="0" y1="0" x2="1" y2="1"><stop offset="0.35" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="#fff" stop-opacity="0.07"/><stop offset="0.65" stop-color="#fff" stop-opacity="0"/></linearGradient>
<clipPath id="av"><circle cx="180" cy="179" r="70"/></clipPath>
</defs>
<rect x="4" y="4" width="352" height="532" rx="22" fill="url(#rimc)"/>
<rect x="14" y="14" width="332" height="512" rx="16" fill="#0d1b1a"/>
<text x="28" y="38" font-size="10" font-weight="700" letter-spacing="2" fill="#94a3b8">{rank_name.upper()}</text>
<rect x="{mood_l:.0f}" y="25" width="{mood_w:.0f}" height="18" rx="9" fill="none" stroke="{ACC}" stroke-opacity="0.55"/>
<circle cx="{mood_l+11:.0f}" cy="34" r="3" fill="{ACC}"/>
<text x="{mood_l+19:.0f}" y="37.5" font-size="9.5" font-weight="700" letter-spacing="1.2" fill="{ACC}">{mood_t}</text>
<text x="28" y="68" font-size="22" font-weight="800" fill="#f8fafc">{esc(USER)}</text>
<text x="{hp_x:.0f}" y="68" font-size="11" font-weight="700" fill="#94a3b8" text-anchor="end">HP</text>
<text x="332" y="68" font-size="26" font-weight="800" fill="{ACC}" text-anchor="end">{total}</text>
<rect x="28" y="84" width="304" height="190" rx="10" fill="url(#art)" stroke="#2dd4bf" stroke-opacity="0.6"/>
<circle cx="180" cy="179" r="78" fill="none" stroke="#2dd4bf" stroke-opacity="0.35" stroke-width="2"/>
<image href="data:image/jpeg;base64,{avatar()}" x="110" y="109" width="140" height="140" clip-path="url(#av)" preserveAspectRatio="xMidYMid slice"/>
<circle cx="180" cy="179" r="70" fill="none" stroke="url(#rimc)" stroke-width="3"/>
<rect x="28" y="284" width="304" height="20" rx="4" fill="#12302e"/>
<text x="180" y="298" font-size="10.5" font-style="italic" fill="#cbd5e1" text-anchor="middle">{esc(TAGLINE)} · LV {active}</text>
{rows}
<line x1="28" y1="480" x2="332" y2="480" stroke="#2dd4bf" stroke-opacity="0.5"/>
<text x="28" y="498" font-size="10.5" fill="#94a3b8">weakness  <tspan fill="#f8fafc">{esc(CFG.get("weakness", "none found"))}</tspan></text>
<text x="332" y="498" font-size="10.5" fill="#94a3b8" text-anchor="end">retreat  <tspan fill="#f8fafc">0</tspan></text>
<text x="28" y="516" font-size="10" fill="#64748b">Repos {user["public_repos"]} · Followers {user["followers"]} · Stars {stars}</text>
<text x="332" y="516" font-size="10" fill="#64748b" text-anchor="end">{next_txt}</text>
<rect x="4" y="4" width="352" height="532" rx="22" fill="url(#shine)"/>
'''

# ---------- right column: stats, streak, languages ----------
tiles = [("Contributions", f"{total:,}"), ("Active days", str(active)),
         ("Public repos", str(user["public_repos"])), ("Followers", str(user["followers"])),
         ("Stars earned", str(stars)), ("Joined", f"{joined:%b %Y}")]
tile_svg = ""
for n, (label, val) in enumerate(tiles):
    x, y = 22 + (n % 2) * 174, 52 + (n // 2) * 38
    tile_svg += (f'<rect x="{x}" y="{y}" width="162" height="30" rx="9" fill="#12302e" stroke="#134e4a"/>'
                 f'<rect x="{x+1}" y="{y+8}" width="3" height="14" rx="1.5" fill="#2dd4bf"/>'
                 f'<text x="{x+14}" y="{y+19.5}" font-size="11" fill="#94a3b8">{label}</text>'
                 f'<text x="{x+150}" y="{y+20}" font-size="14" font-weight="800" fill="{ACC}" text-anchor="end">{val}</text>')
stats_box = box(380, 0, 380, 172, f'<text x="22" y="32" font-size="15" font-weight="800" fill="#f8fafc">{esc(USER)} · Stats</text>{tile_svg}')

circ = 2 * math.pi * 30
ring = circ * min(1, streak / max(longest, 1))
streak_box = box(380, 184, 380, 172, f'''
<line x1="127" y1="26" x2="127" y2="146" stroke="#134e4a"/><line x1="253" y1="26" x2="253" y2="146" stroke="#134e4a"/>
<text x="63" y="84" font-size="28" font-weight="800" fill="{ACC}" text-anchor="middle">{total:,}</text>
<text x="63" y="112" font-size="11" fill="#cbd5e1" text-anchor="middle">Total Contributions</text>
<text x="63" y="130" font-size="10" fill="#94a3b8" text-anchor="middle">{d0:%b} {d0.year} - Present</text>
<circle cx="190" cy="68" r="30" fill="none" stroke="#134e4a" stroke-width="5"/>
<circle cx="190" cy="68" r="30" fill="none" stroke="{ACC}" stroke-width="5" stroke-linecap="round" stroke-dasharray="{ring:.1f} {circ:.1f}" transform="rotate(-90 190 68)"/>
<text x="190" y="77" font-size="26" font-weight="800" fill="#f8fafc" text-anchor="middle">{streak}</text>
<text x="190" y="120" font-size="11" font-weight="700" fill="{ACC}" text-anchor="middle">Current Streak</text>
<text x="190" y="136" font-size="10" fill="#94a3b8" text-anchor="middle">{cur_range}</text>
<text x="317" y="84" font-size="28" font-weight="800" fill="{ACC}" text-anchor="middle">{longest}</text>
<text x="317" y="112" font-size="11" fill="#cbd5e1" text-anchor="middle">Longest Streak</text>
<text x="317" y="130" font-size="10" fill="#94a3b8" text-anchor="middle">{long_range}</text>''')

head = '<text x="22" y="34" font-size="10" font-weight="700" letter-spacing="2" fill="#94a3b8">LANGUAGE STACK</text>'
if lang_total:
    MAXROWS = 5  # more than that: show the top 4 and fold the rest into "+N more"
    shown = lang_rows if len(lang_rows) <= MAXROWS else lang_rows[:MAXROWS - 1]
    body = ""
    for i, (name, b) in enumerate(shown):
        y = 52 + i * 22
        pct = 100 * b / lang_total
        col = LANG_COLORS.get(name, FALLBACK[i % len(FALLBACK)])
        label = name if len(name) <= 13 else name[:12] + "…"
        body += (f'<text x="22" y="{y+8}" font-size="11" fill="#cbd5e1">{esc(label)}</text>'
                 f'<rect x="122" y="{y}" width="186" height="8" rx="4" fill="#12302e"/>'
                 f'<rect x="122" y="{y}" width="{max(4, 186*pct/100):.0f}" height="8" rx="4" fill="{col}"/>'
                 f'<text x="358" y="{y+8}" font-size="10.5" fill="#94a3b8" text-anchor="end">{pct:.0f}%</text>')
    if len(lang_rows) > MAXROWS:
        body += f'<text x="22" y="{52+(MAXROWS-1)*22+8}" font-size="11" fill="#64748b">+{len(lang_rows)-(MAXROWS-1)} more</text>'
else:
    bars = "".join(f'<rect x="22" y="{y}" width="64" height="8" rx="4" fill="#134e4a"/><rect x="98" y="{y}" width="260" height="8" rx="4" fill="#12302e"/>' for y in (112, 134, 156))
    body = ('<text x="22" y="64" font-size="18" font-weight="800" fill="#94a3b8">No public language data yet</text>'
            f'<text x="22" y="86" font-size="11.5" fill="#64748b">Appears once a public repo has code.</text>{bars}')
langs_box = box(380, 368, 380, 172, head + body)

write("assets/dashboard.svg", f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 540" width="760" height="540" role="img" aria-label="{esc(USER)} {rank_name}: {total} contributions, {active} active days, {streak} day streak">
<defs>{RIM}</defs>
<g font-family="{SANS}">
{card}
{stats_box}
{streak_box}
{langs_box}
</g>
</svg>
''')


# ---------- projects: favourites first, then by stars; up to 6 cards, "+N more" beyond that ----------
STAR = "0,-7 2,-2.4 7,-2.2 3.1,0.9 4.3,5.7 0,3 -4.3,5.7 -3.1,0.9 -7,-2.2 -2,-2.4"


def project(x, y, i, item):
    head = f'<g transform="translate({x},{y})">'
    if item is None:  # empty slot
        return head + f'''<rect x="1" y="1" width="238" height="168" rx="16" fill="#0b1514" stroke="#134e4a" stroke-width="2" stroke-dasharray="6 5"/>
<text x="20" y="32" font-size="10" font-weight="700" letter-spacing="2" fill="#94a3b8">PROJECT {i:02d}</text>
<text x="20" y="62" font-size="19" font-weight="800" fill="#94a3b8">Next project</text>
<text x="20" y="88" font-size="12" fill="#94a3b8">Building in the open.</text>
<text x="20" y="106" font-size="12" fill="#94a3b8">Coming soon.</text>
<line x1="20" y1="124" x2="220" y2="124" stroke="#134e4a"/>
<circle cx="26" cy="144" r="6" fill="none" stroke="#134e4a"/><circle cx="26" cy="144" r="2.5" fill="#134e4a"/>
<text x="42" y="148" font-size="11" fill="#64748b">Empty slot</text>
</g>'''
    r, fav = item
    name = r["name"] if len(r["name"]) <= 17 else r["name"][:16] + "…"
    desc = textwrap.wrap(r["description"] or "No description yet.", 30)
    d1_, d2_ = (desc + ["", ""])[:2]
    if len(desc) > 2:
        d2_ = d2_[:28] + "…"
    lc = LANG_COLORS.get(r["language"], "#2dd4bf") if r["language"] else "#64748b"
    foot = (f'<circle cx="26" cy="144" r="5" fill="{lc}"/><text x="38" y="148" font-size="11" fill="#cbd5e1">{esc(r["language"] or "Public")}</text>'
            f'<polygon transform="translate(188,144) scale(0.8)" points="{STAR}" fill="#94a3b8"/>'
            f'<text x="220" y="148" font-size="11" fill="#cbd5e1" text-anchor="end">{r["stargazers_count"]}</text>')
    badge =(f'<polygon transform="translate(222,28)" points="{STAR}" fill="{ACC}"/>'
             f'<text x="212" y="32" font-size="9" font-weight="700" letter-spacing="1.5" fill="{ACC}" text-anchor="end">FEATURED</text>') if fav else ""
    return head + f'''<rect x="1" y="1" width="238" height="168" rx="16" fill="url(#rim)"/><rect x="3" y="3" width="234" height="164" rx="14" fill="#0d1b1a"/>
<text x="20" y="32" font-size="10" font-weight="700" letter-spacing="2" fill="#94a3b8">PROJECT {i:02d}</text>{badge}
<text x="20" y="62" font-size="19" font-weight="800" fill="#f8fafc">{esc(name)}</text>
<text x="20" y="88" font-size="12" fill="#94a3b8">{esc(d1_)}</text>
<text x="20" y="106" font-size="12" fill="#94a3b8">{esc(d2_)}</text>
<line x1="20" y1="124" x2="220" y2="124" stroke="#134e4a"/>
{foot}
</g>'''


MAXP = 5  # only the top 5 are shown
slots = [(r, is_fav(r)) for r in ranked[:MAXP]]
while len(slots) < 3:
    slots.append(None)
nrows = math.ceil(len(slots) / 3)
PH = nrows * 170 + (nrows - 1) * 16
# a short last row is centred instead of left-aligned
xoff = lambda k: (k % 3) * 260 + (3 - min(3, len(slots) - (k // 3) * 3)) * 130
cards = "\n".join(project(xoff(k), (k // 3) * 186, k + 1, s) for k, s in enumerate(slots))
write("assets/projects.svg", f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 {PH}" width="760" height="{PH}" role="img" aria-label="Projects: {len(ranked)} public, {sum(1 for r in ranked if is_fav(r))} featured">
<defs>{RIM}</defs>
<g font-family="{SANS}">
{cards}
</g>
</svg>
''')

# ---------- footer: identity + focus + rank on the left, refresh status on the right (date only: at most one commit a day) ----------
chips, cx_ = "", 92
for label, col in [(f, "#2dd4bf") for f in FOCUS] + [(rank_name, ACC)]:
    t = label.upper()
    w = 22 + 7.0 * len(t)
    chips += (f'<rect x="{cx_:.0f}" y="52" width="{w:.0f}" height="20" rx="10" fill="none" stroke="{col}" stroke-opacity="0.55"/>'
              f'<text x="{cx_+w/2:.0f}" y="65.5" font-size="9.5" font-weight="700" letter-spacing="1.2" fill="{col if col == ACC else "#cbd5e1"}" text-anchor="middle">{esc(t)}</text>')
    cx_ += w + 8
write("assets/footer.svg", f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 124" width="760" height="124" role="img" aria-label="{esc(USER)} · {esc(TAGLINE)} · {rank_name} · last updated {now:%b} {now.day}, {now.year}">
<defs>{RIM}
<linearGradient id="rimf" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{rim_stops[0]}"/><stop offset="0.5" stop-color="{rim_stops[1]}"/><stop offset="1" stop-color="{rim_stops[2]}"/></linearGradient>
<clipPath id="fav"><circle cx="52" cy="50" r="22"/></clipPath>
</defs>
<style>
.pulse{{transform-box:fill-box;transform-origin:center;animation:pulse 2.4s ease-out infinite}}
@keyframes pulse{{0%{{opacity:.7;transform:scale(1)}}100%{{opacity:0;transform:scale(2.6)}}}}
@media (prefers-reduced-motion:reduce){{.pulse{{animation:none;opacity:0}}}}
</style>
<rect x="1" y="1" width="758" height="122" rx="16" fill="url(#rim)"/>
<rect x="3" y="3" width="754" height="118" rx="14" fill="#0d1b1a"/>
<circle cx="52" cy="50" r="26" fill="none" stroke="url(#rimf)" stroke-width="2.5"/>
<image href="data:image/jpeg;base64,{avatar()}" x="30" y="28" width="44" height="44" clip-path="url(#fav)" preserveAspectRatio="xMidYMid slice"/>
<g font-family="{SANS}">
<text x="92" y="38" font-size="17" font-weight="800" fill="#f8fafc">{esc(USER)}</text>
{chips}
<text x="732" y="30" font-size="9" font-weight="700" letter-spacing="2" fill="#94a3b8" text-anchor="end">LAST UPDATED</text>
<text x="732" y="54" font-size="19" font-weight="800" fill="{ACC}" text-anchor="end">{now:%b} {now.day}, {now.year}</text>
<circle class="pulse" cx="{732-4.8*28-12:.0f}" cy="68" r="3" fill="{ACC}"/>
<circle cx="{732-4.8*28-12:.0f}" cy="68" r="3" fill="{ACC}"/>
<text x="732" y="72" font-size="10.5" fill="#94a3b8" text-anchor="end">auto-refreshes every 3 hours</text>
<line x1="24" y1="92" x2="736" y2="92" stroke="#134e4a"/>
<text x="24" y="109" font-size="10" fill="#64748b">© {now.year} {esc(USER)}</text>
<text x="736" y="109" font-size="10" fill="#64748b" text-anchor="end">Generated from live GitHub data · GitHub Actions</text>
</g>
</svg>
''')
write("snippet.md", f'''<p align="center">
  <img src="./themes/default/assets/dashboard.svg" alt="Trainer card with stats, streak and language stack for {esc(USER)}" width="100%" />
</p>

<br/>

<p align="center">
  <img src="./themes/default/assets/city.svg" alt="3D contribution graph" width="100%" />
</p>

<br/>

<p align="center">
  <a href="https://github.com/{esc(USER)}?tab=repositories"><img src="./themes/default/assets/projects.svg" alt="Projects by {esc(USER)}" width="100%" /></a>
</p>

<br/>

<p align="center">
  <a href="https://github.com/{esc(USER)}"><img src="./themes/default/assets/footer.svg" alt="{esc(USER)} · {esc(TAGLINE)}" width="100%" /></a>
</p>
''')
print(f"{USER}: total={total} rank={rank_name} active={active} streak={streak} repos={len(repos)} langs={len(lang_rows)}")
