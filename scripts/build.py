"""Run every theme's generator (themes/*/generate.py). Needs PROFILE_USER locally; in GitHub Actions it defaults to the repo owner."""
import subprocess, sys
from pathlib import Path

for gen in sorted((Path(__file__).resolve().parent.parent / "themes").glob("*/generate.py")):
    print(f"== {gen.parent.name}")
    subprocess.run([sys.executable, str(gen)], check=True)
