# Venue profiles — sources and verification notes

The machine-readable profiles live in `assets/style.py` (`PROFILES`). This file
records where each number came from and what to re-verify near submission.
**Journal specs change**: re-check the source and update `checked:` in the paper's
`paper_config.yaml` before final submission. Unknown venue → use `generic` and say so;
never guess a named journal's specs.

| venue    | full width | column | regular text | exceptions | font | dpi | placement | source (checked 2026-10-12) |
|----------|------------|--------|--------------|------------|------|-----|-----------|------------------------------|
| nature   | 183 mm = 7.20 in | 89 mm = 3.50 in | 5–7 pt (**max 7 is binding**) | panel labels 8 pt bold lowercase | sans (Arial/Helvetica) | 600 | tbp | https://www.nature.com/nature/for-authors/formatting-guide |
| acmsmall | 395.8225 pt / 72.27 = 5.477 in | — | ≥ 7.5 pt (math scripts too) | — | document font (Libertine) via pgf for final production | 300 | tbp | https://www.acm.org/publications/proceedings-template |
| elsevier | 190 mm = 7.48 in | 90 mm = 3.54 in | 7–10 pt | tick numerals ≥ 6 pt | serif (Times) or sans | 300 | tbp | https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions |
| trb      | 6.5 in | — | ≥ 8 pt | tick numerals ≥ 7 pt | sans | 300 | H | https://www.trb.org/Publications/PubsTRRJournalAuthors.aspx |
| ieee     | 7.16 in | 3.5 in | 8–10 pt | tick numerals ≥ 7 pt | serif (Times) | 300 | tbp | https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-graphics-for-your-article/ |
| generic  | 6.5 in | 3.25 in | 7–9 pt | tick numerals ≥ 6 pt | sans | 300 | tbp | — |

Per-element rule [R]: readable labels (axis titles, legend, annotations) obey the
regular range; tick numerals and footnote-grade text may go one step lower where
the exceptions column allows; **nothing ever below 5 pt**; a stated max (Nature)
is as binding as a min. Submission-stage specs may differ from final/production —
record any override in `paper_config.yaml` with a cited source.

Notes per venue:

- **nature** — widths are the stated 89/183 mm artwork sizes; 600 dpi for raster
  exports of line-containing art. Panel labels: 8 pt bold **lowercase** letters,
  the one sanctioned exception above the 7 pt ceiling (`S.panel_label`).
- **acmsmall** — the width is `\textwidth` of `acmart` with the `acmsmall` option
  (395.8225 pt at 72.27 pt/in). For camera-ready font matching (Linux Libertine),
  switch matplotlib to the `pgf` backend compiled with the document preamble; the
  default profile keeps a portable serif and embeds it, which is acceptable at
  submission stage.
- **elsevier** — 190/90 mm are the standard single/double-column artwork widths;
  some Elsevier titles differ — check the specific journal's Guide for Authors.
- **trb** — TRR/TRB manuscripts are single-column on US letter with 1 in margins
  → 6.5 in text width; figures and tables placed in-text near first mention
  (hence `[H]` placement, `float` package).
- **ieee** — 7.16 in two-column span / 3.5 in single column.
