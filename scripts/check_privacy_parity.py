"""Check that the visible privacy page covers the app policy's v2.1 text.

Usage: python scripts/check_privacy_parity.py path/to/docs/PRIVACY_POLICY.md
Uses only the Python standard library. Run after rendering and before review.
"""

from __future__ import annotations

import argparse
import html
import re
from html.parser import HTMLParser
from pathlib import Path


class VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.in_article = False
        self.ignored = 0
        self.headings: list[str] = []
        self.current_heading: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "article":
            self.in_article = True
        if not self.in_article:
            return
        if tag in {"script", "style"}:
            self.ignored += 1
        if tag in {"h1", "h2", "h3"}:
            self.current_heading = []
        if tag in {"p", "li", "td", "th", "h1", "h2", "h3", "blockquote", "br"}:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self.ignored:
            self.ignored -= 1
        if tag in {"h1", "h2", "h3"} and self.current_heading is not None:
            self.headings.append(normalize("".join(self.current_heading)))
            self.current_heading = None
        if tag == "article":
            self.in_article = False
        if tag in {"p", "li", "td", "th", "h1", "h2", "h3"}:
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        if self.in_article and not self.ignored:
            self.parts.append(data)
            if self.current_heading is not None:
                self.current_heading.append(data)


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def markdown_units(source: str) -> tuple[list[str], list[str]]:
    if not source.startswith("---\n"):
        raise ValueError("Expected source front matter")
    _, _, body = source.partition("\n---\n")
    body = body.split("\n— Drafted by Claude", 1)[0]
    headings: list[str] = []
    units: list[str] = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line or line == "---" or re.fullmatch(r"\|?[-:| ]+\|?", line):
            continue
        is_heading = line.startswith("#")
        line = re.sub(r"^#{1,6}\s+", "", line)
        line = re.sub(r"^>\s*|^-\s+", "", line)
        line = re.sub(r"\*\*|(?<!\w)\*(?!\w)|`", "", line)
        if is_heading:
            headings.append(normalize(line))
        if line.startswith("|"):
            units.extend(normalize(cell) for cell in line.strip("|").split("|") if normalize(cell))
        else:
            units.append(normalize(line))
    return headings, units


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--html", type=Path, default=Path("privacy.html"))
    args = parser.parse_args()
    source = args.source.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    page = args.html.read_text(encoding="utf-8")
    expected_headings, units = markdown_units(source)
    visible = VisibleText()
    visible.feed(page)
    text = normalize("".join(visible.parts))
    missing = [unit for unit in units if unit not in text]
    if visible.headings != expected_headings:
        raise SystemExit(f"Heading mismatch:\nexpected {expected_headings}\nactual {visible.headings}")
    if missing:
        raise SystemExit("Missing source text:\n" + "\n".join(missing))
    if "privacy@nepalipay.com" in text:
        raise SystemExit("Stale privacy@nepalipay.com contact remains")
    if "Effective Date: April 25, 2026" in text:
        raise SystemExit("Stale April effective date remains")
    print(f"PASS: {len(expected_headings)} headings and {len(units)} source text units are present in privacy.html")


if __name__ == "__main__":
    main()
