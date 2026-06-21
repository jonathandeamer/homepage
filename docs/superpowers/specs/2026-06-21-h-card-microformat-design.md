# h-card microformat + `rel="me"` identity graph

**Date:** 2026-06-21
**Status:** Approved (design)

## Problem

The homepage already emits rich machine-readable metadata in `<head>`:
OpenGraph, Twitter cards, and a JSON-LD `Person` block. What it lacks is the
complementary **microformats2** layer in the page body. For a site that is
literally a personal *calling card*, an [h-card](https://microformats.org/wiki/h-card)
is the natural representation: it makes the visible card itself parseable by
IndieWeb tools, Mastodon, and other microformats consumers, without any new
markup or JavaScript.

Separately, only the Mastodon link currently carries `rel="me"`. Extending
`rel="me"` to the other identity links builds out the bidirectional identity
graph that underpins IndieAuth and profile verification.

The sibling site `~/small-observations` was reviewed for ideas; it has *no*
microformats and nothing the homepage is missing, so this work is additive and
homegrown rather than ported.

## Goals

- Mark up the existing home card as a **representative h-card**.
- Add `rel="me"` to external profile links so they join the identity graph.
- Keep all changes additive: no structural markup changes, no CSS, no JS, no
  new pages, no third-party requests.
- Lock the new public surface into the executable contract
  (`scripts/check_rendered_site.py` + `tests/`).

## Non-goals (YAGNI)

- No changes to the JSON-LD `Person` block — it already covers structured data
  and stays as-is. h-card is the complementary layer, not a replacement.
- No webmention or micropub endpoints.
- No CSS changes.
- No new pages or feeds.
- No change to link labels, URLs, or copy — so `static/llms.txt` and its
  contract check are untouched.

## Design

### 1. `content/_index.md` — extend `rel="me"`

Add `rel: "me"` to each external profile link item:

- Professional → LinkedIn
- Elsewhere → Wikipedia, Strava, GitHub
- Social → Bluesky, Threads, Twitter (Mastodon already has it)

The Contact → Email item stays a `mailto:` with **no** `rel` (it is not an
identity profile; it is marked `u-email` in the template instead).

`rel="me"` only delivers verification value where the remote profile links back
to the homepage (GitHub website field, Bluesky, Mastodon qualify today). On the
others it is harmless and inert until a return link exists. No labels, URLs, or
copy change, so `llms.txt` and `REQUIRED_LLMS_LINKS` are unaffected.

### 2. `themes/calling-card/layouts/index.html` — h-card classes

Additive `class` attributes only; no element is added, removed, or restructured
except one hidden anchor (below):

| Element                       | Added class |
|-------------------------------|-------------|
| `<article class="card">`      | `h-card`    |
| `<h1 id="site-title">`        | `p-name`    |
| `<p class="intro">`           | `p-note`    |
| portrait `<img>`              | `u-photo`   |
| email `<a>` (the `mailto:`)   | `u-email`   |

The email link needs `u-email` applied specifically to the `mailto:` item. The
template renders all links in one `range`; the class is applied conditionally
when the URL begins `mailto:`.

**Representative h-card self-reference.** A microformats parser treats an
h-card as *representing the page* when the page contains exactly one h-card
whose `u-url` equals the page URL. There is no natural visible self-link on the
card, so add one visually-hidden anchor inside the `h-card` root:

```html
<a class="u-url u-uid" href="{{ site.BaseURL }}" hidden></a>
```

`hidden` keeps it out of the visual layout and the accessibility tree while
remaining in the DOM for parsers. This is preferred over wrapping the `<h1>` in
a self-link, which would change visible/interactive behaviour.

### 3. Contract enforcement

#### `scripts/check_rendered_site.py`

The existing `HeadParser` only inspects `<head>`. Add a body-aware audit that
parses the rendered `index.html` and asserts the h-card is present and
well-formed. New audit (wired into `audit_rendered_site`) checks:

- a `h-card` root element exists,
- within the document, the classes `p-name`, `p-note`, `u-photo`, and
  `u-email` are each present,
- a `u-url` (or `u-uid`) element resolves to `https://jonathandeamer.com/`.

Extend the identity-graph assertion: in addition to the existing single
`rel="me"` head/body check for Mastodon, assert that the **GitHub** and
**Bluesky** profile links also carry `rel="me"` (the links that genuinely
verify). This locks in the identity-graph intent without over-asserting on
platforms that will not back-link.

Implementation note: a dedicated `HTMLParser` subclass (or extension of the
existing one) collects, per element, the `class` token set, `rel` token set,
and `href`, so the body assertions can be expressed against rendered output.

#### `tests/test_check_rendered_site.py`

Add unit tests for the new h-card body audit, following the existing test
style (synthetic rendered HTML fixtures):

- passes on a well-formed h-card,
- reports a missing `h-card` root,
- reports a missing required property class (e.g. `u-photo`),
- reports a `u-url`/`u-uid` that does not resolve to the apex,
- reports missing `rel="me"` on GitHub/Bluesky.

## Affected files

- `content/_index.md`
- `themes/calling-card/layouts/index.html`
- `scripts/check_rendered_site.py`
- `tests/test_check_rendered_site.py`

## Verification

- `make test` — Python unit tests, including the new h-card audit tests.
- `make check` — build + rendered-contract audit (now including the h-card).
- Manual: paste the rendered homepage into an h-card parser
  (e.g. <https://php.microformats.io/>) and confirm a single representative
  h-card with name, note, photo, email, and the rel=me identity URLs.
