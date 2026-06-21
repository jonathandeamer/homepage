#!/usr/bin/env python3
"""Check rendered homepage output for the site's small public contract."""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path


SITE = "https://jonathandeamer.com"
GITHUB_URL = "https://github.com/jonathandeamer"
BLUESKY_URL = "https://bsky.app/profile/jonathandeamer.bsky.social"
REQUIRED_HOME_META = [
    ("property", "og:title"),
    ("property", "og:description"),
    ("property", "og:url"),
    ("name", "twitter:card"),
    ("name", "theme-color"),
]
REQUIRED_404_META = [
    ("name", "robots"),
    ("name", "theme-color"),
    ("property", "og:title"),
    ("property", "og:description"),
    ("property", "og:url"),
    ("name", "twitter:card"),
]
REQUIRED_LLMS_LINKS = [
    ("Homepage", f"{SITE}/"),
    ("Email", "mailto:jonathandeamer@gmail.com"),
    ("LinkedIn", "https://www.linkedin.com/in/jonathandeamer/"),
    ("Wikipedia", "https://en.wikipedia.org/wiki/User:Jonathan_Deamer"),
    ("Strava", "https://www.strava.com/athletes/18361576"),
    ("GitHub", "https://github.com/jonathandeamer"),
    ("Bluesky", "https://bsky.app/profile/jonathandeamer.bsky.social"),
    ("Mastodon", "https://tilde.zone/@JonathanDeamer"),
    ("Threads", "https://www.threads.net/@jonathandeamer"),
    ("Twitter", "https://twitter.com/JonathanDeamer"),
    ("Small Observations", "https://smallobservations.net/"),
    ("Homepage source", "https://github.com/jonathandeamer/homepage"),
    ("Portrait photo", "https://www.flickr.com/photos/jonathandeamer/50782596227/"),
    ("Creative Commons Attribution 4.0", "https://creativecommons.org/licenses/by/4.0/"),
]


class HeadParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.title_parts: list[str] = []
        self.canonical = ""
        self.rel_me = ""
        self.meta: dict[tuple[str, str], str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {name.lower(): value or "" for name, value in attrs}
        if tag.lower() == "title":
            self.in_title = True
            return
        if tag.lower() == "link":
            rels = {part.lower() for part in attr_map.get("rel", "").split()}
            if "canonical" in rels:
                self.canonical = attr_map.get("href", "").strip()
            if "me" in rels:
                self.rel_me = attr_map.get("href", "").strip()
            return
        if tag.lower() == "meta":
            content = attr_map.get("content", "").strip()
            if "property" in attr_map:
                self.meta[("property", attr_map["property"])] = content
            if "name" in attr_map:
                self.meta[("name", attr_map["name"])] = content

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)

    @property
    def title(self) -> str:
        return "".join(self.title_parts).strip()


class CardParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.elements: list[dict] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {name.lower(): value or "" for name, value in attrs}
        self.elements.append(
            {
                "classes": {c for c in attr_map.get("class", "").split() if c},
                "rel": {r.lower() for r in attr_map.get("rel", "").split() if r},
                "href": attr_map.get("href", "").strip(),
            }
        )


def parse_page(path: Path) -> HeadParser:
    parser = HeadParser()
    parser.feed(path.read_text())
    return parser


def audit_page(path: Path, expected_canonical: str, required_meta: list[tuple[str, str]]) -> list[str]:
    label = path.name
    if not path.exists():
        return [f"{label}: missing file"]

    parser = parse_page(path)
    errors: list[str] = []
    if not parser.title:
        errors.append(f"{label}: missing non-empty title")
    if not parser.canonical:
        errors.append(f"{label}: missing non-empty canonical link")
    elif parser.canonical != expected_canonical:
        errors.append(f"{label}: canonical {parser.canonical!r} does not match expected {expected_canonical!r}")
    if parser.rel_me != "https://tilde.zone/@JonathanDeamer":
        errors.append(f"{label}: missing rel=me link")
    if not parser.meta.get(("name", "description"), "").strip():
        errors.append(f"{label}: missing non-empty description")

    for key in required_meta:
        if not parser.meta.get(key, "").strip():
            errors.append(f"{label}: missing non-empty {key[1]}")

    return errors


def audit_home_card(path: Path) -> list[str]:
    label = path.name
    if not path.exists():
        return []

    parser = CardParser()
    parser.feed(path.read_text())
    errors: list[str] = []

    all_classes: set[str] = set()
    for el in parser.elements:
        all_classes |= el["classes"]

    if "h-card" not in all_classes:
        errors.append(f"{label}: missing h-card root")
    for cls in ("p-name", "p-note", "u-photo", "u-email"):
        if cls not in all_classes:
            errors.append(f"{label}: missing {cls} in h-card")

    has_self_url = any(
        ({"u-url", "u-uid"} & el["classes"]) and el["href"] == f"{SITE}/"
        for el in parser.elements
    )
    if not has_self_url:
        errors.append(f"{label}: missing u-url/u-uid resolving to {SITE}/")

    rel_me_hrefs = {el["href"] for el in parser.elements if "me" in el["rel"]}
    for name, url in (("GitHub", GITHUB_URL), ("Bluesky", BLUESKY_URL)):
        if url not in rel_me_hrefs:
            errors.append(f"{label}: missing rel=me for {name}")

    return errors


def audit_sitemap(public_dir: Path) -> list[str]:
    path = public_dir / "sitemap.xml"
    if not path.exists():
        return ["sitemap.xml: missing file"]
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"sitemap.xml: invalid XML: {exc}"]
    urls = [node.text or "" for node in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
    if f"{SITE}/" not in urls:
        return [f"sitemap.xml: missing {SITE}/"]
    if f"{SITE}/404.html" in urls or f"{SITE}/404/" in urls:
        return ["sitemap.xml: must not include 404 page"]
    return []


def audit_robots(public_dir: Path) -> list[str]:
    path = public_dir / "robots.txt"
    if not path.exists():
        return ["robots.txt: missing file"]
    text = path.read_text()
    if f"Sitemap: {SITE}/sitemap.xml" not in text:
        return [f"robots.txt: missing Sitemap: {SITE}/sitemap.xml"]
    return []


def audit_llms(public_dir: Path) -> list[str]:
    path = public_dir / "llms.txt"
    if not path.exists():
        return ["llms.txt: missing file"]

    text = path.read_text()
    errors: list[str] = []
    if not text.startswith("# Jonathan Deamer\n"):
        errors.append("llms.txt: missing # Jonathan Deamer heading")
    if "\n> Personal homepage for Jonathan Deamer" not in text:
        errors.append("llms.txt: missing summary blockquote")
    for label, url in REQUIRED_LLMS_LINKS:
        link = f"[{label}]({url})"
        if link not in text:
            errors.append(f"llms.txt: missing {link}")
    return errors


def audit_rendered_site(public_dir: Path) -> list[str]:
    errors: list[str] = []
    errors.extend(audit_page(public_dir / "index.html", f"{SITE}/", REQUIRED_HOME_META))
    errors.extend(audit_home_card(public_dir / "index.html"))
    errors.extend(audit_page(public_dir / "404.html", f"{SITE}/404.html", REQUIRED_404_META))

    for feed_name in ("feed.xml", "index.xml"):
        if (public_dir / feed_name).exists():
            errors.append(f"{feed_name}: RSS/feed output must not be generated")

    errors.extend(audit_sitemap(public_dir))
    errors.extend(audit_robots(public_dir))
    errors.extend(audit_llms(public_dir))
    return errors


def main(argv: list[str]) -> int:
    public_dir = Path(argv[1]) if len(argv) > 1 else Path("public")
    errors = audit_rendered_site(public_dir)
    if not errors:
        print("    ok")
        return 0
    for error in errors:
        print(f"    {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
