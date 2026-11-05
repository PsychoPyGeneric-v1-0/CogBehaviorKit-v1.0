"""Converts README.md (and the tutorials) to .html files with real, readable tables.
Open the .html in any web browser (double-click). Needs:  pip install markdown
Usage:  python tools/make_readme_html.py
"""
from pathlib import Path
import markdown

ROOT = Path(__file__).resolve().parents[1]
CSS = """
body{font-family:Segoe UI,Arial,sans-serif;max-width:60rem;margin:2rem auto;padding:0 1rem;line-height:1.55;color:#222}
h1,h2,h3{border-bottom:1px solid #ddd;padding-bottom:.2rem;margin-top:2rem}
table{border-collapse:collapse;margin:1rem 0;width:100%}
th,td{border:1px solid #bbb;padding:.4rem .7rem;text-align:left;vertical-align:top}
th{background:#eef2f7}
tr:nth-child(even) td{background:#fafafa}
code{background:#f3f3f3;padding:.1rem .3rem;border-radius:3px;font-family:Consolas,monospace}
pre{background:#f3f3f3;padding:.8rem;border-radius:5px;overflow-x:auto}
pre code{background:none;padding:0}
blockquote{border-left:4px solid #e0a800;margin:1rem 0;padding:.2rem 1rem;background:#fff8e1}
"""

for md_file in [ROOT / "README.md", *sorted((ROOT / "tutorials").glob("*.md"))]:
    body = markdown.markdown(md_file.read_text(encoding="utf-8"), extensions=["tables", "fenced_code"])
    html = (f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{md_file.stem}</title>"
            f"<style>{CSS}</style></head><body>{body}</body></html>")
    md_file.with_suffix(".html").write_text(html, encoding="utf-8")
    print("written:", md_file.with_suffix(".html").relative_to(ROOT))
