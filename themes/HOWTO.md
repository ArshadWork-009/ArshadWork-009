# Themes

One folder per theme. Each holds:

| File | What it is |
|------|-----------|
| `generate.py` | Draws the theme from live GitHub data and writes the two things below |
| `assets/*.svg` | The generated images (committed, refreshed every 3 hours by the workflow) |
| `snippet.md` | The paste-ready README for the repo root. Image paths are root-relative (`./themes/<name>/assets/...`) |

## Available themes

| Theme | Looks like |
|-------|-----------|
| `default` | a trainer card with rank, streak and language stack, plus a 3D contribution city |
| `trading` | candlestick chart of your weekly commits, order flow, watchlist |
| `terminal` | zsh windows: `whoami`, `git shortlog`, an `nmap`-style language table, a heatmap |
| `soc` | a security-operations console: activity gauge, alert severity, alert calendar |
| `blueprint` | a technical drawing on blue grid paper: one continuous sheet with 4 figures (a weekly activity chart with dimension lines, a hatch-pattern heatmap, schedules for weekday load, languages and stats, and a repo system diagram with a title block) |

## Use a theme
Copy `themes/<name>/snippet.md` into the root `README.md`, or run **Actions -> Switch README theme** and pick the theme from the drop-down.

## Add a theme
1. Copy a folder: `themes/trading` -> `themes/my-theme`.
2. Edit `my-theme/generate.py`. Shared data (`USER`, `days`, `total`, `streak`, `user`, `repos`, `lang_rows`, `avatar`, ...) comes from `scripts/profile_data.py`; keep the rest as the drawing code.
3. Make sure it writes `assets/*.svg` and `snippet.md` with `./themes/my-theme/assets/...` paths.
4. `PROFILE_USER=you python scripts/build.py` builds every theme; `python scripts/preview.py` makes the local `preview.html` (git-ignored) with a button per theme.

The build picks up every `themes/*/` folder by itself. To make a new theme selectable in the **Switch README theme** drop-down, also add its name to the `options:` list in `.github/workflows/switch-theme.yml`.

## Personal text
`profile.json` at the repo root: `tagline`, `focus` (footer chips), `weakness`. The tagline falls back to your GitHub bio.
