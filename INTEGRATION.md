# Use this on your own GitHub profile

This repo turns your live GitHub activity into a profile README with four switchable themes
(**default**, **trading**, **terminal**, **soc**). A GitHub Action rebuilds the images every 3 hours,
so the stats always belong to whoever owns the repo. Nothing here is tied to the original author.

You need: a GitHub account and about 10 minutes. You do not need to install anything unless you want to preview locally.

---

## 1. Create your profile repo

GitHub only shows a README on your profile when the repo is **public** and named **exactly your username**.

1. Go to <https://github.com/new>.
2. Repository name: your username, character for character (`octocat` -> `octocat/octocat`).
3. Choose **Public**. Leave "Add a README" **unticked**. Click **Create repository**.

> If GitHub shows "You found a secret!" under the name box, the name is right.

## 2. Copy the files into it

Clone this repo, drop its history, and push the files to your new repo.

```bash
git clone https://github.com/ArshadWork-009/ArshadWork-009.git my-profile
cd my-profile
rm -rf .git                      # PowerShell: Remove-Item -Recurse -Force .git
git init -b main
git add .
git commit -m "Initial profile"
git remote add origin https://github.com/YOUR-USERNAME/YOUR-USERNAME.git
git push -u origin main
```

Why not fork? A fork keeps the original repo name, but your profile repo must be named after *you*. You would have to rename it, and a new repo is simpler.

## 3. Make it yours: `profile.json`

Open `profile.json` in the repo root and replace the text. Every key is optional.

```json
{
  "tagline": "Data Engineer · Open Source",
  "focus": ["Data", "Python"],
  "weakness": "off-by-one errors ×3"
}
```

| Key | Where it shows | If you leave it out |
|-----|----------------|---------------------|
| `tagline` | under your name in every theme | your GitHub bio (first 44 characters), then "Developer" |
| `focus` | footer chips (default, trading) and the `echo $FOCUS` line (terminal) | no chips, no line |
| `weakness` | one joke line on the default theme's card | "none found" |

Your username, avatar, stats, languages and repos are read from GitHub automatically. You never type them in.

## 4. Allow the Action to save its work

The Action commits the regenerated images back to your repo, so it needs write permission. (What the Actions are and why they exist is explained [further down](#what-the-actions-do-and-why-they-exist).)

1. In your repo: **Settings -> Actions -> General**.
2. Scroll to **Workflow permissions**.
3. Choose **Read and write permissions** and click **Save**.

## 5. Run the first build

Until this runs, your repo still contains the *original author's* images and stats.

1. Open the **Actions** tab. If GitHub asks, click **I understand my workflows, go ahead and enable them**.
2. Click **Update profile visuals** in the left list.
3. Click **Run workflow** -> **Run workflow**.
4. Wait about a minute for the green tick. A new commit called `chore: update profile visuals` appears.

From now on it runs by itself every 3 hours, and again whenever you push a change to `profile.json` or a theme's `generate.py`.

## 6. Pick a theme

Every theme lives in its own folder under `themes/`.

| Theme | Looks like |
|-------|-----------|
| `default` | a trainer card with rank, streak and language stack, plus a 3D contribution city |
| `trading` | candlestick chart of your weekly commits, order flow, watchlist |
| `terminal` | zsh windows: `whoami`, `git shortlog`, an `nmap`-style language table, a heatmap |
| `soc` | a security-operations console: activity gauge, alert severity, alert calendar |

**Option A, from the website:**

1. **Actions** tab -> **Switch README theme** -> **Run workflow**.
2. Type a theme folder name, for example `terminal`, and run it.
3. After about 20 seconds your profile page shows that theme.

**Option B, by hand:** copy the theme's `snippet.md` over `README.md` and push.

```bash
cp themes/terminal/snippet.md README.md      # PowerShell: Copy-Item themes\terminal\snippet.md README.md
git add README.md
git commit -m "Use the terminal theme"
git push
```

The 3-hourly build notices which theme `README.md` is using and keeps it up to date, so you can switch whenever you like.

## 7. Check your profile

Open `https://github.com/YOUR-USERNAME`. The README appears above your pinned repos. If the images look stale, wait for the next run or press **Run workflow** again.

---

## Optional: pin a repo to the top

Themes list your public, non-fork, non-archived repos by stars. To list one first:

1. Open that repo on GitHub, click the gear next to **About**.
2. Add the topic `featured` and save.
3. It shows first, with a "featured" badge, after the next build.

## Optional: preview on your own computer

Needs Python 3.12 or newer. There is nothing to `pip install`.

```bash
# macOS / Linux
PROFILE_USER=YOUR-USERNAME python scripts/build.py
python scripts/preview.py
```

```powershell
# Windows PowerShell
$env:PROFILE_USER = "YOUR-USERNAME"
python scripts/build.py
python scripts/preview.py
```

Then double-click `preview.html`. It has one button per theme. The file is git-ignored.

GitHub allows only 60 anonymous API requests an hour. If you see `HTTP Error 403: rate limit exceeded`,
create a token at <https://github.com/settings/tokens> (no scopes needed) and set it before running:

```bash
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx          # PowerShell: $env:GITHUB_TOKEN = "ghp_xxxxxxxxxxxx"
```

The Action does not have this problem: it uses its own token.

## Optional: make your own theme

Copy a theme folder, rename it, and edit its `generate.py`. Nothing needs registering.

```bash
cp -r themes/terminal themes/mytheme
# edit themes/mytheme/generate.py, then:
PROFILE_USER=YOUR-USERNAME python scripts/build.py
```

Details are in [`themes/HOWTO.md`](themes/HOWTO.md).

---

## How it fits together

```
profile.json              your text: tagline, focus, weakness
scripts/profile_data.py   fetches your GitHub data once, shared by every theme
scripts/build.py          runs every themes/*/generate.py
themes/<name>/
  generate.py             draws that theme
  assets/*.svg            the generated images (committed by the Action)
  snippet.md              the README for that theme, ready to paste
README.md                 the active theme's snippet; this is what your profile shows
.github/workflows/        update-profile.yml (every 3h) and switch-theme.yml (manual)
```

## What the Actions do, and why they exist

A GitHub profile README is plain Markdown: it cannot run code or call GitHub's API. So the stats are drawn
ahead of time as images (SVG files) and the README just shows those images. **GitHub Actions** is the free
robot that redraws them for you, so you never run anything by hand. There are two workflows, both in
`.github/workflows/`. See their runs and logs under your repo's **Actions** tab.

### 1. Update profile visuals (`update-profile.yml`), the one that keeps stats fresh

| | |
|---|---|
| **Runs when** | every 3 hours; when you press **Run workflow**; when you push a change to `profile.json`, `scripts/profile_data.py` or any `themes/*/generate.py` |
| **Result** | a commit called `chore: update profile visuals`, made only if something actually changed |

What it does, step by step:

1. Checks out your repo and installs Python 3.12 on a temporary GitHub machine.
2. Runs `scripts/build.py`, which runs every theme's `generate.py`. Each one reads your contributions, profile, repos and languages from GitHub and rewrites that theme's `assets/*.svg` and `snippet.md`. It gets your username from the repo owner, so it works for anyone without editing.
3. Looks at `README.md` to see which theme you are using and refreshes it from that theme's new `snippet.md`.
4. Commits the changed files as `github-actions` and pushes them to `main`.

### 2. Switch README theme (`switch-theme.yml`), the manual theme picker

| | |
|---|---|
| **Runs when** | only when you press **Run workflow** (it asks for a theme name) |
| **Result** | a commit called `chore: switch README to <theme> theme` |

It checks the name is a real folder under `themes/`, copies that theme's `snippet.md` over `README.md`, and commits it.
Only people with write access to your repo can run it, so visitors cannot change your profile.

### Good to know

- **Cost:** nothing. Actions are free and unlimited on public repos.
- **Secrets:** none to set up. It uses the `GITHUB_TOKEN` GitHub creates for each run, which can only write to this repo and expires when the run ends. That token also gives the build a much higher API limit than your own computer gets anonymously.
- **Change how often it runs:** edit the `cron` line in `update-profile.yml`. Times are UTC. Every 6 hours is `"0 */6 * * *"`.
- **Turn it off:** **Actions** -> pick the workflow -> **...** menu -> **Disable workflow**.
- **If updates stop:** GitHub pauses scheduled runs in a public repo after about 60 days with no activity. Open the **Actions** tab, re-enable the workflow, and press **Run workflow**.
- **Run it now:** **Actions** -> **Update profile visuals** -> **Run workflow**. Do this after editing `profile.json` if you do not want to wait for the next 3 hours.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Stats stopped updating | Check the latest run under **Actions** for a red cross and read its log. If runs have simply stopped appearing, see "If updates stop" above. |
| My profile shows the original author's stats | The first build has not run. Do step 5. |
| README does not appear on my profile | The repo is not public, or its name is not exactly your username. |
| The Action fails with a permissions error | Do step 4 (read and write permissions). |
| `no calendar cells parsed` | The username is wrong, or the profile does not exist. Check `PROFILE_USER`. |
| Stats look low | Private-repo work only counts if you tick **Include private contributions on my profile** in your profile settings, and the numbers are still read from your public profile. |
| `git push` is rejected | The Action committed while you were editing. Run `git pull --rebase`, then push again. |
| Images are broken inside `themes/<name>/snippet.md` on GitHub | Expected. Its image paths start at the repo root, so they only work once pasted into the root `README.md`. |
| Switch workflow says `no such theme` | The name must match a folder in `themes/` exactly (lowercase). |
| I want different colours | Edit the colour constants at the top of `themes/<name>/generate.py` and push. The Action rebuilds. |
