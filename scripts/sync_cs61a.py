#!/usr/bin/env python
"""Sync public CS61A starter code and study materials into this repo."""

from __future__ import annotations

import json
import re
import shutil
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

BASE_URL = "https://cs61a.org/"
RESOURCES_URL = urllib.parse.urljoin(BASE_URL, "resources/")
ROOT = Path(__file__).resolve().parents[1]
MATERIALS_DIR = ROOT / "materials"
GUIDES_DIR = MATERIALS_DIR / "guides"
STARTER_ZIP_DIR = MATERIALS_DIR / "starter_code"
STARTER_EXTRACT_DIR = MATERIALS_DIR / "starter_code_extracted"
CATALOG_PATH = MATERIALS_DIR / "catalog.json"

GUIDE_LINK_TEXT = {
    "Studying Guide",
    "Composition Guide",
    "MT1 Study Guide",
    "MT2 Study Guide",
    "Final Study Guide",
    "Advice from Students",
    "Scheme Specifications",
    "Scheme Built-In Procedures",
    "Textbook",
    "Python Tutor",
}
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    )
}


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._current_href: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._current_href = dict(attrs).get("href")

    def handle_endtag(self, tag: str) -> None:
        if tag == "a":
            self._current_href = None

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if self._current_href and text:
            self.links.append((text, self._current_href))


@dataclass
class Assignment:
    kind: str
    slug: str
    page_url: str
    zip_url: str | None
    zip_filename: str | None
    title: str


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers=DEFAULT_HEADERS)
    with urllib.request.urlopen(request) as response:
        return response.read().decode("utf-8", errors="ignore")


def fetch_binary(url: str) -> bytes:
    request = urllib.request.Request(url, headers=DEFAULT_HEADERS)
    with urllib.request.urlopen(request) as response:
        return response.read()


def ensure_dirs() -> None:
    for path in [MATERIALS_DIR, GUIDES_DIR, STARTER_ZIP_DIR, STARTER_EXTRACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def normalize_url(url: str, current_page: str = BASE_URL) -> str:
    return urllib.parse.urljoin(current_page, url)


def unique_assignment_pages(home_html: str) -> list[tuple[str, str]]:
    patterns = {
        "lab": r'href="([^"]*/lab/lab\d+/|/lab/lab\d+/)"',
        "hw": r'href="([^"]*/hw/hw\d+/|/hw/hw\d+/)"',
        "proj": r'href="([^"]*/proj/[a-z_]+/?|/proj/[a-z_]+/?)"',
    }
    seen: set[tuple[str, str]] = set()
    results: list[tuple[str, str]] = []
    for kind, pattern in patterns.items():
        for match in re.finditer(pattern, home_html):
            page_url = normalize_url(match.group(1))
            slug = page_url.rstrip("/").split("/")[-1]
            key = (kind, slug)
            if key not in seen:
                seen.add(key)
                results.append((kind, page_url))
    order = {"lab": 0, "hw": 1, "proj": 2}
    return sorted(results, key=lambda item: (order[item[0]], item[1]))


def extract_title(html: str) -> str:
    match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    title = re.sub(r"\s+", " ", match.group(1)).strip()
    return title.replace(" | CS 61A", "")


def discover_zip_url(html: str, page_url: str) -> str | None:
    zip_matches = re.findall(r'href="([^"]+\.zip)"', html, re.IGNORECASE)
    if not zip_matches:
        return None
    return normalize_url(zip_matches[0], page_url)


def discover_assignments() -> list[Assignment]:
    home_html = fetch_text(BASE_URL)
    assignments: list[Assignment] = []
    for kind, page_url in unique_assignment_pages(home_html):
        html = fetch_text(page_url)
        slug = page_url.rstrip("/").split("/")[-1]
        zip_url = discover_zip_url(html, page_url)
        zip_filename = zip_url.split("/")[-1] if zip_url else None
        assignments.append(
            Assignment(
                kind=kind,
                slug=slug,
                page_url=page_url,
                zip_url=zip_url,
                zip_filename=zip_filename,
                title=extract_title(html) or slug,
            )
        )
    return assignments


def save_binary(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def extract_zip(zip_path: Path, dest_dir: Path) -> None:
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(dest_dir)


def sync_assignments(assignments: Iterable[Assignment]) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    for assignment in assignments:
        if not assignment.zip_url or not assignment.zip_filename:
            continue
        zip_path = STARTER_ZIP_DIR / assignment.kind / assignment.zip_filename
        print(f"Downloading starter code: {assignment.slug} -> {zip_path}")
        try:
            save_binary(zip_path, fetch_binary(assignment.zip_url))
            extract_zip(zip_path, STARTER_EXTRACT_DIR / assignment.kind / assignment.slug)
        except (urllib.error.URLError, zipfile.BadZipFile) as exc:
            failures.append(
                {
                    "type": "assignment",
                    "slug": assignment.slug,
                    "url": assignment.zip_url,
                    "error": str(exc),
                }
            )
            print(f"Warning: failed to sync {assignment.slug}: {exc}")
    return failures


def discover_guides() -> list[dict[str, str]]:
    resources_html = fetch_text(RESOURCES_URL)
    parser = LinkParser()
    parser.feed(resources_html)
    guides: list[dict[str, str]] = []
    seen: set[str] = set()
    for text, href in parser.links:
        if text not in GUIDE_LINK_TEXT:
            continue
        url = normalize_url(href, RESOURCES_URL)
        if url in seen:
            continue
        seen.add(url)
        slug = (
            text.lower()
            .replace(" ", "-")
            .replace("/", "-")
            .replace("__", "-")
        )
        suffix = ".pdf" if url.lower().endswith(".pdf") else ".html"
        guides.append({"title": text, "url": url, "filename": f"{slug}{suffix}"})
    return guides


def sync_guides(guides: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    for guide in guides:
        path = GUIDES_DIR / guide["filename"]
        print(f"Downloading guide: {guide['title']} -> {path}")
        try:
            save_binary(path, fetch_binary(guide["url"]))
        except urllib.error.URLError as exc:
            failures.append(
                {
                    "type": "guide",
                    "title": guide["title"],
                    "url": guide["url"],
                    "error": str(exc),
                }
            )
            print(f"Warning: failed to sync guide {guide['title']}: {exc}")
    return failures


def write_catalog(
    assignments: list[Assignment],
    guides: list[dict[str, str]],
    failures: list[dict[str, str]],
) -> None:
    payload = {
        "source": BASE_URL,
        "resources_page": RESOURCES_URL,
        "assignment_count": len(assignments),
        "guide_count": len(guides),
        "assignments": [asdict(item) for item in assignments],
        "guides": guides,
        "sync_failures": failures,
    }
    CATALOG_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    ensure_dirs()
    assignments = discover_assignments()
    guides = discover_guides()
    failures = []
    failures.extend(sync_assignments(assignments))
    failures.extend(sync_guides(guides))
    write_catalog(assignments, guides, failures)
    gitkeep = STARTER_EXTRACT_DIR / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")
    print(f"Wrote catalog to {CATALOG_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
