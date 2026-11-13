"""Trading-terminal theme: writes assets/*.svg and snippet.md into this folder.

Weekly candles, volume, order flow, volume skyline, watchlist, status footer.
snippet.md is the paste-ready README for the repo root. Run: PROFILE_USER=you python themes/trading/generate.py
"""
import math, re, sys
from datetime import date
from html import escape as esc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from profile_data import *  # shared GitHub data: USER, days, total, streak, user, repos, langs, ...
from isocity import iso_city, CSS as CITY_CSS


UP, DN, GOLD, BG, PANEL, LINE, DIM, TXT = "#0ecb81", "#f6465d", "#f0b90b", "#0b0e11", "#12161c", "#1e2329", "#848e9c", "#eaecef"
# weekly candles from the real daily counts: open = first day, close = last day, high/low = busiest/quietest day, volume = week total
candles = [(w[0], max(w), min(w), w[-1], sum(w)) for w in wk]
dir_up = chg is None or chg >= 0
dtxt = f"{'▲' if dir_up else '▼'} {chg:+.1f}%" if chg is not None else "▲ new"
dcol = UP if dir_up else DN

# ---------- dashboard: terminal layout (symbol header, OHLC readout, candles + right price axis, volume, side panel, tape) ----------
# the side panel is laid out first; its bottom edge (PB) then sets the chart height so both columns end together
hdr = lambda yy, t, r="": (f'<text x="580" y="{yy}" font-size="9.5" font-weight="700" letter-spacing="2" fill="{DIM}">{t}</text>'
                           + (f'<text x="730" y="{yy}" font-size="8.5" fill="{DIM}" text-anchor="end">{r}</text>' if r else ""))

rows = [("Contributions", f"{total:,}", UP, None), ("Active days", str(active), TXT, None),
        ("Streak", f"{streak}d", UP if streak else DIM, cur_range), ("Longest", f"{longest}d", TXT, long_range),
        ("Repos", str(user["public_repos"]), TXT, None), ("Stars", str(stars), TXT, None),
        ("Followers", str(user["followers"]), TXT, None), ("Joined", f"{joined:%b %Y}", TXT, None)]
py, panel = 122, ""
for k, v, c, sub in rows:
    panel += (f'<text x="580" y="{py}" font-size="11" fill="{DIM}">{k}</text>'
              f'<text x="730" y="{py}" font-size="12.5" font-weight="700" fill="{c}" text-anchor="end" font-family="{MONO}">{v}</text>')
    if sub:
        panel += f'<text x="580" y="{py + 11}" font-size="8.5" fill="{DIM}" font-family="{MONO}">{esc(sub)}</text>'
    py += 31 if sub else 22
    panel += f'<line x1="580" x2="730" y1="{py - 14}" y2="{py - 14}" stroke="{LINE}"/>'

oy = py + 14
panel += hdr(oy, "ORDER FLOW", "by weekday") + "".join(
    f'<text x="580" y="{oy + 20 + i * 15}" font-size="10" fill="{DIM}">{n}</text>'
    f'<rect x="612" y="{oy + 13 + i * 15}" width="84" height="7" rx="2" fill="{LINE}"/>'
    f'<rect x="612" y="{oy + 13 + i * 15}" width="{max(2, 84 * v / wmax):.0f}" height="7" rx="2" fill="{GOLD if v == wmax else UP}" fill-opacity="0.9"/>'
    f'<text x="730" y="{oy + 20 + i * 15}" font-size="10" fill="{TXT}" text-anchor="end" font-family="{MONO}">{v}</text>' for i, (n, v) in enumerate(zip(WD, wd)))

ay = oy + 138
panel += hdr(ay, "ALLOCATION")
if lang_total:
    shown = lang_rows if len(lang_rows) <= 5 else lang_rows[:4]  # more than 5: top 4 and a "+N more" line
    extra = len(lang_rows) - len(shown)
    pal = [UP, GOLD, "#4c9aff", "#a855f7", "#14b8a6"]
    for i, (n, b) in enumerate(shown):
        panel += (f'<text x="580" y="{ay + 22 + i * 17}" font-size="10.5" fill="{DIM}">{esc(n if len(n) <= 9 else n[:8] + "…")}</text>'
                  f'<rect x="632" y="{ay + 15 + i * 17}" width="74" height="7" rx="2" fill="{LINE}"/>'
                  f'<rect x="632" y="{ay + 15 + i * 17}" width="{max(3, 74 * b / lang_total):.0f}" height="7" rx="2" fill="{LANG_COLORS.get(n, pal[i])}"/>'
                  f'<text x="730" y="{ay + 22 + i * 17}" font-size="10" fill="{TXT}" text-anchor="end" font-family="{MONO}">{100 * b / lang_total:.0f}%</text>')
    if extra:
        panel += f'<text x="580" y="{ay + 22 + len(shown) * 17}" font-size="10" fill="{DIM}">+{extra} more</text>'
    last_y = ay + 22 + (len(shown) - (0 if extra else 1)) * 17
else:
    panel += f'<text x="580" y="{ay + 22}" font-size="11" fill="{DIM}">No public language data yet</text>'
    last_y = ay + 22
PB = last_y + 18  # panel bottom edge

N, CX0, CX1, CY0 = len(candles), 20, 504, 100  # CX1 leaves room for the axis labels, then the last-price tag, before the side panel at x=566
VY1 = PB - 80
VY0 = VY1 - 82
CY1 = VY0 - 18
TY = PB + 14  # tape top
HH = TY + 44  # svg height
hi_p = max(max(c[1] for c in candles), 1)
lo_p = min(c[2] for c in candles)
y = lambda p: CY1 - math.sqrt(p / hi_p) * (CY1 - CY0)  # sqrt scale: one 50-commit day would flatten every other week
step = (CX1 - CX0) / N
xc = lambda i: CX0 + i * step + step / 2
vmax = max(max(vols), 1)
week_first = {}
for c in days:
    week_first.setdefault(c[1], c[2])
wdate = [date.fromisoformat(week_first[k]) for k in sorted(week_first)]
mticks = [(i, d) for i, d in enumerate(wdate) if i and d.month != wdate[i - 1].month]

grid = "".join(f'<line x1="{CX0}" x2="{CX1}" y1="{CY0 + k * (CY1 - CY0) / 4:.0f}" y2="{CY0 + k * (CY1 - CY0) / 4:.0f}" stroke="{LINE}" stroke-dasharray="2 4"/>' for k in range(5))
grid += "".join(f'<line x1="{xc(i):.0f}" x2="{xc(i):.0f}" y1="{CY0}" y2="{VY1}" stroke="{LINE}" stroke-dasharray="2 4"/>' for i, _ in mticks)
ylabels = "".join(f'<text x="{CX1 + 7}" y="{CY0 + k * (CY1 - CY0) / 4 + 3:.0f}" font-size="9" fill="{DIM}" font-family="{MONO}">{hi_p * ((4 - k) / 4) ** 2:.0f}</text>' for k in range(5))  # inverse of the sqrt scale
xlabels = "".join(f'<text x="{xc(i):.0f}" y="{VY1 + 15}" font-size="9" fill="{DIM}" text-anchor="middle" font-family="{MONO}">{d:%Y}</text>' if d.month == 1
                  else f'<text x="{xc(i):.0f}" y="{VY1 + 15}" font-size="9" fill="{DIM}" text-anchor="middle" font-family="{MONO}">{d:%b}</text>' for i, d in mticks)
bars = ""
for i, (o, hi, lo, c, v) in enumerate(candles):
    col = UP if c > o else DN if c < o else DIM
    top, bot = y(max(o, c)), y(min(o, c))
    bw = max(step * 0.62, 1.5)
    dl = f'style="animation-delay:{i * 14}ms"'  # candles and volume grow in left to right
    bars += (f'<g class="c" {dl}><line x1="{xc(i):.1f}" x2="{xc(i):.1f}" y1="{y(hi):.1f}" y2="{y(lo):.1f}" stroke="{col}"/>'
             f'<rect x="{xc(i) - bw / 2:.1f}" y="{top:.1f}" width="{bw:.1f}" height="{max(bot - top, 1.5):.1f}" rx="1" fill="{col}"/></g>'
             f'<rect class="v" {dl} x="{xc(i) - bw / 2:.1f}" y="{VY1 - v / vmax * (VY1 - VY0):.1f}" width="{bw:.1f}" height="{max(v / vmax * (VY1 - VY0), 1):.1f}" fill="{col}" fill-opacity="0.45"/>')
ma = [sum(vols[max(0, i - 3):i + 1]) / len(vols[max(0, i - 3):i + 1]) for i in range(N)]
ma_pts = " ".join(f"{xc(i):.1f},{VY1 - m / vmax * (VY1 - VY0):.1f}" for i, m in enumerate(ma))
lo_, lh_, ll_, lc, lv = candles[-1]
ly = y(lc)
lcol = UP if lc > lo_ else DN if lc < lo_ else DIM
ohlc = "&#160;&#160;".join(f'<tspan fill="{DIM}">{k}</tspan> <tspan fill="{lcol}">{v}</tspan>' for k, v in [("O", lo_), ("H", lh_), ("L", ll_), ("C", lc), ("VOL", lv)])
ai = max(range(N), key=lambda i: candles[i][1])  # all-time-high candle
ath = f'<text x="{xc(ai):.0f}" y="{y(candles[ai][1]) - 5:.0f}" font-size="9" font-weight="700" fill="{GOLD}" text-anchor="middle" font-family="{MONO}">H {candles[ai][1]}</text>'

hstats = "".join(
    f'<text x="{x}" y="27" font-size="8.5" font-weight="700" letter-spacing="1" fill="{DIM}">{k}</text><text x="{x}" y="45" font-size="12.5" font-weight="700" fill="{TXT}" font-family="{MONO}">{v}</text>'
    for x, k, v in [(556, "52W HIGH", hi_p), (624, "52W LOW", lo_p), (690, "4W VOL", last4)])

mood_t = mood.upper()  # mood pill, right-aligned above the chart
mw = 22 + 6.6 * len(mood_t)
mx = CX1 - mw
pills = (f'<rect x="{mx:.0f}" y="69" width="{mw:.0f}" height="16" rx="8" fill="{UP}" fill-opacity="0.12" stroke="{UP}" stroke-opacity="0.5"/>'
         f'<circle cx="{mx + 10:.0f}" cy="77" r="2.5" fill="{UP}"/><text x="{mx + 17:.0f}" y="80.5" font-size="8.5" font-weight="700" letter-spacing="1" fill="{UP}">{esc(mood_t)}</text>')

legend = "".join(f'<rect x="{x}" y="{VY1 + 41}" width="8" height="8" rx="2" fill="{c}"/><text x="{x + 13}" y="{VY1 + 49}" font-size="9.5" fill="{DIM}">{t}</text>'
                 for x, c, t in [(CX0, UP, "Up week (close &gt; open)"), (CX0 + 130, DN, "Down week"), (CX0 + 206, DIM, "Flat")]
                 ) + f'<line x1="{CX0 + 254}" x2="{CX0 + 268}" y1="{VY1 + 45}" y2="{VY1 + 45}" stroke="{GOLD}" stroke-width="1.6"/><text x="{CX0 + 273}" y="{VY1 + 49}" font-size="9.5" fill="{DIM}">MA(4) volume</text>'

tape = [("COMMITS", f"{total:,}", dtxt, dcol), ("STREAK", f"{streak}d", None, DIM), ("ACTIVE", str(active), None, DIM),
        ("LONGEST", f"{longest}d", None, DIM), ("REPOS", str(user["public_repos"]), None, DIM), ("STARS", str(stars), None, DIM),
        ("FOLLOWERS", str(user["followers"]), None, DIM)] + [(n.upper()[:8], f"{100 * b / lang_total:.0f}%", None, DIM) for n, b in lang_rows[:2]]
TS = 190
item = lambda x, t: (f'<text x="{x}" y="0" font-size="11" font-family="{MONO}"><tspan fill="{DIM}">{t[0]} </tspan><tspan fill="{TXT}" font-weight="700">{t[1]}</tspan>'
                     + (f'<tspan fill="{t[3]}"> {t[2]}</tspan>' if t[2] else "") + "</text>")
TW = TS * len(tape)
tape_svg = "".join(item(k * TS + j * TW, t) for j in (0, 1) for k, t in enumerate(tape))
pw = 24 + 7.2 * len(dtxt)  # change-pill width

write("assets/dashboard.svg", f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 {HH}" width="760" height="{HH}" role="img" aria-label="Trading-style dashboard for {esc(USER)}: {total} contributions, {active} active days, {streak} day streak">
<defs><clipPath id="tp"><rect x="16" y="{TY}" width="728" height="30"/></clipPath><clipPath id="av"><circle cx="40" cy="32" r="16"/></clipPath>
<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{UP}" stop-opacity="0.10"/><stop offset="1" stop-color="{UP}" stop-opacity="0"/></linearGradient>
<radialGradient id="glow" cx="0.85" cy="0" r="0.7"><stop offset="0" stop-color="{UP}" stop-opacity="0.07"/><stop offset="1" stop-color="{UP}" stop-opacity="0"/></radialGradient></defs>
<style>.blink{{animation:b 1.2s steps(2) infinite}}@keyframes b{{50%{{opacity:.25}}}}.pulse{{transform-box:fill-box;transform-origin:center;animation:p 2.2s ease-out infinite}}@keyframes p{{0%{{opacity:.7;transform:scale(1)}}100%{{opacity:0;transform:scale(2.8)}}}}.c{{transform-origin:0 {CY1}px;animation:grow .55s cubic-bezier(.2,.8,.2,1) both}}.v{{transform-origin:0 {VY1}px;animation:grow .55s cubic-bezier(.2,.8,.2,1) both}}@keyframes grow{{from{{transform:scaleY(0);opacity:0}}}}.ma{{stroke-dasharray:1;animation:draw 1.1s ease-out .5s both}}@keyframes draw{{from{{stroke-dashoffset:1}}to{{stroke-dashoffset:0}}}}.late{{animation:fade .4s ease-out 1.3s both}}@keyframes fade{{from{{opacity:0}}}}@media (prefers-reduced-motion:reduce){{.blink{{animation:none}}.pulse{{animation:none;opacity:0}}.c,.v,.ma,.late{{animation:none}}}}</style>
<rect x="1" y="1" width="758" height="{HH - 2}" rx="14" fill="{BG}" stroke="{LINE}"/><rect x="1" y="1" width="758" height="{HH - 2}" rx="14" fill="url(#glow)"/>
<g font-family="{SANS}">
<circle cx="40" cy="32" r="19" fill="none" stroke="{UP}" stroke-width="2"/>
<image href="data:image/jpeg;base64,{avatar()}" x="24" y="16" width="32" height="32" clip-path="url(#av)" preserveAspectRatio="xMidYMid slice"/>
<text x="70" y="29" font-size="15" font-weight="800" fill="{TXT}">{esc(USER.upper())}<tspan fill="{DIM}" font-weight="600">/COMMITS</tspan></text>
<circle class="pulse" cx="75" cy="43" r="3" fill="{UP}"/><circle cx="75" cy="43" r="3" fill="{UP}"/>
<text x="84" y="46.5" font-size="10.5" fill="{DIM}">{esc(TAGLINE)} · 1W</text>
<text x="326" y="40" font-size="25" font-weight="800" fill="{dcol}" font-family="{MONO}">{total:,}</text>
<rect x="{326 + 15.2 * len(f"{total:,}") + 10:.0f}" y="22" width="{pw:.0f}" height="24" rx="12" fill="{dcol}" fill-opacity="0.15"/>
<text x="{326 + 15.2 * len(f"{total:,}") + 10 + pw / 2:.0f}" y="38" font-size="11.5" font-weight="700" fill="{dcol}" text-anchor="middle">{dtxt}</text>
{hstats}
<line x1="16" x2="744" y1="64" y2="64" stroke="{LINE}"/>
<text x="24" y="86" font-size="10" font-family="{MONO}">{ohlc}</text>
{pills}
<text x="{(CX0 + CX1) / 2:.0f}" y="{(CY0 + CY1) / 2 + 18:.0f}" font-size="58" font-weight="800" fill="{TXT}" fill-opacity="0.035" text-anchor="middle" letter-spacing="6">{esc(re.split(r"[-_]", USER)[0].upper()[:10])}</text>
{grid}
{bars}
<polyline class="ma" pathLength="1" points="{ma_pts}" fill="none" stroke="{GOLD}" stroke-width="1.4"/>
<g class="late">{ath}
<line x1="{CX0}" x2="{CX1}" y1="{ly:.1f}" y2="{ly:.1f}" stroke="{lcol}" stroke-dasharray="3 3" stroke-opacity="0.8"/>
<circle class="blink" cx="{xc(N - 1):.1f}" cy="{ly:.1f}" r="3.5" fill="{lcol}"/>
<rect x="{CX1 + 30}" y="{ly - 9:.1f}" width="28" height="18" rx="3" fill="{lcol}"/><text x="{CX1 + 44}" y="{ly + 4:.1f}" font-size="10.5" font-weight="800" fill="{BG}" text-anchor="middle" font-family="{MONO}">{lc}</text></g>
{ylabels}
<line x1="{CX0}" x2="{CX1}" y1="{VY0 - 8}" y2="{VY0 - 8}" stroke="{LINE}"/>
<text x="{CX0 + 4}" y="{VY0 + 4}" font-size="9" fill="{DIM}" font-family="{MONO}">Volume</text>
{xlabels}
{legend}
<text x="24" y="{VY1 + 68}" font-size="9.5" fill="{DIM}">Candle = 1 week of daily commits (open = first day, close = last day) · price axis is sqrt-scaled</text>
<rect x="566" y="76" width="178" height="{PB - 76}" rx="10" fill="{PANEL}" stroke="{LINE}"/>
<text x="580" y="100" font-size="9.5" font-weight="700" letter-spacing="2" fill="{DIM}">PORTFOLIO</text>
{panel}
<rect x="16" y="{TY}" width="728" height="30" rx="8" fill="{PANEL}" stroke="{LINE}"/>
<g clip-path="url(#tp)"><g transform="translate(0,{TY + 19})"><g>{tape_svg}
<animateTransform attributeName="transform" type="translate" from="30 0" to="{30 - TW} 0" dur="{len(tape) * 4}s" repeatCount="indefinite"/></g></g></g>
</g></svg>
''')

# ---------- city: contribution calendar as a volume skyline ----------
PAL = {0: ("#161c22", "#11161b", "#0d1115"), 1: ("#0a4d36", "#073b29", "#052c1f"), 2: ("#0b8a5f", "#086a49", "#064f37"),
       3: ("#0ecb81", "#0a9a62", "#077248"), 4: ("#6af0b8", "#3fbf8a", "#2a8f66")}
HIGH = ("#f8d35e", GOLD, "#b88a00")  # busy days (and the all-time high) in gold
shapes, W, H, ox, oy = iso_city(days, maxc, PAL, HIGH, high_min)
legend = "".join(f'<rect x="{W - 262 + i * 18:.0f}" y="{H - 62:.0f}" width="12" height="12" rx="3" fill="{PAL[i][0]}"/>' for i in range(5))
legend += f'<rect x="{W - 92:.0f}" y="{H - 62:.0f}" width="12" height="12" rx="3" fill="{GOLD}"/><text x="{W - 74:.0f}" y="{H - 52:.0f}" font-size="11" fill="{DIM}">Peak</text>'
chips, cx_ = "", 44
for lab, val, col in [("TOTAL", f"{total:,}", UP), ("ACTIVE DAYS", str(active), TXT), ("ATH", f"{best[4]} · {bd:%b} {bd.day}", GOLD)]:
    lw, vw = 6.4 * len(lab), 7.2 * len(val)
    w = 10 + lw + 8 + vw + 10
    chips += (f'<rect x="{cx_:.0f}" y="104" width="{w:.0f}" height="24" rx="6" fill="{PANEL}" stroke="{LINE}"/>'
              f'<text x="{cx_ + 10:.0f}" y="120" font-size="9" font-weight="700" letter-spacing="1" fill="{DIM}">{lab}</text>'
              f'<text x="{cx_ + 18 + lw:.0f}" y="120" font-size="11.5" font-weight="700" fill="{col}" font-family="{MONO}">{esc(val)}</text>')
    cx_ += w + 8
write("assets/city.svg", f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" height="{H:.0f}" role="img" aria-label="Volume skyline for {esc(USER)}: {total} contributions, {active} active days">
<defs><radialGradient id="glow" cx="0.85" cy="0" r="0.7"><stop offset="0" stop-color="{UP}" stop-opacity="0.07"/><stop offset="1" stop-color="{UP}" stop-opacity="0"/></radialGradient></defs>
<style>{CITY_CSS}</style>
<rect x="0.5" y="0.5" width="{W - 1:.0f}" height="{H - 1:.0f}" rx="22" fill="{BG}" stroke="{LINE}"/><rect x="0.5" y="0.5" width="{W - 1:.0f}" height="{H - 1:.0f}" rx="22" fill="url(#glow)"/>
<g stroke="{LINE}" stroke-dasharray="2 5">{"".join(f'<line x1="22" x2="{W - 22:.0f}" y1="{H * k / 6:.0f}" y2="{H * k / 6:.0f}"/>' for k in range(1, 6))}</g>
<g transform="translate({ox:.1f},{oy:.1f})">
{chr(10).join(shapes)}
</g>
<g font-family="{SANS}">
<text x="44" y="64" font-size="20" font-weight="800" fill="{TXT}">{esc(USER.upper())}<tspan fill="{DIM}" font-weight="600">/VOLUME</tspan></text>
<text x="44" y="86" font-size="12" fill="{DIM}">Daily contribution volume · 12 months · block height = commits</text>
{chips}
<text x="{W - 268:.0f}" y="{H - 52:.0f}" font-size="11" fill="{DIM}" text-anchor="end">Low</text>
{legend}
<text x="{W - 124:.0f}" y="{H - 52:.0f}" font-size="11" fill="{DIM}">High</text>
<text x="44" y="{H - 34:.0f}" font-size="11" font-family="{MONO}" fill="{DIM}">@{esc(USER)} · {d0:%b %Y} to {d1:%b %Y}</text>
</g>
</svg>
''')

# ---------- projects: watchlist table ----------
STAR = "0,-7 2,-2.4 7,-2.2 3.1,0.9 4.3,5.7 0,3 -4.3,5.7 -3.1,0.9 -7,-2.2 -2,-2.4"
slots = ranked[:5]
slots += [None] * (3 - len(slots))
RH = 42


def row(i, r):
    ry = 78 + i * RH
    sep = f'<line x1="24" x2="736" y1="{ry + RH - 6}" y2="{ry + RH - 6}" stroke="{LINE}"/>'
    if r is None:
        return (f'<text x="24" y="{ry + 18}" font-size="13" font-weight="700" fill="{DIM}" font-family="{MONO}">—</text>'
                f'<text x="190" y="{ry + 18}" font-size="11.5" fill="{DIM}">Next listing coming soon</text>{sep}')
    name = r["name"].upper()
    name = name if len(name) <= 16 else name[:15] + "…"
    d_ = r["description"] or "No description yet."
    d_ = d_ if len(d_) <= 38 else d_[:37] + "…"
    col = LANG_COLORS.get(r["language"], UP) if r["language"] else DIM
    pushed = date.fromisoformat(r["pushed_at"][:10])
    st = r["stargazers_count"]
    fav = is_fav(r)
    mark = (f'<polygon transform="translate(30,{ry + 14}) scale(0.9)" points="{STAR}" fill="{GOLD}"/>'
            f'<text x="42" y="{ry + 30}" font-size="8" font-weight="700" letter-spacing="1.5" fill="{GOLD}">FEATURED</text>') if fav else f'<circle cx="30" cy="{ry + 14}" r="4" fill="{UP}"/>'
    return (mark +
            f'<text x="42" y="{ry + 18}" font-size="13" font-weight="800" fill="{TXT}" font-family="{MONO}">{esc(name)}</text>'
            f'<text x="190" y="{ry + 18}" font-size="11.5" fill="{DIM}">{esc(d_)}</text>'
            f'<circle cx="474" cy="{ry + 14}" r="4" fill="{col}"/><text x="484" y="{ry + 18}" font-size="11.5" fill="{TXT}">{esc(r["language"] or "Public")}</text>'
            f'<text x="620" y="{ry + 18}" font-size="12" font-weight="700" fill="{UP if st else DIM}" text-anchor="end" font-family="{MONO}">{"▲" if st else "■"} {st}</text>'
            f'<text x="736" y="{ry + 18}" font-size="11" fill="{DIM}" text-anchor="end" font-family="{MONO}">{pushed:%b} {pushed.day}</text>{sep}')


PH = 78 + len(slots) * RH + 6
write("assets/projects.svg", f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 {PH}" width="760" height="{PH}" role="img" aria-label="Watchlist: {len(ranked)} public repos, {sum(1 for r in ranked if is_fav(r))} featured">
<rect x="1" y="1" width="758" height="{PH - 2}" rx="14" fill="{BG}" stroke="{LINE}"/>
<g font-family="{SANS}">
<text x="24" y="34" font-size="15" font-weight="800" fill="{TXT}">WATCHLIST</text>
<rect x="116" y="20" width="{22 + 7 * len(str(len(ranked)))}" height="18" rx="9" fill="{UP}" fill-opacity="0.15"/><text x="{127 + 3.5 * len(str(len(ranked)))}" y="33" font-size="10.5" font-weight="700" fill="{UP}" text-anchor="middle" font-family="{MONO}">{len(ranked)}</text>
<text x="736" y="33" font-size="10.5" fill="{DIM}" text-anchor="end">{'Featured first, then by stars' if any(is_fav(r) for r in ranked) else 'Positions · sorted by stars'}</text>
<line x1="16" x2="744" y1="50" y2="50" stroke="{LINE}"/>
<g font-size="9" font-weight="700" letter-spacing="1.5" fill="{DIM}"><text x="24" y="68">SYMBOL</text><text x="190" y="68">DESCRIPTION</text><text x="474" y="68">LANGUAGE</text><text x="620" y="68" text-anchor="end">STARS</text><text x="736" y="68" text-anchor="end">LAST TRADE</text></g>
{"".join(row(k, s) for k, s in enumerate(slots))}
</g>
</svg>
''')

# ---------- footer: terminal status bar ----------
chips, cx_ = "", 92
for label, col in [(f, UP) for f in FOCUS] + [("Market open", UP)]:
    t = label.upper()
    w = 22 + 7.0 * len(t)
    chips += (f'<rect x="{cx_:.0f}" y="52" width="{w:.0f}" height="20" rx="10" fill="{col}" fill-opacity="0.12" stroke="{col}" stroke-opacity="0.5"/>'
              f'<text x="{cx_ + w / 2:.0f}" y="65.5" font-size="9.5" font-weight="700" letter-spacing="1.2" fill="{col}" text-anchor="middle">{esc(t)}</text>')
    cx_ += w + 8
write("assets/footer.svg", f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 124" width="760" height="124" role="img" aria-label="{esc(USER)} · {esc(TAGLINE)} · last updated {now:%b} {now.day}, {now.year}">
<defs><clipPath id="fav"><circle cx="52" cy="50" r="22"/></clipPath>
<linearGradient id="bar" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{UP}"/><stop offset="1" stop-color="{GOLD}"/></linearGradient></defs>
<style>
.pulse{{transform-box:fill-box;transform-origin:center;animation:pulse 2.4s ease-out infinite}}
@keyframes pulse{{0%{{opacity:.7;transform:scale(1)}}100%{{opacity:0;transform:scale(2.6)}}}}
@media (prefers-reduced-motion:reduce){{.pulse{{animation:none;opacity:0}}}}
</style>
<rect x="1" y="1" width="758" height="122" rx="14" fill="{BG}" stroke="{LINE}"/>
<rect x="24" y="1.5" width="712" height="2" rx="1" fill="url(#bar)" fill-opacity="0.8"/>
<circle cx="52" cy="50" r="26" fill="none" stroke="{UP}" stroke-width="2.5"/>
<image href="data:image/jpeg;base64,{avatar()}" x="30" y="28" width="44" height="44" clip-path="url(#fav)" preserveAspectRatio="xMidYMid slice"/>
<g font-family="{SANS}">
<text x="92" y="38" font-size="17" font-weight="800" fill="{TXT}">{esc(USER)}</text>
{chips}
<text x="732" y="30" font-size="9" font-weight="700" letter-spacing="2" fill="{DIM}" text-anchor="end">LAST UPDATED</text>
<text x="732" y="54" font-size="19" font-weight="800" fill="{UP}" text-anchor="end" font-family="{MONO}">{now:%b} {now.day}, {now.year}</text>
<circle class="pulse" cx="{732 - 4.8 * 28 - 12:.0f}" cy="68" r="3" fill="{UP}"/>
<circle cx="{732 - 4.8 * 28 - 12:.0f}" cy="68" r="3" fill="{UP}"/>
<text x="732" y="72" font-size="10.5" fill="{DIM}" text-anchor="end">auto-refreshes every 3 hours</text>
<line x1="24" y1="92" x2="736" y2="92" stroke="{LINE}"/>
<text x="24" y="109" font-size="10" fill="{DIM}">© {now.year} {esc(USER)}</text>
<text x="736" y="109" font-size="10" fill="{DIM}" text-anchor="end">Generated from live GitHub data · GitHub Actions</text>
</g>
</svg>
''')
write("snippet.md", f'''<p align="center">
  <img src="./themes/trading/assets/dashboard.svg" alt="Trading dashboard with weekly candles, stats and language allocation for {esc(USER)}" width="100%" />
</p>

<br/>

<p align="center">
  <img src="./themes/trading/assets/city.svg" alt="Volume skyline of contributions" width="100%" />
</p>

<br/>

<p align="center">
  <a href="https://github.com/{esc(USER)}?tab=repositories"><img src="./themes/trading/assets/projects.svg" alt="Watchlist of {esc(USER)}'s repositories" width="100%" /></a>
</p>

<br/>

<p align="center">
  <a href="https://github.com/{esc(USER)}"><img src="./themes/trading/assets/footer.svg" alt="{esc(USER)} · {esc(TAGLINE)}" width="100%" /></a>
</p>
''')
print(f"{USER}: total={total} active={active} streak={streak} weeks={N} delta={chg} repos={len(repos)} langs={len(lang_rows)}")
