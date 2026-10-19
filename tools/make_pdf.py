"""Render docs/TESLIM.md to docs/TESLIM.pdf with headless Chrome (dev tool, macOS).

Requires: pip install markdown. Uses a throwaway Chrome profile, so a running Chrome is untouched.
"""
from pathlib import Path
import subprocess
import tempfile

import markdown

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'docs/TESLIM.md'
TARGET = ROOT / 'docs/TESLIM.pdf'
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

STYLE = """
@page { size: A4; margin: 16mm 15mm 18mm; }
body { font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif; font-size: 10.5pt;
       line-height: 1.45; color: #1d1d1f; }
h1 { font-size: 20pt; margin: 0 0 10pt; padding-bottom: 6pt; border-bottom: 2px solid #8a1c1c; color: #8a1c1c; }
h2 { font-size: 13.5pt; margin: 16pt 0 6pt; color: #8a1c1c; break-after: avoid; }
p, li { margin: 3pt 0; }
ul, ol { padding-left: 18pt; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0; font-size: 9.5pt; break-inside: avoid; }
th, td { border: 1px solid #c9c9c9; padding: 4pt 6pt; text-align: left; vertical-align: top; }
th { background: #f3eded; }
blockquote { margin: 6pt 0; padding: 5pt 9pt; background: #fbf6e9; border-left: 3px solid #c9a227; }
blockquote p { margin: 0; }
code { font-family: Menlo, Consolas, monospace; font-size: 9pt; background: #f2f2f2; padding: 0 3pt; border-radius: 3px; }
hr { border: 0; border-top: 1px solid #ddd; margin: 12pt 0; }
"""


def main():
    body = markdown.markdown(SOURCE.read_text(encoding='utf-8'), extensions=['tables', 'sane_lists'])
    html = f'<!doctype html><html lang="tr"><head><meta charset="utf-8"><title>Yula Kullanım Rehberi</title>' \
           f'<style>{STYLE}</style></head><body>{body}</body></html>'
    with tempfile.TemporaryDirectory(prefix='yula-pdf-') as work:
        page = Path(work) / 'teslim.html'
        page.write_text(html, encoding='utf-8')
        subprocess.run([CHROME, '--headless=new', '--disable-gpu', f'--user-data-dir={work}/profile',
                        '--no-pdf-header-footer', f'--print-to-pdf={TARGET}', page.as_uri()],
                       check=True, capture_output=True, timeout=120)
    print(TARGET)


if __name__ == '__main__':
    main()
