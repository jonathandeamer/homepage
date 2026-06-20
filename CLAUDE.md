# CLAUDE.md

This file provides guidance to coding agents working in this repository.

## What this is

This is the Hugo source for `https://jonathandeamer.com/`, a tiny personal calling-card homepage. It is intentionally not a blog, portfolio, feed, or app. Preserve the current public contract: `/`, `/404.html`, `/llms.txt`, no RSS feed, no extra public pages unless the user explicitly asks.

Design rationale lives in `docs/superpowers/specs/`. Implementation plans live in `docs/superpowers/plans/`. Read them before non-trivial changes.

## Architecture

The repo is a Hugo site plus two small Python support tools. The "big picture" worth knowing:

- **One theme, `themes/calling-card`.** `layouts/_default/baseof.html` is the shell; `layouts/index.html` renders the home card; `layouts/404.html` the error page. `partials/head-meta.html` builds every `<meta>`/OpenGraph/Twitter tag, inlines + fingerprints the CSS, and preloads the font — it's where most cross-cutting head logic lives.
- **Content is data-driven from `content/_index.md`.** Front matter defines the `links` (labelled groups of `{name, url, rel?}`), the `portrait`, `intro`, and `license`. The page **body markdown** is rendered via `.Content` as the muted aside near the footer (e.g. the Small Observations note) — so homepage copy is split between front matter *and* body; check both. When changing homepage links, descriptions, related sites, licensing, or portrait attribution, update `static/llms.txt` in the same change so `/llms.txt` stays aligned with the visible page.
- **The public contract is executable, not just prose.** `scripts/check_rendered_site.py` (run by `make check`) asserts the rendered output: non-empty title/description/canonical, `rel=me`, required OG/Twitter meta on `/` and `/404.html`, `/llms.txt` exists with the expected Markdown links, no RSS/feed files, sitemap includes `/` but excludes the 404, robots points at the sitemap. Any change to the public surface must be reflected here and in `tests/`.
- **Images run through Hugo's pipeline at build time.** The portrait lives in `assets/img/` and is `Resize`d in templates to produce the responsive `webp`/`png` in the card and the 1200×1200 OG images. There are no pre-rendered derivatives committed.
- **Deploy config is generated and fail-closed.** `scripts/write_deploy_config.py` writes `.hugo-deploy.generated.toml` from the `HOMEPAGE_*` env vars, validating the `s3://` URL and CloudFront distribution ID before writing; `make deploy` then feeds it to Hugo's deployer.

## Workflow

Committing directly to `main` is fine in this repo — no feature branch or PR is required unless the user asks for one. Run `make check` before committing non-trivial changes.

Commit messages are enforced by the `commit-msg` hook as `type(scope): subject` (lowercase subject, no trailing period, ≤72 chars):

- types: `feat | fix | style | refactor | docs | chore | build`
- scopes: `home | 404 | css | font | asset | config | script | spec | plan | deploy`

## Commands

Use `make`, not plain `hugo`.

```text
make dev          # local Hugo server
make build        # clean production build
make test         # unit tests for the Python scripts (tests/)
make check        # build + rendered-contract / a11y / HTML checks
make screenshots  # capture desktop/mobile/404 PNGs to tmp/screenshots
make clean        # remove generated output
make deploy-dry   # generated deploy config + Hugo deploy dry run
make deploy       # production deploy to S3 + CloudFront
```

- `make test` covers only the Python scripts in `scripts/`; Hugo templates are verified via `make check` and visual inspection. Run a single test with e.g. `python3 -m unittest tests.test_check_rendered_site.RenderedSiteAuditTests.test_reports_canonical_mismatch`.
- `make check`'s link/accessibility/HTML audits (`htmltest`, `pa11y`, `vnu`) are optional — each is skipped with an install hint if not present, so a clean run locally may not exercise all of them.
- `make screenshots` needs a Playwright venv at `~/.venvs/playwright` (override with `make screenshots PLAYWRIGHT_PYTHON=…`); output lands in the gitignored `tmp/`.

## Site constraints

- One local theme: `themes/calling-card`.
- Editable homepage data lives in `content/_index.md`.
- The LLM summary lives in `static/llms.txt` and is copied directly to `/llms.txt`; keep it in sync with current homepage content rather than treating it as generated output.
- No runtime JavaScript.
- No third-party requests.
- One self-hosted expressive serif font.
- The portrait source is `assets/img/jonathan-deamer.png`.
- CSS is hand-written in one file and inlined by Hugo.
- Keep the apex domain `https://jonathandeamer.com/`.
- Keep `rel="me"` for `https://tilde.zone/@JonathanDeamer`.
- Use British English for public-facing copy.

## Deployment

Deployment uses Hugo's deployer with S3 and CloudFront. Unlike the deploy
target, these values live outside the repo (in env vars, not `hugo.toml`), so
`make deploy` and `make deploy-dry` require:

```text
HOMEPAGE_S3_URL                       # s3://jonathandeamer.com?region=eu-west-2
HOMEPAGE_CLOUDFRONT_DISTRIBUTION_ID   # E1C2VU2IB8K3UT
HOMEPAGE_AWS_PROFILE                  # hugo-deploy (optional; falls back to default)
```

The live infrastructure already exists and serves the site: S3 bucket
`jonathandeamer.com` (eu-west-2) behind CloudFront `E1C2VU2IB8K3UT` (aliases
`jonathandeamer.com`, `www.jonathandeamer.com`).

Credentials come from the shared **`hugo-deploy`** IAM user
(`arn:aws:iam::017635961881:user/hugo-deploy`), which also deploys
`smallobservations.net`. Its `HomepageDeployPolicy` grants least-privilege
access: `s3:ListBucket`/`GetBucketLocation` on the bucket,
`GetObject`/`PutObject`/`DeleteObject` on its objects, and
`cloudfront:CreateInvalidation`/`GetInvalidation` on the distribution. The
matching local AWS profile is `hugo-deploy`.

For convenience the three vars live in a gitignored `.deploy.env` at the repo
root — deploy with `source .deploy.env && make deploy` (preview first with
`make deploy-dry`).

Do not guess AWS values. If they are not available, fail clearly and ask the user.
