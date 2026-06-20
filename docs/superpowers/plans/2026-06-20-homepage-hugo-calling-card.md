# Homepage Hugo Calling Card Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the manually maintained static homepage with a tiny Hugo calling-card site that preserves the current URL contract and adds the workflow benefits from `small-observations`.

**Architecture:** The repo becomes a normal Hugo project with one local theme, `themes/calling-card`. Homepage facts live in `content/_index.md`; rendering, CSS, font, metadata, and 404 handling live in the theme. Build, checks, and deployment run through `make`; deployment writes a generated Hugo deploy config from explicit environment variables so production uploads fail closed until AWS values are verified.

**Tech Stack:** Hugo 0.161 extended with deploy support, Make, Python 3 standard library `unittest` and `html.parser`, self-hosted Fraunces WOFF2, no runtime JavaScript.

---

## File Structure

Create or modify these files:

- Modify: `.gitignore` — replace the old allowlist with normal generated/local ignores.
- Create: `hugo.toml` — Hugo site config for apex domain, local theme, no feed.
- Create: `Makefile` — `dev`, `build`, `test`, `check`, `clean`, `deploy`, `deploy-dry`.
- Create: `CLAUDE.md` — repo guidance for future agent work.
- Create: `content/_index.md` — editable homepage data.
- Create: `assets/img/jonathan-deamer.png` — portrait copied from `~/Downloads`.
- Create: `themes/calling-card/layouts/_default/baseof.html` — shared HTML shell.
- Create: `themes/calling-card/layouts/index.html` — homepage card rendering.
- Create: `themes/calling-card/layouts/404.html` — root `public/404.html`.
- Create: `themes/calling-card/layouts/partials/head-meta.html` — canonical, OG/Twitter, favicon, font preload.
- Create: `themes/calling-card/layouts/partials/footer.html` — licence footer.
- Create: `themes/calling-card/layouts/robots.txt` — allow all + sitemap.
- Create: `themes/calling-card/assets/css/site.css` — one hand-written stylesheet, inlined.
- Create: `themes/calling-card/static/fonts/fraunces-latin.woff2` — copied from `small-observations`.
- Create: `themes/calling-card/static/favicon.png` — copied from `~/Downloads`.
- Create: `scripts/check_rendered_site.py` — rendered contract checker.
- Create: `scripts/write_deploy_config.py` — generated Hugo deploy config writer.
- Create: `tests/test_check_rendered_site.py` — unit tests for rendered checker.
- Create: `tests/test_write_deploy_config.py` — unit tests for deploy config writer.
- Create: `.githooks/commit-msg` — conventional commit hook for this repo.
- Delete: `index.html`, `404.html`, `style.css` — old root static source files after Hugo equivalents build.

---

### Task 1: Replace Ignore File And Make Docs Trackable

**Files:**
- Modify: `.gitignore`
- Track: `docs/superpowers/specs/2026-06-20-homepage-hugo-calling-card-design.md`
- Track: `docs/superpowers/plans/2026-06-20-homepage-hugo-calling-card.md`

- [ ] **Step 1: Replace `.gitignore`**

Replace `.gitignore` with exactly:

```gitignore
.DS_Store

# Hugo output and caches
public/
resources/_gen/
.hugo_build.lock

# Generated deploy config written from local environment variables
.hugo-deploy.generated.toml

# Local worktrees and brainstorming/mockup scratch files
.worktrees/
.superpowers/
```

- [ ] **Step 2: Verify docs are no longer ignored**

Run:

```bash
git check-ignore -v docs/superpowers/specs/2026-06-20-homepage-hugo-calling-card-design.md docs/superpowers/plans/2026-06-20-homepage-hugo-calling-card.md || true
```

Expected: no output.

- [ ] **Step 3: Verify local scratch files stay ignored**

Run:

```bash
git check-ignore -v .worktrees/example .superpowers/example public/index.html .hugo-deploy.generated.toml
```

Expected: four lines showing `.gitignore` rules for `.worktrees/`, `.superpowers/`, `public/`, and `.hugo-deploy.generated.toml`.

- [ ] **Step 4: Commit**

Run:

```bash
git add .gitignore docs/superpowers/specs/2026-06-20-homepage-hugo-calling-card-design.md docs/superpowers/plans/2026-06-20-homepage-hugo-calling-card.md
git commit -m "build(config): replace static-site ignore rules"
```

Expected: commit succeeds and docs are tracked without `git add -f`.

---

### Task 2: Add Rendered Site Contract Checker

**Files:**
- Create: `tests/test_check_rendered_site.py`
- Create: `scripts/check_rendered_site.py`

- [ ] **Step 1: Create failing tests**

Create `tests/test_check_rendered_site.py`:

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from scripts.check_rendered_site import audit_rendered_site


SITE = "https://jonathandeamer.com"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


HOME_HEAD = f"""
<title>Jonathan Deamer</title>
<meta name="description" content="Places you can find Jonathan Deamer online, and ways to get in touch.">
<meta name="theme-color" content="#203125">
<link rel="canonical" href="{SITE}/">
<link rel="me" href="https://tilde.zone/@JonathanDeamer">
<meta property="og:title" content="Jonathan Deamer">
<meta property="og:description" content="Places you can find Jonathan Deamer online, and ways to get in touch.">
<meta property="og:url" content="{SITE}/">
<meta name="twitter:card" content="summary_large_image">
"""


NOT_FOUND_HEAD = f"""
<title>404 — Jonathan Deamer</title>
<meta name="robots" content="noindex, nofollow">
<meta name="description" content="404 error">
<meta name="theme-color" content="#203125">
<link rel="canonical" href="{SITE}/404.html">
<link rel="me" href="https://tilde.zone/@JonathanDeamer">
<meta property="og:title" content="404 — Jonathan Deamer">
<meta property="og:description" content="404 error">
<meta property="og:url" content="{SITE}/404.html">
<meta name="twitter:card" content="summary">
"""


def page(head: str, body: str = "<h1>Jonathan Deamer</h1>") -> str:
    return f"<!doctype html><html lang='en-gb'><head>{head}</head><body>{body}</body></html>"


class RenderedSiteAuditTests(TestCase):
    def test_accepts_valid_rendered_site(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "index.html", page(HOME_HEAD))
            write(root / "404.html", page(NOT_FOUND_HEAD, "<h1>404: there's nothing here</h1>"))
            write(root / "sitemap.xml", f"<?xml version='1.0'?><urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'><url><loc>{SITE}/</loc></url></urlset>")
            write(root / "robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")

            self.assertEqual(audit_rendered_site(root), [])

    def test_reports_missing_files_and_unwanted_feeds(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "feed.xml", "<rss></rss>")
            write(root / "index.xml", "<rss></rss>")

            self.assertEqual(
                audit_rendered_site(root),
                [
                    "index.html: missing file",
                    "404.html: missing file",
                    "feed.xml: RSS/feed output must not be generated",
                    "index.xml: RSS/feed output must not be generated",
                    "sitemap.xml: missing file",
                    "robots.txt: missing file",
                ],
            )

    def test_reports_missing_home_metadata(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "index.html", page("<title></title>"))
            write(root / "404.html", page(NOT_FOUND_HEAD, "<h1>404: there's nothing here</h1>"))
            write(root / "sitemap.xml", "<?xml version='1.0'?><urlset></urlset>")
            write(root / "robots.txt", "User-agent: *\n")

            self.assertIn("index.html: missing non-empty canonical link", audit_rendered_site(root))
            self.assertIn("index.html: missing rel=me link", audit_rendered_site(root))
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python3 -m unittest tests/test_check_rendered_site.py
```

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.check_rendered_site'`.

- [ ] **Step 3: Add checker implementation**

Create `scripts/check_rendered_site.py`:

```python
#!/usr/bin/env python3
"""Check rendered homepage output for the site's small public contract."""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path


SITE = "https://jonathandeamer.com"
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
    if parser.canonical != expected_canonical:
        errors.append(f"{label}: missing non-empty canonical link")
    if parser.rel_me != "https://tilde.zone/@JonathanDeamer":
        errors.append(f"{label}: missing rel=me link")
    if not parser.meta.get(("name", "description"), "").strip():
        errors.append(f"{label}: missing non-empty description")

    for key in required_meta:
        if not parser.meta.get(key, "").strip():
            errors.append(f"{label}: missing non-empty {key[1]}")

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


def audit_rendered_site(public_dir: Path) -> list[str]:
    errors: list[str] = []
    errors.extend(audit_page(public_dir / "index.html", f"{SITE}/", REQUIRED_HOME_META))
    errors.extend(audit_page(public_dir / "404.html", f"{SITE}/404.html", REQUIRED_404_META))

    for feed_name in ("feed.xml", "index.xml"):
        if (public_dir / feed_name).exists():
            errors.append(f"{feed_name}: RSS/feed output must not be generated")

    errors.extend(audit_sitemap(public_dir))
    errors.extend(audit_robots(public_dir))
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
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```bash
python3 -m unittest tests/test_check_rendered_site.py
```

Expected: `OK`.

- [ ] **Step 5: Commit**

Run:

```bash
git add scripts/check_rendered_site.py tests/test_check_rendered_site.py
git commit -m "build(script): add rendered site contract check"
```

Expected: commit succeeds.

---

### Task 3: Build Hugo Site And Calling Card Theme

**Files:**
- Create: `hugo.toml`
- Create: `Makefile`
- Create: `content/_index.md`
- Create: `assets/img/jonathan-deamer.png`
- Create: `themes/calling-card/layouts/_default/baseof.html`
- Create: `themes/calling-card/layouts/index.html`
- Create: `themes/calling-card/layouts/404.html`
- Create: `themes/calling-card/layouts/partials/head-meta.html`
- Create: `themes/calling-card/layouts/partials/footer.html`
- Create: `themes/calling-card/layouts/robots.txt`
- Create: `themes/calling-card/assets/css/site.css`
- Create: `themes/calling-card/static/fonts/fraunces-latin.woff2`
- Create: `themes/calling-card/static/favicon.png`
- Delete: `index.html`
- Delete: `404.html`
- Delete: `style.css`

- [ ] **Step 1: Copy binary assets**

Run:

```bash
mkdir -p assets/img themes/calling-card/static/fonts themes/calling-card/static
cp /Users/jonathan/Downloads/jonathan-deamer.png assets/img/jonathan-deamer.png
cp /Users/jonathan/Downloads/favicon.png themes/calling-card/static/favicon.png
cp /Users/jonathan/small-observations/themes/notebook/static/fonts/fraunces-latin.woff2 themes/calling-card/static/fonts/fraunces-latin.woff2
```

Expected: all three files exist in the repo.

- [ ] **Step 2: Create Hugo config**

Create `hugo.toml`:

```toml
baseURL = "https://jonathandeamer.com/"
defaultContentLanguage = "en-gb"
locale = "en-gb"
title = "Jonathan Deamer"
theme = "calling-card"
enableRobotsTXT = true
disableKinds = ["taxonomy", "term", "section", "RSS"]
disableHugoGeneratorInject = true

[outputs]
  home = ["HTML"]
  page = ["HTML"]

[imaging]
  quality = 82
  resampleFilter = "Lanczos"
  hint = "photo"
  anchor = "smart"

[minify]
  minifyOutput = true

[params]
  author = "Jonathan Deamer"
  description = "Places you can find Jonathan Deamer online, and ways to get in touch."
  themeColor = "#203125"
```

- [ ] **Step 3: Create homepage content**

Create `content/_index.md`:

```yaml
---
title: "Jonathan Deamer"
description: "Places you can find Jonathan Deamer online, and ways to get in touch."
intro: "Places you can find me online, and ways to get in touch."
portrait:
  src: "img/jonathan-deamer.png"
  alt: "Photo of Jonathan Deamer"
  href: "https://www.flickr.com/photos/jonathandeamer/50782596227/"
links:
  - label: "Contact"
    items:
      - name: "Email"
        url: "mailto:jonathandeamer@gmail.com"
  - label: "Professional"
    items:
      - name: "LinkedIn"
        url: "https://www.linkedin.com/in/jonathandeamer/"
  - label: "Social"
    items:
      - name: "Bluesky"
        url: "https://bsky.app/profile/jonathandeamer.bsky.social"
      - name: "Mastodon"
        url: "https://tilde.zone/@JonathanDeamer"
        rel: "me"
      - name: "Threads"
        url: "https://www.threads.net/@jonathandeamer"
      - name: "Twitter"
        url: "https://twitter.com/JonathanDeamer"
  - label: "Elsewhere"
    items:
      - name: "Wikipedia"
        url: "https://en.wikipedia.org/wiki/User:Jonathan_Deamer"
      - name: "Strava"
        url: "https://www.strava.com/athletes/18361576"
license:
  text: "Everything on this site CC-BY unless otherwise stated."
  url: "https://creativecommons.org/licenses/by/4.0/"
---
```

- [ ] **Step 4: Create `Makefile` without deploy targets**

Create `Makefile`:

```make
# Jonathan Deamer homepage — common tasks

.DEFAULT_GOAL := help
.PHONY: help dev build test check clean

help:  ## list available targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

dev:  ## hugo dev server
	hugo server --port 1313 --bind 127.0.0.1

build:  ## clean production build
	hugo --cleanDestinationDir --minify --gc --printPathWarnings

test:  ## run unit tests for local scripts
	python3 -m unittest discover -s tests -p 'test_*.py'

check: build test  ## build then sanity-check rendered output
	@echo
	@echo "→ rendered site contract:"
	@python3 scripts/check_rendered_site.py public
	@echo
	@if command -v htmltest >/dev/null 2>&1; then \
		echo "→ htmltest (internal link check):"; \
		htmltest -s public 2>&1 | tail -15; \
	else \
		echo "→ htmltest not installed (skipping link check)"; \
		echo "    install with: brew install htmltest"; \
	fi
	@echo
	@if command -v pa11y >/dev/null 2>&1; then \
		echo "→ pa11y (accessibility audit on homepage):"; \
		pa11y "file://$(PWD)/public/index.html"; \
		echo; \
		echo "→ pa11y (accessibility audit on 404):"; \
		pa11y "file://$(PWD)/public/404.html"; \
	else \
		echo "→ pa11y not installed (skipping accessibility check)"; \
		echo "    install with: npm install -g pa11y"; \
	fi
	@echo
	@if command -v vnu >/dev/null 2>&1 || java -jar ~/.vnu/vnu.jar --version >/dev/null 2>&1; then \
		echo "→ vnu HTML validation:"; \
		java -jar ~/.vnu/vnu.jar --skip-non-html "public/index.html" "public/404.html" 2>&1 | head -30 \
			&& echo "    ok" || true; \
	else \
		echo "→ vnu HTML validator not installed (skipping)"; \
		echo "    install: mkdir -p ~/.vnu && curl -sL https://github.com/validator/validator/releases/latest/download/vnu.jar -o ~/.vnu/vnu.jar"; \
	fi
	@echo
	@echo "→ sitemap:"
	@test -s public/sitemap.xml \
		&& xmllint --noout public/sitemap.xml 2>&1 \
		&& echo "    ok" \
		|| echo "    INVALID or missing — see errors above"
	@echo

clean:  ## remove generated output
	rm -rf public resources/_gen .hugo_build.lock .hugo-deploy.generated.toml
```

- [ ] **Step 5: Create base template**

Create `themes/calling-card/layouts/_default/baseof.html`:

```html
<!doctype html>
<html lang="{{ site.Language.Lang | default "en-gb" }}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ block "title" . }}{{ site.Title }}{{ end }}</title>
  {{ partial "head-meta.html" . }}
  {{ block "head" . }}{{ end }}
</head>
<body>
  <a class="skip-nav" href="#main-content">Skip to content</a>
  <main class="page" id="main-content">
    {{ block "main" . }}{{ end }}
    {{ partial "footer.html" . }}
  </main>
</body>
</html>
```

- [ ] **Step 6: Create metadata partial**

Create `themes/calling-card/layouts/partials/head-meta.html`:

```html
{{ $description := .Description | default site.Params.description }}
{{ $themeColor := site.Params.themeColor | default "#203125" }}
{{ $canonical := .Permalink }}
{{ if eq .Kind "404" }}{{ $canonical = "404.html" | absURL }}{{ end }}

<meta name="description" content="{{ $description }}">
<meta name="theme-color" content="{{ $themeColor }}">
<link rel="canonical" href="{{ $canonical }}">
<link rel="icon" type="image/png" href="{{ "favicon.png" | relURL }}">
<link rel="preload" href="{{ "fonts/fraunces-latin.woff2" | relURL }}" as="font" type="font/woff2" crossorigin>
<link rel="me" href="https://tilde.zone/@JonathanDeamer">

{{ with resources.Get "css/site.css" | minify | fingerprint }}
  <style>{{ .Content | safeCSS }}</style>
{{ end }}

{{ $ogTitle := site.Title }}
{{ if not .IsHome }}{{ $ogTitle = printf "%s — %s" .Title site.Title }}{{ end }}
{{ if eq .Kind "404" }}{{ $ogTitle = printf "404 — %s" site.Title }}{{ end }}
<meta property="og:site_name" content="{{ site.Title }}">
<meta property="og:title" content="{{ $ogTitle }}">
<meta property="og:description" content="{{ $description }}">
<meta property="og:url" content="{{ $canonical }}">
<meta property="og:type" content="website">
<meta property="og:locale" content="en_GB">

{{ $portrait := "" }}
{{ $portraitAlt := "" }}
{{ if .IsHome }}
  {{ $portrait = .Params.portrait.src }}
  {{ $portraitAlt = .Params.portrait.alt }}
{{ end }}
{{ with $portrait }}
  {{ with resources.Get . }}
    {{ $og := .Resize "1200x1200 webp q82" }}
    <meta property="og:image" content="{{ $og.Permalink }}">
    <meta property="og:image:width" content="{{ $og.Width }}">
    <meta property="og:image:height" content="{{ $og.Height }}">
    {{ with $portraitAlt }}<meta property="og:image:alt" content="{{ . }}">{{ end }}
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:image" content="{{ $og.Permalink }}">
    {{ with $portraitAlt }}<meta name="twitter:image:alt" content="{{ . }}">{{ end }}
  {{ end }}
{{ else }}
  <meta name="twitter:card" content="summary">
{{ end }}
```

- [ ] **Step 7: Create homepage template**

Create `themes/calling-card/layouts/index.html`:

```html
{{ define "main" }}
{{ $portrait := resources.Get .Params.portrait.src }}
{{ if not $portrait }}{{ errorf "missing portrait asset %q" .Params.portrait.src }}{{ end }}
{{ $portraitWebp := $portrait.Resize "360x360 webp q82" }}
{{ $portraitPng := $portrait.Resize "360x360 png" }}

<article class="card" aria-labelledby="site-title">
  <div class="card-copy">
    <p class="eyebrow">Personal homepage</p>
    <h1 id="site-title">{{ .Title }}</h1>
    <p class="intro">{{ .Params.intro }}</p>

    <nav class="link-groups" aria-label="Places to find Jonathan online">
      {{ range .Params.links }}
        <section class="link-group" aria-labelledby="links-{{ .label | anchorize }}">
          <h2 id="links-{{ .label | anchorize }}">{{ .label }}</h2>
          <ul>
            {{ range .items }}
              <li><a href="{{ .url }}"{{ with .rel }} rel="{{ . }}"{{ end }}>{{ .name }}</a></li>
            {{ end }}
          </ul>
        </section>
      {{ end }}
    </nav>
  </div>

  <aside class="portrait" aria-label="Portrait">
    <a href="{{ .Params.portrait.href }}">
      <picture>
        <source type="image/webp" srcset="{{ $portraitWebp.RelPermalink }}">
        <img src="{{ $portraitPng.RelPermalink }}" alt="{{ .Params.portrait.alt }}" width="{{ $portraitPng.Width }}" height="{{ $portraitPng.Height }}">
      </picture>
    </a>
  </aside>
</article>
{{ end }}
```

- [ ] **Step 8: Create 404 template**

Create `themes/calling-card/layouts/404.html`:

```html
{{ define "title" }}404 — {{ site.Title }}{{ end }}
{{ define "head" }}<meta name="robots" content="noindex, nofollow">{{ end }}
{{ define "main" }}
<article class="card notfound" aria-labelledby="notfound-title">
  <div class="card-copy">
    <p class="eyebrow">Page not found</p>
    <h1 id="notfound-title">404: there's nothing here</h1>
    <p class="intro">Sorry :(</p>
    <p><a href="mailto:jonathandeamer@gmail.com">Get in touch</a> if you were looking for something specific — I used to write lots about music and tech in particular, and that no longer lives on this domain.</p>
    <p><a href="{{ "/" | relURL }}">Back to the homepage</a></p>
  </div>
</article>
{{ end }}
```

- [ ] **Step 9: Create footer and robots templates**

Create `themes/calling-card/layouts/partials/footer.html`:

```html
<footer class="site-footer">
  <p>Everything on this site <a href="https://creativecommons.org/licenses/by/4.0/" rel="license">CC-BY</a> unless otherwise stated.</p>
</footer>
```

Create `themes/calling-card/layouts/robots.txt`:

```txt
User-agent: *
Allow: /

Sitemap: {{ site.BaseURL }}sitemap.xml
```

- [ ] **Step 10: Create stylesheet**

Create `themes/calling-card/assets/css/site.css`:

```css
@font-face {
  font-family: "Fraunces";
  font-weight: 100 900;
  font-style: normal;
  font-display: swap;
  src: url("/fonts/fraunces-latin.woff2") format("woff2");
}

:root {
  --bg: #17251b;
  --panel: #203125;
  --panel-soft: #273a2d;
  --ink: #f2eadf;
  --ink-soft: #d9d0c2;
  --muted: #a9bd98;
  --rule: #7b8f6e;
  --accent: #d86847;
  --accent-strong: #f07c55;
  --shadow: rgba(0, 0, 0, 0.28);
  --serif: "Fraunces", "Iowan Old Style", "Hoefler Text", Georgia, serif;
}

* { box-sizing: border-box; }

:focus-visible {
  outline: 2px solid var(--accent-strong);
  outline-offset: 4px;
}

html {
  min-height: 100%;
  background: radial-gradient(circle at 15% 15%, #253a2b 0, var(--bg) 35rem);
}

body {
  min-height: 100vh;
  margin: 0;
  color: var(--ink);
  background: transparent;
  font-family: var(--serif);
  font-variation-settings: "opsz" 18, "SOFT" 45;
  font-size: clamp(17px, 1vw + 14px, 19px);
  line-height: 1.55;
}

a {
  color: var(--accent-strong);
  text-decoration-thickness: 1px;
  text-underline-offset: 0.16em;
}

a:hover {
  color: var(--ink);
}

img {
  display: block;
  max-width: 100%;
  height: auto;
}

.skip-nav {
  position: absolute;
  top: -100%;
  left: 1rem;
  z-index: 10;
  padding: 0.5rem 1rem;
  color: var(--bg);
  background: var(--ink);
  text-decoration: none;
}

.skip-nav:focus {
  top: 1rem;
}

.page {
  width: min(100% - 2rem, 62rem);
  min-height: 100vh;
  margin: 0 auto;
  padding: clamp(1.5rem, 5vw, 4rem) 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(14rem, 20rem);
  gap: clamp(1.25rem, 4vw, 3rem);
  align-items: center;
  padding: clamp(1.25rem, 4vw, 3rem);
  border: 1px solid color-mix(in srgb, var(--rule) 78%, transparent);
  background: linear-gradient(135deg, var(--panel), var(--panel-soft));
  box-shadow: 0 1.4rem 4rem var(--shadow);
}

.eyebrow {
  margin: 0 0 0.65rem;
  color: var(--muted);
  font-variant-caps: all-small-caps;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.12em;
  font-size: 0.86rem;
}

h1 {
  margin: 0;
  font-weight: 520;
  font-size: clamp(2.5rem, 7vw, 5rem);
  line-height: 0.94;
  font-variation-settings: "opsz" 120, "SOFT" 90, "WONK" 1;
}

.intro {
  max-width: 32rem;
  margin: 1rem 0 1.4rem;
  color: var(--ink-soft);
  font-size: 1.1rem;
}

.link-groups {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem 1.5rem;
  max-width: 34rem;
}

.link-group {
  padding-top: 0.8rem;
  border-top: 1px solid color-mix(in srgb, var(--rule) 72%, transparent);
}

.link-group h2 {
  margin: 0 0 0.35rem;
  color: var(--muted);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  font-size: 0.82rem;
  font-weight: 560;
}

.link-group ul {
  list-style: none;
  margin: 0;
  padding: 0;
}

.link-group li {
  margin: 0.16rem 0;
}

.portrait {
  justify-self: end;
}

.portrait a {
  display: block;
  padding: 0.45rem;
  border: 1px solid var(--rule);
  background: color-mix(in srgb, var(--bg) 52%, transparent);
}

.portrait img {
  width: min(100%, 20rem);
  aspect-ratio: 1 / 1;
  object-fit: cover;
}

.site-footer {
  margin-top: 1rem;
  color: var(--muted);
  font-size: 0.88rem;
  text-align: center;
}

.site-footer p {
  margin: 0;
}

.notfound {
  grid-template-columns: minmax(0, 40rem);
  justify-content: start;
}

.notfound h1 {
  font-size: clamp(2rem, 5vw, 3.6rem);
}

.notfound p {
  max-width: 38rem;
  color: var(--ink-soft);
}

@media (max-width: 760px) {
  .page {
    justify-content: flex-start;
  }

  .card {
    grid-template-columns: 1fr;
  }

  .portrait {
    justify-self: start;
    order: -1;
  }

  .portrait img {
    width: min(100%, 14rem);
  }

  .link-groups {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 11: Remove old static source files**

Run:

```bash
git rm index.html 404.html style.css
```

Expected: files are staged for deletion.

- [ ] **Step 12: Build and run checks**

Run:

```bash
make build
python3 scripts/check_rendered_site.py public
```

Expected: Hugo build exits 0 and rendered site contract prints `ok`.

- [ ] **Step 13: Commit**

Run:

```bash
git add hugo.toml Makefile content themes assets
git add -u index.html 404.html style.css
git commit -m "feat(home): migrate calling card to hugo"
```

Expected: commit succeeds.

---

### Task 4: Add Repo Guidance And Commit Hook

**Files:**
- Create: `CLAUDE.md`
- Create: `.githooks/commit-msg`

- [ ] **Step 1: Create `CLAUDE.md`**

Create `CLAUDE.md`:

```markdown
# CLAUDE.md

This file provides guidance to coding agents working in this repository.

## What this is

This is the Hugo source for `https://jonathandeamer.com/`, a tiny personal calling-card homepage. It is intentionally not a blog, portfolio, feed, or app. Preserve the current public contract: `/`, `/404.html`, no RSS feed, no extra public pages unless the user explicitly asks.

Design rationale lives in `docs/superpowers/specs/`. Implementation plans live in `docs/superpowers/plans/`. Read them before non-trivial changes.

## Commands

Use `make`, not plain `hugo`.

```text
make dev          # local Hugo server
make build        # clean production build
make test         # unit tests for local scripts
make check        # build + rendered/a11y/html checks
make clean        # remove generated output
make deploy-dry   # generated deploy config + Hugo deploy dry run
make deploy       # production deploy to S3 + CloudFront
```

## Site constraints

- One local theme: `themes/calling-card`.
- Editable homepage data lives in `content/_index.md`.
- No runtime JavaScript.
- No third-party requests.
- One self-hosted expressive serif font.
- The portrait source is `assets/img/jonathan-deamer.png`.
- CSS is hand-written in one file and inlined by Hugo.
- Keep the apex domain `https://jonathandeamer.com/`.
- Keep `rel="me"` for `https://tilde.zone/@JonathanDeamer`.
- Use British English for public-facing copy.

## Deployment

Deployment uses Hugo's deployer with S3 and CloudFront. `make deploy` and `make deploy-dry` require:

```text
HOMEPAGE_S3_URL
HOMEPAGE_CLOUDFRONT_DISTRIBUTION_ID
HOMEPAGE_AWS_PROFILE
```

Do not guess AWS values. If they are not available, fail clearly and ask the user.
```

- [ ] **Step 2: Create commit hook**

Create `.githooks/commit-msg`:

```bash
#!/usr/bin/env bash
# Enforce conventional commits with a required scope.

set -e

msg_file="$1"
first_line=$(head -n1 "$msg_file")

if [[ "$first_line" =~ ^(Merge|Revert|fixup!|squash!|amend!)\  ]]; then
  exit 0
fi

types='feat|fix|style|refactor|docs|chore|build'
scopes='home|404|css|font|asset|config|script|spec|plan|deploy'

pattern="^($types)\\(($scopes)\\): [a-z0-9].{1,70}[^.]$"

if ! [[ "$first_line" =~ $pattern ]]; then
  echo
  echo "Commit message does not match the required format."
  echo
  echo "  Required:   type(scope): subject"
  echo "  Types:      $types"
  echo "  Scopes:     $scopes"
  echo "  Subject:    lowercase start, no trailing period, <=72 chars total"
  echo
  echo "  Got:        $first_line"
  echo
  echo "  Examples:"
  echo "    feat(home): migrate calling card to hugo"
  echo "    style(css): tighten portrait spacing"
  echo "    build(deploy): add hugo deploy config writer"
  echo
  exit 1
fi
```

- [ ] **Step 3: Enable hook**

Run:

```bash
chmod +x .githooks/commit-msg
git config core.hooksPath .githooks
```

Expected:

```bash
git config --get core.hooksPath
```

prints `.githooks`.

- [ ] **Step 4: Run checks**

Run:

```bash
make test
make check
```

Expected: both commands exit 0.

- [ ] **Step 5: Commit**

Run:

```bash
git add CLAUDE.md .githooks/commit-msg
git commit -m "docs(config): add homepage agent guidance"
```

Expected: commit succeeds through the new hook.

---

### Task 5: Add Fail-Closed Hugo Deploy Config Writer

**Files:**
- Modify: `.gitignore`
- Modify: `Makefile`
- Create: `scripts/write_deploy_config.py`
- Create: `tests/test_write_deploy_config.py`

- [ ] **Step 1: Create failing tests**

Create `tests/test_write_deploy_config.py`:

```python
import os
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from scripts.write_deploy_config import deploy_config, main


class DeployConfigTests(TestCase):
    def test_deploy_config_contains_target_and_cache_matchers(self) -> None:
        text = deploy_config("s3://jonathandeamer.com?region=eu-west-2", "E123")

        self.assertIn('name = "production"', text)
        self.assertIn('URL = "s3://jonathandeamer.com?region=eu-west-2"', text)
        self.assertIn('cloudFrontDistributionID = "E123"', text)
        self.assertIn("must-revalidate", text)
        self.assertIn("max-age=31536000", text)

    def test_main_fails_when_required_env_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "deploy.toml"
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(main([str(output)]), 2)
            self.assertFalse(output.exists())

    def test_main_writes_config_from_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "deploy.toml"
            env = {
                "HOMEPAGE_S3_URL": "s3://jonathandeamer.com?region=eu-west-2",
                "HOMEPAGE_CLOUDFRONT_DISTRIBUTION_ID": "E123",
            }
            with patch.dict(os.environ, env, clear=True):
                self.assertEqual(main([str(output)]), 0)
            self.assertIn('URL = "s3://jonathandeamer.com?region=eu-west-2"', output.read_text())
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python3 -m unittest tests/test_write_deploy_config.py
```

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.write_deploy_config'`.

- [ ] **Step 3: Add deploy config writer**

Create `scripts/write_deploy_config.py`:

```python
#!/usr/bin/env python3
"""Write Hugo deploy config from explicit local environment variables."""

from __future__ import annotations

import os
import sys
from pathlib import Path


OUTPUT = Path(".hugo-deploy.generated.toml")
S3_ENV = "HOMEPAGE_S3_URL"
CF_ENV = "HOMEPAGE_CLOUDFRONT_DISTRIBUTION_ID"


def deploy_config(s3_url: str, distribution_id: str) -> str:
    return f'''[deployment]
  [[deployment.matchers]]
    pattern = '^sitemap\\.xml$'
    contentType = 'application/xml'
    cacheControl = 'public, max-age=0, must-revalidate'
  [[deployment.matchers]]
    pattern = '^.+\\.html$'
    cacheControl = 'public, max-age=0, must-revalidate'
  [[deployment.matchers]]
    pattern = '^.+\\.(?:jpg|jpeg|png|gif|webp|svg)$'
    cacheControl = 'max-age=31536000, no-transform, public'
  [[deployment.matchers]]
    pattern = '^.+\\.(?:woff2|woff)$'
    cacheControl = 'max-age=31536000, no-transform, public'

  [[deployment.targets]]
    name = "production"
    URL = "{s3_url}"
    cloudFrontDistributionID = "{distribution_id}"
'''


def main(argv: list[str]) -> int:
    output = Path(argv[0]) if argv else OUTPUT
    s3_url = os.environ.get(S3_ENV, "").strip()
    distribution_id = os.environ.get(CF_ENV, "").strip()

    missing = [name for name, value in ((S3_ENV, s3_url), (CF_ENV, distribution_id)) if not value]
    if missing:
        print(f"missing required environment variable(s): {', '.join(missing)}", file=sys.stderr)
        return 2
    if not s3_url.startswith("s3://"):
        print(f"{S3_ENV} must start with s3://", file=sys.stderr)
        return 2

    output.write_text(deploy_config(s3_url, distribution_id))
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 4: Update `Makefile` deploy targets**

Change the `.PHONY` line to:

```make
.PHONY: help dev build test check clean deploy deploy-dry
```

Add these targets after `clean`:

```make
deploy: build  ## deploy production build to S3 and invalidate CloudFront
	python3 scripts/write_deploy_config.py
	@if [ -n "$$HOMEPAGE_AWS_PROFILE" ]; then \
		AWS_PROFILE="$$HOMEPAGE_AWS_PROFILE" hugo --config hugo.toml,.hugo-deploy.generated.toml deploy --target production; \
	else \
		hugo --config hugo.toml,.hugo-deploy.generated.toml deploy --target production; \
	fi

deploy-dry: build  ## show production deploy changes without uploading
	python3 scripts/write_deploy_config.py
	@if [ -n "$$HOMEPAGE_AWS_PROFILE" ]; then \
		AWS_PROFILE="$$HOMEPAGE_AWS_PROFILE" hugo --config hugo.toml,.hugo-deploy.generated.toml deploy --target production --dryRun; \
	else \
		hugo --config hugo.toml,.hugo-deploy.generated.toml deploy --target production --dryRun; \
	fi
```

- [ ] **Step 5: Run tests and fail-closed deploy check**

Run:

```bash
python3 -m unittest tests/test_write_deploy_config.py
env -i PATH="$PATH" make deploy-dry
```

Expected: unit tests pass. `make deploy-dry` exits non-zero after building because `HOMEPAGE_S3_URL` and `HOMEPAGE_CLOUDFRONT_DISTRIBUTION_ID` are missing.

- [ ] **Step 6: Commit**

Run:

```bash
git add Makefile scripts/write_deploy_config.py tests/test_write_deploy_config.py .gitignore
git commit -m "build(deploy): add fail-closed hugo deploy config"
```

Expected: commit succeeds.

---

### Task 6: Final Verification And Handoff

**Files:**
- Modify only if verification exposes a defect in previous tasks.

- [ ] **Step 1: Run full unit tests**

Run:

```bash
make test
```

Expected: all `unittest` tests pass with `OK`.

- [ ] **Step 2: Run full site check**

Run:

```bash
make check
```

Expected: Hugo build exits 0, rendered contract prints `ok`, and installed optional tools report no blocking issues. If `pa11y` cannot launch Chromium locally, capture the exact error and rerun outside the constrained session before claiming accessibility checks pass.

- [ ] **Step 3: Inspect generated public contract**

Run:

```bash
find public -maxdepth 2 -type f | sort
test -f public/index.html
test -f public/404.html
test ! -f public/feed.xml
test ! -f public/index.xml
```

Expected: `index.html` and `404.html` exist, no feed files exist.

- [ ] **Step 4: Optional deploy dry run with verified AWS values**

Only run this step when the user has provided or confirmed exact AWS values and exported them in the shell.

Run:

```bash
: "${HOMEPAGE_S3_URL:?set HOMEPAGE_S3_URL to the verified s3:// bucket URL}"
: "${HOMEPAGE_CLOUDFRONT_DISTRIBUTION_ID:?set HOMEPAGE_CLOUDFRONT_DISTRIBUTION_ID to the verified distribution ID}"
: "${HOMEPAGE_AWS_PROFILE:?set HOMEPAGE_AWS_PROFILE to the verified AWS profile}"
make deploy-dry
```

Expected: Hugo deploy dry run lists planned uploads/deletes and does not upload.

- [ ] **Step 5: Review git status**

Run:

```bash
git status --short --branch
```

Expected: clean worktree, branch ahead by the implementation commits.
