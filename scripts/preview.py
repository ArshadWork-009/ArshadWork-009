"""Build preview.html (git-ignored): every theme's snippet.md with a button to switch between them. Open it from the repo root."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
themes = {p.parent.name: p.read_text(encoding="utf-8") for p in sorted((root / "themes").glob("*/snippet.md"))}
buttons = "".join(f'<button data-t="{n}">{n}</button>' for n in themes)
(root / "preview.html").write_text(f'''<!doctype html>
<html><head><meta charset="utf-8"><title>README preview</title>
<style>
  body{{background:#0d1117;color:#e6edf3;font-family:-apple-system,Segoe UI,sans-serif;margin:0;padding:32px}}
  .bar{{max-width:900px;margin:0 auto 16px;display:flex;gap:8px}}
  button{{background:#21262d;color:#e6edf3;border:1px solid #30363d;border-radius:6px;padding:6px 14px;cursor:pointer;font:inherit;text-transform:capitalize}}
  button.on{{background:#238636;border-color:#2ea043}}
  .box{{max-width:900px;margin:auto;border:1px solid #30363d;border-radius:6px;padding:32px}}
  img{{max-width:100%}} a{{color:#58a6ff}}
</style></head><body>
<div class="bar">{buttons}</div><div class="box" id="box"></div>
<script>
const T = {json.dumps(themes)};
const show = n => {{ box.innerHTML = T[n]; document.querySelectorAll("button").forEach(b => b.classList.toggle("on", b.dataset.t === n)); }};
document.querySelectorAll("button").forEach(b => b.onclick = () => show(b.dataset.t));
show(Object.keys(T)[0]);
</script></body></html>''', encoding="utf-8")
print("preview.html written (git-ignored)")
