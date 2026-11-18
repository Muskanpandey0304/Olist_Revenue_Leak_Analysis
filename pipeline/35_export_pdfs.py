"""Export the stakeholder memo and the insights report from Markdown to PDF.

Markdown -> styled HTML (python-markdown) -> PDF (headless Microsoft Edge or Google Chrome, no extra install).
Output: reports/stakeholder_memo.pdf and reports/insights_report.pdf

Run:  python pipeline/35_export_pdfs.py
"""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import markdown

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]

CSS = """
@page { size: A4; margin: 14mm 15mm; }
body { font-family: 'Segoe UI', Arial, sans-serif; color: #0B0B0B; font-size: 10pt; line-height: 1.45; }
h1 { font-size: 19pt; margin: 0 0 6pt; color: #1b4f8f; border-bottom: 2px solid #2A78D6; padding-bottom: 4pt; }
h2 { font-size: 12.5pt; margin: 14pt 0 4pt; color: #1b4f8f; }
h3 { font-size: 11pt; margin: 10pt 0 3pt; }
p { margin: 4pt 0; }
ul, ol { margin: 3pt 0 3pt 16pt; padding: 0; }
li { margin: 2pt 0; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0; font-size: 8.5pt; page-break-inside: auto; }
th { background: #2A78D6; color: #fff; text-align: left; padding: 4pt 5pt; }
td { border: 1px solid #d5d4d0; padding: 4pt 5pt; vertical-align: top; }
tr { page-break-inside: avoid; }
tr:nth-child(even) td { background: #f6f6f4; }
code { font-family: Consolas, monospace; font-size: 8.5pt; background: #f1f1ee; padding: 0 2pt; }
blockquote { border-left: 3px solid #EB6834; margin: 6pt 0; padding: 2pt 8pt; color: #333; }
img { max-width: 100%; }
"""


def find_browser() -> str:
    for b in BROWSERS:
        if Path(b).exists():
            return b
    sys.exit("Need Microsoft Edge or Google Chrome installed to print the PDF.")


def to_pdf(md_path: Path, browser: str):
    html_body = markdown.markdown(md_path.read_text(encoding="utf-8"), extensions=["tables", "sane_lists", "nl2br"])
    html = f"<!doctype html><html><head><meta charset='utf-8'><title>{md_path.stem}</title><style>{CSS}</style></head><body>{html_body}</body></html>"
    pdf = md_path.with_suffix(".pdf")
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "page.html"
        page.write_text(html, encoding="utf-8")
        subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--user-data-dir={Path(tmp) / 'profile'}", f"--print-to-pdf={pdf}", page.as_uri()],
                       check=True, capture_output=True, timeout=120)
    print(f"wrote {pdf.relative_to(ROOT)} ({pdf.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    b = find_browser()
    for name in ["stakeholder_memo", "insights_report"]:
        to_pdf(REPORTS / f"{name}.md", b)
