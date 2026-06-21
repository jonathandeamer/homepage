# Favicon: "JD" monogram

Date: 2026-06-21

## Goal

Replace the single-letter "J" favicon with a two-letter "JD" monogram so the
icon reads as the owner's initials, while preserving the existing visual
language (dark-green rounded square, cream serif letterforms, a small amount of
the site's orange accent).

## Decision

Side-by-side "JD" in the cream serif, with a thin orange underline rule beneath
the letters as the accent. This replaces the previous floating orange dot, which
became an indistinct speck at favicon sizes. The underline survives down to
16px and reads as a deliberate typographic flourish rather than debris.

Selected variant: **R2-thin-med** (thin rule, proportioned to the letters'
width, centred).

## Specification

Source of truth is a single SVG (`themes/calling-card/static/favicon.svg`),
`viewBox="0 0 64 64"`:

- Background: existing diagonal gradient `#203125 → #273a2d`, `rx="14"`.
- Inner border: existing `#6f8264` stroke at 55% opacity, inset rounded rect.
- Letters: `JD`, cream `#f2eadf`, serif stack
  (`Georgia, 'Times New Roman', serif`), `font-size="37"`, `font-weight="600"`,
  `letter-spacing="0.5"`, centred (`text-anchor="middle"`,
  `dominant-baseline="central"`), baseline anchor `y="31"`.
- Accent: orange `#c2674a` rounded rule, `x="20" y="49" width="24" height="2"
  rx="1"`.

All colours are the site palette tokens (`--panel`, `--panel-soft`, `--rule`,
`--ink`, `--accent`).

## Deliverables

Three static files referenced by `partials/head-meta.html`, all derived from the
one SVG:

1. `favicon.svg` — the vector above.
2. `favicon.png` — 32×32 raster.
3. `apple-touch-icon.png` — 180×180 raster.

## Verification

- `make check` passes (rendered-contract audit unaffected — the icon link tags
  are unchanged).
- Visual review at 16/32/64px and on the running site (`make dev`).

## Out of scope

No changes to `head-meta.html` link tags, `llms.txt`, or any other public
surface. This is an asset swap only.
