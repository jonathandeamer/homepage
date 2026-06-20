# Homepage Hugo Calling Card Migration — Design Spec

**Date:** 2026-06-20
**Status:** Design approved, ready for implementation planning

## Purpose

Migrate `jonathandeamer.com` from two hand-written static HTML files into a tiny Hugo site while preserving the current public purpose: a compact personal page listing places to find Jonathan online and ways to get in touch.

The aim is not to turn the homepage into a blog, portfolio, or content site. Hugo is being introduced for the workflow benefits learned from `small-observations`: a clean build/deploy loop, reusable templates, local checks, stricter repository practice, and a structure that is more fun and safer to tweak later.

## Current State

The current `homepage` repo has four tracked files:

- `index.html`
- `404.html`
- `style.css`
- `.gitignore`

The current `.gitignore` is an allowlist that ignores everything except the old static files. That was useful for the previous manually uploaded site, but it is wrong for the Hugo migration because docs, config, theme files, content, scripts, and assets should be tracked normally.

The live/bucket download in `~/Downloads` also contains the missing assets:

- `jonathan-deamer.png` — 600x600 portrait source
- `jonathan-deamer.webp` — 272x272 derived portrait
- `favicon.png` — 32x32 favicon

The downloaded `index.html` and `style.css` match the repo. The Hugo migration should copy only the useful assets, not the duplicate HTML/CSS.

## Goals

- Preserve the public URL contract:
  - homepage at `https://jonathandeamer.com/`
  - friendly custom `404.html`
  - no RSS feed
  - no extra public pages in the first migration
- Keep the site as a personal calling card with a visible portrait.
- Make the visual design a bit prettier and more distinctive while staying compact.
- Use a self-hosted expressive serif font.
- Avoid runtime JavaScript and third-party requests.
- Add the stricter local workflow from `small-observations` in a size-appropriate way:
  - `Makefile`
  - clean Hugo builds
  - local validation/audit checks
  - S3 + CloudFront deploy via Hugo
  - checked-in specs/plans
  - repo guidance for future agents
  - conventional commit hook

## Non-Goals

- No blog, notes section, feed, CMS, analytics, or client-side app.
- No redesign that obscures the page's practical purpose.
- No imported third-party Hugo theme.
- No new npm build pipeline for the site itself.
- No fabricated replacement image; the existing portrait asset is the source of truth.

## Architecture

Use Hugo with one local theme, `themes/calling-card`.

Content and design should be split the same way as `small-observations`, but with much less machinery:

```text
hugo.toml
Makefile
CLAUDE.md
content/_index.md
themes/calling-card/
  layouts/_default/baseof.html
  layouts/index.html
  layouts/404.html
  layouts/partials/head-meta.html
  layouts/partials/footer.html
  assets/css/site.css
  static/fonts/fraunces-latin.woff2
  static/favicon.png
assets/img/jonathan-deamer.png
scripts/
docs/superpowers/specs/
docs/superpowers/plans/
.githooks/commit-msg
```

`content/_index.md` should hold the editable homepage facts: title, description, intro copy, link groups, portrait metadata, portrait credit URL, and licence text. The theme renders those facts into the calling-card layout.

The portrait should live in Hugo `assets/` so templates can use Hugo's image pipeline to emit appropriately sized images. The favicon can live in theme `static/` because it is already tiny and stable.

## Content Model

Homepage front matter should be structured, not embedded as raw HTML. A representative shape:

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

Templates should preserve current link destinations unless implementation finds a broken or obsolete URL and the user approves changing it.

## Visual Direction

Use the approved "personal calling card" direction, with correct normal capitalisation: `Jonathan Deamer`, not all caps.

The design should feel like a small made object rather than a generic link list:

- dark, restrained background that nods to the existing green site
- expressive self-hosted serif typography
- visible portrait in the first viewport
- grouped links with clear labels
- compact footer/licence line
- strong focus states and hover states
- responsive layout that works as a single card on narrow screens

The site can borrow lessons from `small-observations` without becoming visually identical to it. Reusing Fraunces is acceptable and likely the lowest-risk first implementation because the font file already exists locally and its behaviour is known. If a different expressive serif is chosen later, it must be self-hosted, licensed for web use, and documented in the repo.

## HTML And Accessibility

The generated HTML should be semantic and small:

- one meaningful `<h1>` on the homepage
- one meaningful `<h1>` on the 404 page
- skip-navigation link at the start of `<body>`
- visible `:focus-visible` outline
- portrait has non-empty alt text
- decorative flourishes use `aria-hidden="true"`
- grouped links are represented as lists or labelled sections, not loose visual-only text
- page works without CSS
- colour contrast must meet WCAG AA for body text and functional links

The 404 should preserve the current message and contact path in spirit:

- title: `404 — Jonathan Deamer`
- robots `noindex, nofollow`
- short apology/copy
- link home or email

## Head Metadata

Every rendered page should include:

- UTF-8 charset and responsive viewport
- page-specific `<title>`
- description meta
- canonical URL
- favicon
- `theme-color`
- `rel="me"` for Mastodon
- Open Graph and Twitter card metadata

The homepage should use the portrait as its social preview image if Hugo can generate a suitable derived asset. The 404 can use summary metadata without an image.

## Build Workflow

Everything should go through `make`, following the `small-observations` lesson that direct `hugo` commands can leave stale output.

Targets:

```text
make help        # list targets
make dev         # Hugo dev server
make build       # clean production build
make check       # build + audits
make clean       # remove generated output
make deploy      # production build and deploy
make deploy-dry  # show deploy changes without uploading
```

`make build` should use `hugo --cleanDestinationDir --minify --gc --printPathWarnings`.

Generated output should remain untracked:

- `public/`
- `resources/_gen/`
- `.hugo_build.lock`

Replace the current `.gitignore` from scratch during implementation. The new file should track repository source by default, including `docs/superpowers/specs/` and `docs/superpowers/plans/`, and ignore only generated/local files:

- `public/`
- `resources/_gen/`
- `.hugo_build.lock`
- `.DS_Store`
- `.superpowers/`
- editor/OS noise if it appears

There should be no broad `*` ignore rule and no need to force-add docs.

## Checks

`make check` should be small but meaningful:

- build the site
- verify rendered metadata for homepage and 404
- verify canonical URLs use the apex domain
- verify there is no RSS output
- verify `404.html` exists at the site root
- verify `sitemap.xml` and `robots.txt` if enabled
- run `htmltest` when installed
- run `pa11y` when installed
- run `vnu` when installed
- run `xmllint` on XML outputs when present

Because this site has no Python package or ingest pipeline, it does not need the photo/front-matter scripts from `small-observations`. Any scripts copied or written for this repo should be specific to this site's small rendered-output contract.

## Deployment

Use Hugo's deployer with the same S3 + CloudFront pattern as `small-observations`.

The deploy target should use the existing AWS infrastructure for `jonathandeamer.com`, replacing the current manual bucket upload. Implementation must verify the exact bucket name, region, AWS profile, and CloudFront distribution ID from local/AWS context or user-provided values before the first real deploy. If those values cannot be verified, `make deploy` should fail clearly rather than uploading to a guessed destination.

Cache policy:

- HTML and `sitemap.xml`: `public, max-age=0, must-revalidate`
- fingerprinted processed images and fonts: long-cache, `max-age=31536000, no-transform, public`
- stable static assets such as `favicon.png`: long-cache is acceptable if CloudFront invalidation covers deploys that change them
- no steady-state `force = true` deploy matchers

The implementation should include `make deploy-dry` so the upload set can be reviewed before touching production.

## Repository Practice

Add a `CLAUDE.md` equivalent for this repo documenting:

- the site is a tiny Hugo personal calling card
- keep public scope small
- use `make`, not plain `hugo`
- no runtime JavaScript
- no third-party requests
- self-hosted font only
- preserve the apex domain and current URL contract
- deployment depends on S3 + CloudFront
- where design specs and implementation plans live

Add `.githooks/commit-msg` with a smaller conventional-commit rule. Suggested allowed types:

- `feat`
- `fix`
- `style`
- `refactor`
- `docs`
- `chore`
- `build`

Suggested allowed scopes:

- `home`
- `404`
- `css`
- `font`
- `asset`
- `config`
- `script`
- `spec`
- `plan`
- `deploy`

Set `core.hooksPath` to `.githooks` during implementation, as in `small-observations`.

## Migration Notes

Implementation should proceed incrementally:

1. Add Hugo config, theme skeleton, content model, and Makefile.
2. Replace `.gitignore` with a normal Hugo/project ignore file that tracks docs and source by default.
3. Move the portrait source and favicon from `~/Downloads`.
4. Port current homepage and 404 content into Hugo templates/content.
5. Apply the calling-card visual design.
6. Add checks and repo guidance.
7. Configure deploy with verified AWS values.
8. Run local verification.
9. Use `make deploy-dry` before any real deploy.

The first implementation should prioritise preserving the current site contract and making the workflow solid. More playful visual refinements can come after the Hugo migration is safely in place.
