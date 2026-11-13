"""Shared GitHub data for every theme: contribution calendar, streaks, profile, repos, languages.

Importing it fetches once. Env: PROFILE_USER (defaults to the repo owner in GitHub Actions),
GITHUB_TOKEN (optional, raises API rate limit). Optional profile.json at the repo root:
{"tagline": "...", "focus": ["..."], "weakness": "..."}; the tagline falls back to your GitHub bio.
A repo with the "featured" topic is listed first by every theme.
"""
import base64, json, os, re, sys, urllib.request
from datetime import date, datetime, timezone
from functools import cache
from itertools import groupby, takewhile
from pathlib import Path

USER = os.environ.get("PROFILE_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER") or sys.exit("set PROFILE_USER to your GitHub username")
ROOT = Path(__file__).resolve().parent.parent  # repo root
CFG = json.loads((ROOT / "profile.json").read_text(encoding="utf-8")) if (ROOT / "profile.json").exists() else {}
FOCUS = CFG.get("focus", [])  # chips in the footer
OUT = Path(sys.argv[0]).resolve().parent  # the theme folder being generated: python themes/<name>/generate.py
# system fonts only: svgs shown through <img> can't load web fonts
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"
MONO = "'JetBrains Mono','Cascadia Mono','SF Mono',Menlo,Consolas,'DejaVu Sans Mono','Liberation Mono',monospace"
LANG_COLORS = {
    "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "Python": "#3572a5", "HTML": "#e34c26", "CSS": "#8b5cf6",
    "Java": "#b07219", "C++": "#f34b7d", "C": "#8b9aa8", "C#": "#43a047", "Go": "#00add8", "Rust": "#dea584",
    "PHP": "#4f5d95", "Ruby": "#cc342d", "Swift": "#f05138", "Kotlin": "#a97bff", "Dart": "#00b4ab",
    "Shell": "#89e051", "Vue": "#41b883", "SCSS": "#c6538c",
}


def fetch(url, api=False):
    h = {"User-Agent": "profile-readme-generator"}
    if api and os.environ.get("GITHUB_TOKEN"):
        h["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    return urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30).read()


def gh(path):
    return json.loads(fetch("https://api.github.com" + path, api=True))


def write(path, text):
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


# ---------- data ----------
html = fetch(f"https://github.com/users/{USER}/contributions").decode("utf-8")
cells = {}  # id -> [row, col, date, level, count]
for m in re.finditer(r'<td[^>]*data-date="([^"]+)"[^>]*id="contribution-day-component-(\d+)-(\d+)"[^>]*data-level="(\d)"', html):
    cells[f"{m[2]}-{m[3]}"] = [int(m[2]), int(m[3]), m[1], int(m[4]), 0]
for m in re.finditer(r'<tool-tip[^>]*for="contribution-day-component-(\d+-\d+)"[^>]*>\s*([^<]*?)\s*</tool-tip>', html):
    n = re.match(r"(\d+) contribution", m[2])
    if m[1] in cells:
        cells[m[1]][4] = int(n[1]) if n else 0
days = sorted(cells.values(), key=lambda c: c[2])
assert days, "no calendar cells parsed"

total = sum(c[4] for c in days)
active = sum(1 for c in days if c[4])
best = max(days, key=lambda c: c[4])
maxc = max(best[4], 1)
d0, d1 = date.fromisoformat(days[0][2]), date.fromisoformat(days[-1][2])
bd = date.fromisoformat(best[2])


def fd(s):
    d = date.fromisoformat(s)
    return f"{d:%b} {d.day}"


rev = days[::-1]
if rev[0][4] == 0:
    rev = rev[1:]  # today isn't over yet; GitHub doesn't break the streak for it
cur = list(takewhile(lambda c: c[4] > 0, rev))  # current streak, newest first
streak = len(cur)
cur_range = f"{fd(cur[-1][2])} - {fd(cur[0][2])}" if cur else "no active streak"
top = max((list(g) for k, g in groupby(days, key=lambda c: c[4] > 0) if k), key=len, default=[])  # longest run of active days
longest = len(top)
long_range = f"{fd(top[0][2])} - {fd(top[-1][2])}" if top else "-"

user = gh(f"/users/{USER}")
TAGLINE = CFG.get("tagline") or (user.get("bio") or "Developer")[:44]
repos = [r for r in gh(f"/users/{USER}/repos?per_page=100&sort=pushed") if not r["fork"]]
stars = sum(r["stargazers_count"] for r in repos)
joined = date.fromisoformat(user["created_at"][:10])


@cache
def avatar():  # base64 profile picture; only some themes draw it, so it is fetched on first use
    return base64.b64encode(fetch(user["avatar_url"] + ("&" if "?" in user["avatar_url"] else "?") + "s=240")).decode()


langs = {}  # language -> bytes across all non-fork public repos
for r in repos:
    try:
        for name, b in gh(f"/repos/{r['full_name']}/languages").items():
            langs[name] = langs.get(name, 0) + b
    except Exception:
        pass  # one repo failing shouldn't blank the card
lang_total = sum(langs.values())
lang_rows = sorted(langs.items(), key=lambda kv: -kv[1])

# ---------- derived once, shared by every theme ----------
def pick(v, limits, names):  # names has one more entry than limits
    return names[sum(v >= lim for lim in limits)]


mood = pick(streak, [1, 3, 7], ["Recharging", "Warming up", "Locked in", "In the zone"])
high_min = max(8, 0.5 * maxc)  # a day at or above this many commits is "busy" in every theme (below 8, nothing is, however quiet the year)
is_fav = lambda r: "featured" in (r.get("topics") or [])  # give a repo the "featured" topic on GitHub to list it first

WD = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
wd, weeks = [0] * 7, {}
for c in days:
    wd[c[0]] += c[4]  # row 0 = Sunday in GitHub's calendar
    weeks.setdefault(c[1], []).append(c[4])
wmax = max(wd) or 1
wk = [w for _, w in sorted(weeks.items())]  # daily counts per calendar week, oldest first
vols = [sum(w) for w in wk]
last4, prev4 = sum(vols[-4:]), sum(vols[-8:-4])
chg = (last4 / prev4 - 1) * 100 if prev4 else None  # events in the last 4 weeks vs the 4 before, in %

pool = [r for r in repos if not r["archived"]]
pool = [r for r in pool if r["name"].lower() != USER.lower()] or pool  # profile repo only if it's all there is
ranked = sorted(pool, key=lambda r: (not is_fav(r), -r["stargazers_count"]))  # featured first, then stars; ties keep latest-push order

now = datetime.now(timezone.utc)
