"""Shared GitHub data for every theme: contribution calendar, streaks, profile, repos, languages.

Importing it fetches once. Env: PROFILE_USER (defaults to the repo owner in GitHub Actions),
GITHUB_TOKEN (optional, raises API rate limit). Optional profile.json at the repo root:
{"tagline": "...", "focus": ["..."], "weakness": "...", "mood": "...", "favorites": ["repo"]}; the tagline falls back to your GitHub bio.
"""
import base64, json, math, os, re, sys, urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

USER = os.environ.get("PROFILE_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER") or sys.exit("set PROFILE_USER to your GitHub username")
ROOT = Path(__file__).resolve().parent.parent  # repo root
CFG = json.loads((ROOT / "profile.json").read_text(encoding="utf-8")) if (ROOT / "profile.json").exists() else {}
FOCUS = CFG.get("focus", [])  # chips in the footer


def fetch(url, api=False):
    h = {"User-Agent": "profile-readme-generator"}
    if api and os.environ.get("GITHUB_TOKEN"):
        h["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    return urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30).read()


def gh(path):
    return json.loads(fetch("https://api.github.com" + path, api=True))


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
streak = 0
for c in rev:
    if c[4] == 0:
        break
    streak += 1
longest = run = 0
ls_ = le_ = rs = None
for c in days:
    if c[4]:
        if run == 0:
            rs = c[2]
        run += 1
        if run > longest:
            longest, ls_, le_ = run, rs, c[2]
    else:
        run = 0
cur_range = f"{fd(rev[streak-1][2])} - {fd(rev[0][2])}" if streak else "no active streak"
long_range = f"{fd(ls_)} - {fd(le_)}" if longest else "-"

user = gh(f"/users/{USER}")
TAGLINE = CFG.get("tagline") or (user.get("bio") or "Developer")[:44]
repos = [r for r in gh(f"/users/{USER}/repos?per_page=100&sort=pushed") if not r["fork"]]
stars = sum(r["stargazers_count"] for r in repos)
joined = date.fromisoformat(user["created_at"][:10])
avatar = base64.b64encode(fetch(user["avatar_url"] + ("&" if "?" in user["avatar_url"] else "?") + "s=240")).decode()

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
RANKS = [(0, "Rookie Trainer"), (100, "Basic Trainer"), (500, "Ace Trainer"), (1500, "Elite Trainer"), (3000, "Champion")]  # (min contributions, title)
rank_i = max(i for i, r in enumerate(RANKS) if total >= r[0])
rank_name = RANKS[rank_i][1]
next_txt = f"Next rank · {RANKS[rank_i + 1][0]:,}" if rank_i + 1 < len(RANKS) else "Max rank"


def pick(v, limits, names):  # names has one more entry than limits
    return names[sum(v >= lim for lim in limits)]


mood = CFG.get("mood") or pick(streak, [1, 3, 7], ["Recharging", "Warming up", "Locked in", "In the zone"])
FAVORITES = CFG.get("favorites", [])  # repo names to always feature first (or just add the "featured" topic to a repo on GitHub)
FEATURED_TOPIC = "featured"


def is_fav(r):
    return r["name"] in FAVORITES or FEATURED_TOPIC in (r.get("topics") or [])


now = datetime.now(timezone.utc)
