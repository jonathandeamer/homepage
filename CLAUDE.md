# CLAUDE.md

This file provides guidance to coding agents working in this repository.

## What this is

This is the Hugo source for `https://jonathandeamer.com/`, a tiny personal calling-card homepage. It is intentionally not a blog, portfolio, feed, or app. Preserve the current public contract: `/`, `/404.html`, no RSS feed, no extra public pages unless the user explicitly asks.

Design rationale lives in `docs/superpowers/specs/`. Implementation plans live in `docs/superpowers/plans/`. Read them before non-trivial changes.

## Workflow

Committing directly to `main` is fine in this repo — no feature branch or PR is required unless the user asks for one. Commit messages must follow the `commit-msg` hook format (`type(scope): subject`); run `make check` before committing non-trivial changes.

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
