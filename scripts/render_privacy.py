"""Render the app's reviewed Markdown candidate into the policy site's HTML shell.

Usage: python scripts/render_privacy.py path/to/docs/PRIVACY_POLICY.md
Requires markdown-it-py. The source stays in the app repository; this script
does not change the source or publish the generated page.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from markdown_it import MarkdownIt


def policy_body(source: str) -> str:
    if not source.startswith("---\n"):
        raise ValueError("Expected YAML front matter")
    _, _, remainder = source.partition("\n---\n")
    if not remainder:
        raise ValueError("Missing closing YAML front matter delimiter")
    # The drafting attribution and PDF maintenance instruction are internal
    # review notes, not part of the customer-facing policy.
    remainder = remainder.split("\n— Drafted by Claude", 1)[0].strip()
    if "**Version:** 2.1" not in remainder:
        raise ValueError("Expected the v2.1 privacy policy candidate")
    return "\n".join(line for line in remainder.splitlines() if line.strip() != "---")


def render(source: str) -> str:
    body = policy_body(source)
    content = MarkdownIt("commonmark").enable("table").render(body)
    content = content.replace("<p><strong>Effective Date:", '<p class="doc-meta"><strong>Effective Date:', 1)
    meta_start = content.index('<p class="doc-meta">')
    meta_end = content.index("</p>", meta_start)
    content = content[:meta_start] + content[meta_start:meta_end].replace("\n", "<br />\n") + content[meta_end:]
    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Privacy Policy — NepaliPay</title>
    <meta name="description" content="How NepaliPay collects, uses, and protects your personal information." />
    <link rel="stylesheet" href="assets/doc.css" />
  </head>
  <body>
    <article class="doc">
      <a href="index.html" class="doc-back">All policies</a>
      <p class="doc-eyebrow">Legal</p>
{''.join('      ' + line if line.strip() else line for line in content.splitlines(keepends=True))}
      <div class="doc-foot">
        Last updated May 2026 · Version 2.1. The <a href="PRIVACY_POLICY.pdf">PDF is an archived prior version</a>.
      </div>
    </article>
  </body>
</html>
'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="App repository docs/PRIVACY_POLICY.md")
    parser.add_argument("--output", type=Path, default=Path("privacy.html"))
    args = parser.parse_args()
    source = args.source.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    args.output.write_text(render(source), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
