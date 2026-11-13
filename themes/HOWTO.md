# Themes

One folder per theme. Each holds:

| File | What it is |
|------|-----------|
| `generate.py` | Draws the theme from live GitHub data and writes the two things below |
| `assets/*.svg` | The generated images (committed, refreshed every 3 hours by the workflow) |
| `snippet.md` | The paste-ready README for the repo root. Image paths are root-relative (`./themes/<name>/assets/...`) |

## Use a theme
Copy `themes/<name>/snippet.md` into the root `README.md`, or run **Actions -> Switch README theme** and type the folder name.

## Add a theme
1. Copy a folder: `themes/trading` -> `themes/my-theme`.
2. Edit `my-theme/generate.py`. Shared data (`USER`, `days`, `total`, `streak`, `user`, `repos`, `lang_rows`, `avatar`, ...) comes from `scripts/profile_data.py`; keep the rest as the drawing code.
3. Make sure it writes `assets/*.svg` and `snippet.md` with `./themes/my-theme/assets/...` paths.
4. `PROFILE_USER=you python scripts/build.py` builds every theme; `python scripts/preview.py` makes the local `preview.html` (git-ignored) with a button per theme.

Nothing else needs registering: the workflows pick up every `themes/*/` folder.

## Personal text
`profile.json` at the repo root: `tagline`, `focus` (footer chips), `weakness`. The tagline falls back to your GitHub bio.
