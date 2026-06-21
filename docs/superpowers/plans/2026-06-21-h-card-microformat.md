# h-card Microformat + rel=me Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mark the homepage card up as a representative h-card and extend `rel="me"` to all identity links, with the new surface locked into the executable contract.

**Architecture:** Two changes to the rendered site (additive `class`/`rel` attributes on the existing `<article class="card">` plus one hidden self-referencing anchor) and one change to the verifier (a new body-level audit in `scripts/check_rendered_site.py` with unit tests). The audit is written and tested first against synthetic HTML, then the templates are changed so the real `make check` build satisfies it.

**Tech Stack:** Hugo templates (Go templating), Python 3 `html.parser` (stdlib), `unittest`.

## Global Constraints

- Public contract is executable: any change to the public surface must be reflected in `scripts/check_rendered_site.py` and `tests/`.
- No runtime JavaScript, no third-party requests, no new pages or feeds.
- British English for public-facing copy.
- Apex domain is `https://jonathandeamer.com/`; keep `rel="me"` for `https://tilde.zone/@JonathanDeamer`.
- Link labels, URLs, and copy are unchanged — `static/llms.txt` and `REQUIRED_LLMS_LINKS` must stay untouched.
- Commit messages: `type(scope): subject` (lowercase, no trailing period, ≤72 chars). Types: `feat|fix|style|refactor|docs|chore|build`. Scopes include `home`, `script`, `config`.
- Run `make check` before considering the feature complete.

---

### Task 1: h-card body audit in the verifier

**Files:**
- Modify: `scripts/check_rendered_site.py`
- Modify: `tests/test_check_rendered_site.py`

**Interfaces:**
- Consumes: existing `audit_rendered_site(public_dir: Path) -> list[str]`, module constant `SITE = "https://jonathandeamer.com"`.
- Produces: `audit_home_card(path: Path) -> list[str]` and a `CardParser(HTMLParser)` whose `.elements` is a `list[dict]` with keys `classes: set[str]`, `rel: set[str]`, `href: str`. `audit_home_card` is wired into `audit_rendered_site` for `index.html` only.

- [ ] **Step 1: Write the failing tests**

In `tests/test_check_rendered_site.py`, add a `HOME_BODY` fixture and tests. Place `HOME_BODY` after the `LLMS_TXT` constant:

```python
GITHUB_URL = "https://github.com/jonathandeamer"
BLUESKY_URL = "https://bsky.app/profile/jonathandeamer.bsky.social"

HOME_BODY = f"""
<article class="card h-card">
  <h1 class="p-name">Jonathan Deamer</h1>
  <p class="intro p-note">Places you can find me online.</p>
  <a class="u-email" href="mailto:jonathandeamer@gmail.com">Email</a>
  <a href="{GITHUB_URL}" rel="me">GitHub</a>
  <a href="{BLUESKY_URL}" rel="me">Bluesky</a>
  <a href="https://tilde.zone/@JonathanDeamer" rel="me">Mastodon</a>
  <img class="u-photo" src="/img/portrait.png" alt="Photo of Jonathan Deamer">
  <a class="u-url u-uid" href="{SITE}/" hidden></a>
</article>
"""
```

Add these test methods to `RenderedSiteAuditTests`:

```python
    def test_accepts_valid_h_card(self) -> None:
        from scripts.check_rendered_site import audit_home_card
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "index.html", page(HOME_HEAD, HOME_BODY))
            self.assertEqual(audit_home_card(root / "index.html"), [])

    def test_reports_missing_h_card_root(self) -> None:
        from scripts.check_rendered_site import audit_home_card
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "index.html", page(HOME_HEAD, HOME_BODY.replace("card h-card", "card")))
            self.assertIn("index.html: missing h-card root", audit_home_card(root / "index.html"))

    def test_reports_missing_h_card_property(self) -> None:
        from scripts.check_rendered_site import audit_home_card
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "index.html", page(HOME_HEAD, HOME_BODY.replace('class="u-photo"', 'class="portrait"')))
            self.assertIn("index.html: missing u-photo in h-card", audit_home_card(root / "index.html"))

    def test_reports_self_url_not_apex(self) -> None:
        from scripts.check_rendered_site import audit_home_card
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "index.html", page(HOME_HEAD, HOME_BODY.replace(f'href="{SITE}/" hidden', 'href="https://example.com/" hidden')))
            self.assertIn(f"index.html: missing u-url/u-uid resolving to {SITE}/", audit_home_card(root / "index.html"))

    def test_reports_missing_rel_me_profile(self) -> None:
        from scripts.check_rendered_site import audit_home_card
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "index.html", page(HOME_HEAD, HOME_BODY.replace(f'href="{GITHUB_URL}" rel="me"', f'href="{GITHUB_URL}"')))
            self.assertIn("index.html: missing rel=me for GitHub", audit_home_card(root / "index.html"))
```

Update the existing `test_accepts_valid_rendered_site` so its home page carries the h-card body (otherwise the wired-in audit will fail it). Change its `index.html` write line to:

```python
            write(root / "index.html", page(HOME_HEAD, HOME_BODY))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd ~/homepage && python3 -m unittest tests.test_check_rendered_site -v`
Expected: FAIL — `ImportError: cannot import name 'audit_home_card'`.

- [ ] **Step 3: Implement the parser and audit**

In `scripts/check_rendered_site.py`, add the profile URL constants next to `SITE`:

```python
GITHUB_URL = "https://github.com/jonathandeamer"
BLUESKY_URL = "https://bsky.app/profile/jonathandeamer.bsky.social"
```

Add the parser class after `HeadParser`:

```python
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
```

Add the audit function after `audit_page`:

```python
def audit_home_card(path: Path) -> list[str]:
    label = path.name
    if not path.exists():
        return [f"{label}: missing file"]

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
```

Wire it into `audit_rendered_site`, immediately after the `index.html` `audit_page` call:

```python
    errors.extend(audit_page(public_dir / "index.html", f"{SITE}/", REQUIRED_HOME_META))
    errors.extend(audit_home_card(public_dir / "index.html"))
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd ~/homepage && python3 -m unittest tests.test_check_rendered_site -v`
Expected: PASS (all tests, including the updated `test_accepts_valid_rendered_site`).

- [ ] **Step 5: Commit**

```bash
cd ~/homepage && git add scripts/check_rendered_site.py tests/test_check_rendered_site.py
git commit -m "feat(script): audit homepage h-card and rel=me identity links"
```

---

### Task 2: h-card markup + rel=me in the rendered site

**Files:**
- Modify: `content/_index.md`
- Modify: `themes/calling-card/layouts/index.html`

**Interfaces:**
- Consumes: `audit_home_card` from Task 1 (runs inside `make check`).
- Produces: rendered `public/index.html` that satisfies the Task 1 audit.

- [ ] **Step 1: Add rel=me to profile links in content**

In `content/_index.md`, add `rel: "me"` to each external profile link item. The Email item is unchanged (no `rel`). Mastodon already has it. The `links:` block becomes:

```yaml
links:
  - label: "Contact"
    items:
      - name: "Email"
        url: "mailto:jonathandeamer@gmail.com"
  - label: "Professional"
    items:
      - name: "LinkedIn"
        url: "https://www.linkedin.com/in/jonathandeamer/"
        rel: "me"
  - label: "Elsewhere"
    items:
      - name: "Wikipedia"
        url: "https://en.wikipedia.org/wiki/User:Jonathan_Deamer"
        rel: "me"
      - name: "Strava"
        url: "https://www.strava.com/athletes/18361576"
        rel: "me"
      - name: "GitHub"
        url: "https://github.com/jonathandeamer"
        rel: "me"
  - label: "Social"
    items:
      - name: "Bluesky"
        url: "https://bsky.app/profile/jonathandeamer.bsky.social"
        rel: "me"
      - name: "Mastodon"
        url: "https://tilde.zone/@JonathanDeamer"
        rel: "me"
      - name: "Threads"
        url: "https://www.threads.net/@jonathandeamer"
        rel: "me"
      - name: "Twitter"
        url: "https://twitter.com/JonathanDeamer"
        rel: "me"
```

- [ ] **Step 2: Add h-card classes to the home template**

In `themes/calling-card/layouts/index.html`, apply the changes below.

`<article>` open tag (line 7):

```html
<article class="card h-card" aria-labelledby="site-title">
```

`<h1>` (line 9):

```html
    <h1 class="p-name" id="site-title">{{ .Title }}</h1>
```

intro paragraph (line 10):

```html
    <p class="intro p-note">{{ .Params.intro }}</p>
```

link `<li>` (line 18) — add `u-email` only to the `mailto:` item:

```html
              <li><a href="{{ .url }}"{{ with .rel }} rel="{{ . }}"{{ end }}{{ if strings.HasPrefix .url "mailto:" }} class="u-email"{{ end }}>{{ .name }}</a></li>
```

portrait `<img>` (line 32) — add `u-photo` to the class:

```html
        <img class="u-photo" src="{{ $portraitPng.RelPermalink }}" alt="{{ .Params.portrait.alt }}" width="{{ $portraitPng.Width }}" height="{{ $portraitPng.Height }}">
```

Add the hidden self-referencing anchor inside the `h-card` root, immediately before the closing `</article>` (after line 35's `</aside>`):

```html
  <a class="u-url u-uid" href="{{ site.BaseURL }}" hidden></a>
</article>
```

- [ ] **Step 3: Build and run the full contract check**

Run: `cd ~/homepage && make check`
Expected: build succeeds and the rendered-contract audit prints `ok` (the homepage now passes `audit_home_card`; htmltest/pa11y/vnu may be skipped if not installed).

- [ ] **Step 4: Verify the rendered h-card manually**

Run: `cd ~/homepage && grep -o 'class="[^"]*card[^"]*"\|class="u-[^"]*"\|class="p-[^"]*"\|rel="me"' public/index.html | sort | uniq -c`
Expected: shows `h-card`, `p-name`, `p-note`, `u-photo`, `u-email`, `u-url u-uid`, and multiple `rel="me"` occurrences. Optionally paste `public/index.html` into <https://php.microformats.io/> and confirm a single representative h-card with name, note, photo, email, and rel=me URLs.

- [ ] **Step 5: Commit**

```bash
cd ~/homepage && git add content/_index.md themes/calling-card/layouts/index.html
git commit -m "feat(home): mark up card as representative h-card with rel=me"
```

---

## Self-Review

**Spec coverage:**
- `content/_index.md` rel=me extension → Task 2 Step 1. ✓
- index.html h-card classes (h-card/p-name/p-note/u-photo/u-email) → Task 2 Step 2. ✓
- Self-referencing hidden `u-url u-uid` → Task 2 Step 2. ✓
- `check_rendered_site.py` body audit (root, properties, self-url, GitHub/Bluesky rel=me) → Task 1 Step 3, wired in. ✓
- Unit tests for present/missing/malformed/self-url/rel=me → Task 1 Step 1. ✓
- JSON-LD untouched, no CSS/JS/pages, llms.txt untouched → no task touches them (confirmed: only the four spec files are modified). ✓
- Verification via `make test` / `make check` → Task 1 Step 4, Task 2 Step 3. ✓

**Placeholder scan:** No TBD/TODO; every code step shows full content. ✓

**Type consistency:** `audit_home_card(path)` and `CardParser.elements` dict keys (`classes`/`rel`/`href`) are used identically across the parser, audit, and tests. Constants `GITHUB_URL`/`BLUESKY_URL` defined in both module and test with matching values. The hidden anchor `href="{{ site.BaseURL }}"` renders `https://jonathandeamer.com/`, matching the audit's `f"{SITE}/"`. ✓
