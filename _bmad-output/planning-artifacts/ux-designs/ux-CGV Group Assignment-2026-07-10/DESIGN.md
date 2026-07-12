---
title: SAMS — Design
project: CGV Group Assignment (CS402.3)
status: final
created: 2026-07-10
updated: 2026-07-10
sources:
  - ../../prds/prd-CGV Group Assignment-2026-07-10/prd.md
  - ../../../../CS402.3 Coursework.md
  - .memlog.md
  - .working/directions-1.html (Direction 1 — Quiet Clerk; exploration artifact — current visual references are mockups/key-process.html, mockups/key-lookup.html, mockups/key-investigate.html)
name: SAMS
description: 'Quiet Clerk — calm, minimal attendance-marking surface for a non-technical admin. Streamlit-native; light mode only; colour-blind-safe statuses.'
colors:
  surface-base: '#FAFAF8'
  surface-raised: '#FFFFFF'
  primary: '#44526A'
  primary-foreground: '#FFFFFF'
  ink-primary: '#33383F'
  ink-muted: '#7B818A'
  border-hairline: '#E9E8E3'
  row-hover: '#F3F2EE'
  status-present: '#256E4C'
  status-absent: '#A63D2A'
  status-ambiguous: '#7A6212'
  status-ambiguous-tint: '#FDFBF2'
  status-ambiguous-border: '#E3D9B4'
typography:
  page-title:
    note: 'Streamlit default family ("Source Sans"). ~26px, weight 600, letter-spacing -0.02em.'
  section-heading:
    note: 'Streamlit default family. ~17px, weight 600.'
  body:
    note: 'Streamlit default family. ~15px, weight 400, line-height 1.5.'
  label:
    note: 'Streamlit default family. ~13.5px, weight 600.'
  caption:
    note: 'Streamlit default family. ~12.5px, weight 400, coloured {colors.ink-muted}.'
  overline:
    note: 'Streamlit default family. ~13px, weight 700, uppercase, letter-spacing 0.06em, coloured {colors.ink-muted}.'
rounded:
  sm: 10px
  md: 12px
  lg: 14px
  full: 9999px
spacing:
  '1': 4px
  '2': 8px
  '3': 12px
  '4': 16px
  '5': 24px
  '6': 32px
  page-margin: 18px
  card-padding: 16px
  content-max-width: 1100px
  column-gap: 24px
components:
  button-primary:
    background: '{colors.primary}'
    foreground: '{colors.primary-foreground}'
    radius: '{rounded.md}'
    minHeight: 52px
  status-chip-present:
    foreground: '{colors.status-present}'
    icon: '✓'
    label: 'Present'
  status-chip-absent:
    foreground: '{colors.status-absent}'
    icon: '✕'
    label: 'Absent'
  status-chip-ambiguous:
    foreground: '{colors.status-ambiguous}'
    icon: '?'
    label: 'Ambiguous'
  result-row:
    background: '{colors.surface-raised}'
    border: '{colors.border-hairline}'
    radius: '{rounded.lg}'
  result-row-ambiguous:
    background: '{colors.status-ambiguous-tint}'
    border: '{colors.status-ambiguous-border}'
    radius: '{rounded.lg}'
  resolve-button:
    background: '{colors.surface-raised}'
    border: '{colors.border-hairline}'
    radius: '{rounded.sm}'
    minHeight: 46px
  stage-checklist-tick:
    background: '{colors.border-hairline}'
    foreground: '{colors.primary}'
    radius: '{rounded.full}'
---

## Brand & Style

SAMS wears the **Quiet Clerk** direction: calm, minimal, and deliberately unremarkable. Nadeesha, a non-technical admin assistant, is marking attendance from her phone in a corridor or reviewing it at her office desktop — either way the interface should never feel like she is operating "software". One soft neutral surface per task, generous whitespace between them, friendly plain-language microcopy, and a Processing Pipeline presented as a modest checklist — reassurance, not spectacle. The single Ambiguous card is the only thing on any screen allowed to raise its hand.

This is a **Streamlit-native** identity. Tokens map onto Streamlit's `config.toml` `[theme]` keys plus a minimal CSS layer; components are Streamlit's own widgets restyled at the edges, never rebuilt. **Light mode only** — there is no dark variant, and the theme is pinned so browser dark-mode preferences do not invert it.

## Colors

The palette is one calm slate plus three statuses that carry real meaning — nothing decorative.

- **Paper (`{colors.surface-base}`, #FAFAF8)** — the page canvas. Warm off-white, never pure white, so raised cards read as surfaces rather than gaps.
- **Card White (`{colors.surface-raised}`, #FFFFFF)** — every task surface: upload card, pipeline checklist, result rows. Separated from the canvas by tone and a `{colors.border-hairline}` (#E9E8E3) hairline, not by shadow.
- **Slate (`{colors.primary}`, #44526A)** — the single action colour. The Process button, links, active sidebar item, focus accents. Muted on purpose: the sheet photo and the results are the content; the chrome stays quiet.
- **Ink (`{colors.ink-primary}`, #33383F) / Muted Ink (`{colors.ink-muted}`, #7B818A)** — body text and supporting text. Muted ink carries hints, captions, Student Index numerals, and section overlines.
- **Present Green (`{colors.status-present}`, #256E4C)**, **Absent Red (`{colors.status-absent}`, #A63D2A)**, **Ambiguous Ochre (`{colors.status-ambiguous}`, #7A6212)** — the three Attendance Record statuses. Chosen dark enough to pass contrast on white and to remain distinguishable in greyscale. **Rule: a status colour never appears without its icon + text label** (✓ Present, ✕ Absent, ? Ambiguous) — colour is reinforcement, never the sole carrier. These colours are used *only* for status; never for decoration, buttons, or emphasis. Concretely: status colours appear only where they mark an actual Attendance Record status — status chips, the Ambiguous row's accent (tint, border, question line), and the chart's status series. Upload confirmations, checklist ticks, and button outlines stay neutral or slate.
- **Tints (`{colors.status-ambiguous-tint}`, `{colors.status-ambiguous-border}`)** — the quietest possible fill: the pale straw wash that lets an Ambiguous row raise its hand without shouting. Checklist tick circles are neutral (hairline grey with a slate tick), not Present green — "stage done" is not an Attendance Record status.

**Streamlit mapping** (`.streamlit/config.toml`):

```toml
[theme]
primaryColor = "#44526A"            # {colors.primary}
backgroundColor = "#FAFAF8"         # {colors.surface-base}
secondaryBackgroundColor = "#FFFFFF" # {colors.surface-raised}
textColor = "#33383F"               # {colors.ink-primary}
font = "sans serif"                 # Streamlit default "Source Sans"
```

Status colours have no `[theme]` slot; they are applied through the status chip markup and a minimal CSS block (see Components).

Avoid: saturated alert banners, gradients, more than one action colour, and any use of red/green that is not literally an Attendance Record status.

## Typography

Type is inherited, not designed: Streamlit's default family (**"Source Sans"**, falling back to the system sans stack) is the spec — acceptable and deliberate; no custom font is loaded. Roles do the work:

- `{typography.page-title}` — one per page ("Mark today's attendance"). Sentence case, never shouty.
- `{typography.section-heading}` — "Results", "Look up a student". Sparse.
- `{typography.body}` — everything Nadeesha reads. ~15px minimum on phone; never smaller for content she must act on.
- `{typography.label}` / `{typography.caption}` — student names in rows / Student Index numerals, file metadata, hints. Captions use `{colors.ink-muted}`, and Student Index numerals render with tabular figures where available.
- `{typography.overline}` — quiet uppercase section markers ("WHAT WE DID WITH YOUR PHOTO"). The only uppercase in the system.

No display sizes, no italics for emphasis, no monospace (SAMS is a clerk's desk, not a lab instrument).

## Layout & Spacing

Scale: 4 / 8 / 12 / 16 / 24 / 32 px. Named tokens: `{spacing.page-margin}` (18px) for the page gutter on phone; `{spacing.card-padding}` (16px) inside cards; `{spacing.content-max-width}` (~1100px) caps the centered content column on desktop; `{spacing.column-gap}` (24px) separates desktop column pairs.

**Single column on phone; a restrained two-column grid on desktop.** On phone (below ~768px) cards stack vertically in task order (upload → action → pipeline → results), matching Streamlit's natural top-to-bottom flow, with the sidebar collapsed to its hamburger. On desktop (~768px and up) the sidebar stays visible and the content column centers at `{spacing.content-max-width}`; pages use the two-column layouts `EXPERIENCE.md` Responsive & Platform specifies (`st.columns` with a `{spacing.column-gap}` gutter), and every column pair stacks back to the phone order on narrow viewports — still calm surfaces in task order, never a dashboard. Generous vertical rhythm between cards (`{spacing.4}`–`{spacing.5}`); tight rhythm inside them. Navigation lives in Streamlit's native multipage sidebar and is not restyled beyond theme colours.

## Elevation & Depth

None, effectively. Surfaces are distinguished by tone (`{colors.surface-raised}` on `{colors.surface-base}`) and hairline borders — no shadows for hierarchy. Streamlit's own transient chrome (toasts, spinners) keeps its default subtle elevation; SAMS adds nothing.

## Shapes

Soft but not playful: `{rounded.lg}` (14px) for cards and result rows, `{rounded.md}` (12px) for the primary button, `{rounded.sm}` (10px) for small controls like the resolve buttons, `{rounded.full}` for the checklist tick circles only. No pill buttons, no sharp corners. Stage images and signature crops keep square corners inside a `{rounded.sm}` frame — they are evidence, not decoration.

## Components

All components extend Streamlit natives (`st.button`, `st.file_uploader`, `st.image`, `st.expander`, `st.dataframe` or a custom row list built from containers) — restyled via `[theme]` plus a minimal CSS block; never re-implemented.

- **Primary button (Process)** — `st.button` themed by `primaryColor`: `{components.button-primary}`. Full column width, min-height 52px, `{typography.label}` at 16px. One per page, maximum.
- **File slot (uploader)** — `st.file_uploader` for the Signing Sheet photo and Info File, each in its own labelled card row on `{colors.surface-raised}`. When a file is accepted the row shows filename + a quiet "✓ Ready" in `{colors.primary}` — a confirmation, not an Attendance Record status, so it never borrows Present green.
- **Pipeline checklist / stage strip** — a `{colors.surface-raised}` card under the overline "What we did with your photo". Each stage is a row: tick circle (`{components.stage-checklist-tick}`) + stage name in `{typography.body}` + the labelled stage image (`st.image`, full column width, collapsible via `st.expander` after completion). The current stage is named in muted ink while running.
- **Status chip** — icon + text label + colour, always all three: `{components.status-chip-present}`, `{components.status-chip-absent}`, `{components.status-chip-ambiguous}`. Text weight 700 at ~13.5px; no filled backgrounds — coloured text and glyph on the row surface. Must survive greyscale.
- **Result row** — `{components.result-row}`: student name (`{typography.label}`), Student Index (`{typography.caption}`), status chip right-aligned. One row per Student Record. On desktop pointer hover, the row background tints to `{colors.row-hover}` (#F3F2EE) — an enhancement only; hover never reveals or carries information.
- **Ambiguous result row** — `{components.result-row-ambiguous}`: pale straw fill, ochre-tinted border, a one-line plain-language question in `{colors.status-ambiguous}`, and two neutral-outlined resolve buttons (`{components.resolve-button}`, min-height 46px, `{colors.border-hairline}` outline): "✓ Present" and "✕ Absent" — the icon + text label carries the meaning; button label text renders in neutral ink (`{colors.ink-primary}`), and neither the text nor the button chrome takes any status colour.
- **Charts (Lookup)** — the Matplotlib figure the Core Engine emits, rendered as-is; the figure itself uses the three status colours with icon/label-bearing legend entries.
- **Investigate panel** — two `st.image` frames side by side within the content column (stacked on narrow phones, comfortably large on desktop), captioned "Reference Signature" and "Signature from sheet"; below them the similarity scale at full content width and a verdict line in `{typography.section-heading}` weight.

## Do's and Don'ts

| Do | Don't |
|---|---|
| One slate action colour; statuses only for statuses | Use green/red/ochre for anything that isn't an Attendance Record status |
| Neutral chrome for confirmations and controls — "✓ Ready" in slate, resolve buttons and checklist ticks neutral-outlined | Present-green "✓ Ready", status-coloured button outlines, or green tick circles |
| Icon + text label with every status colour (✓ ✕ ?) | Colour-only status dots, cells, or chips |
| Light mode only, pinned via config.toml | Ship a dark variant or let browser dark mode invert the theme |
| Streamlit natives restyled by theme + minimal CSS | Rebuild widgets in raw HTML/JS or heavy CSS overrides |
| Single column on phone; only the calm two-column desktop layouts EXPERIENCE.md specifies; generous whitespace, one task per card | Dense dashboard grids, dense tables, horizontal scrolling |
| Plain-language sentence-case microcopy | Jargon ("binarization threshold exceeded"), all-caps shouting, exclamation marks |
| Hairline borders and tone for hierarchy | Shadows, gradients, decorative illustration |
