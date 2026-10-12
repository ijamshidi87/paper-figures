---
name: paper-figures
description: Build publication-ready data figures (matplotlib) and LaTeX tables for research manuscripts in a fixed design system — Okabe-Ito role palette, venue-exact widths with per-element font floors, vector PDF + PNG + grayscale proof, booktabs/threeparttable tables generated from results files, with numeric audits and quality gates. Use whenever the user asks for a figure, plot, chart, heatmap, forest plot, calibration plot, panel figure or table for a paper, or to restyle matplotlib code for a journal (TRR/TRB, Nature, Elsevier, ACM, IEEE). Not for pipeline/framework/schematic diagrams — those belong to the paper-pipelines skill.
---

# Paper figures and tables

Data figures and LaTeX tables only. Pipeline, framework and schematic diagrams are a
separate skill (paper-pipelines) that reuses this skill's `style.py`.

## 0. Rule classes and provenance

Two kinds of rules appear below:
- **[E] Extracted practice** — observed in Amir Rafe's public repos (MIT-licensed;
  when copying code verbatim, keep a one-line attribution comment with the repo URL).
  His own repos sometimes violate these (e.g. 4.8 pt text in f04_calibration.py),
  so [E] is evidence, not law.
- **[R] Recommended standard** — this skill's own requirement. Where [E] and [R]
  conflict, [R] wins. Everything in "Hard rules" (§10) is [R].

## 1. First use in a paper (bootstrap)

When `figures/style.py` does not exist in the paper's repo:

1. Ask (or infer from context): venue and stage (`submission` | `final`), where the
   results live (`results/*.json|csv|parquet`), and the role→meaning mapping for this
   paper's palette (e.g. blue = observed, amber = adjusted). Unknown venue → use the
   `generic` profile and say so; never guess a named journal's specs.
2. Write `paper_config.yaml` (template in §2) at the repo root.
3. Generate `figures/style.py` implementing §3 for that config.
4. Generate `scripts/check_figures.py` (§8) and `scripts/numbers_audit.py` (§8).
   Both MUST end with a real failure propagation — `sys.exit(1)` on any failed check.
   Never `sys.exit(0 if ... else 0)` (a real bug found in r7_style_audit.py).
5. Run the three smoke tests (§9) before producing any real figure. If one fails,
   fix the generated files first.

## 2. Venue profiles

Record in `paper_config.yaml`; every profile carries its source and check date, and
submission-stage specs may differ from final/production specs.

```yaml
venue: trb            # trb | nature | elsevier | acmsmall | ieee | generic
stage: final          # submission | final  (widths/formats may differ by stage)
results_dir: results/
palette_roles:        # one role per colour, fixed for the whole paper
  obs: blue — observed / primary series
  adj: amber — adjusted / secondary
profile:              # filled from the table below; override only with a cited source
  source: <official URL>
  checked: 2026-10-12
```

Built-in profiles ([R]; verify against the source when the paper is close to
submission — journal specs change):

| venue    | full width        | column          | regular text      | exceptions                        | font            | dpi (raster) |
|----------|-------------------|-----------------|-------------------|-----------------------------------|-----------------|--------------|
| nature   | 183 mm (7.20 in)  | 89 mm (3.50 in) | 5–7 pt (max 7!)   | panel labels 8 pt bold lowercase  | sans (Arial/Helv)| 600         |
| acmsmall | 395.8225 pt / 72.27 = 5.477 in | —  | ≥ 7.5 pt          | math scripts pinned ≥ 7.5         | document font via pgf (Libertine) | 300 |
| elsevier | 190 mm (7.48 in)  | 90 mm (3.54 in) | 7–10 pt           | tick numerals ≥ 6 pt              | serif (Times) or sans | 300    |
| trb      | 6.5 in            | —               | ≥ 8 pt            | tick numerals ≥ 7 pt              | sans            | 300          |
| ieee     | 7.16 in           | 3.5 in          | 8–10 pt           | tick numerals ≥ 7 pt              | serif (Times)   | 300          |
| generic  | 6.5 in            | 3.25 in         | 7–9 pt            | tick numerals ≥ 6 pt              | sans            | 300          |

Per-element floors [R]: readable labels (axis titles, legend, annotations) obey the
regular range; tick numerals and footnote-grade text may go one step lower where the
exceptions column allows; nothing ever below 5 pt. A max is as binding as a min where
the profile states one (Nature).

## 3. The design system (`figures/style.py`)

Palette [E→R] — Okabe-Ito with fixed roles, plus structure colours:

```python
C = {"obs": "#0072B2", "adj": "#E69F00", "exp": "#009E73", "alert": "#D55E00",
     "aux": "#CC79A7", "light": "#56B4E9", "neutral": "#7F7F7F",
     "ink": "#222222", "muted": "#5A6066", "rule": "#D9E1E5", "band": "#EEF1F2"}
AMBER_INK = "#B07D14"   # amber is unreadable as type; use this for amber text
```

Rules: `tint(hex, frac)` for lighter fills (never new hues); `seq_cmap()` white→role
colour, `div_cmap()` grey→white→amber; parallel `MARKERS/LINESTYLES/HATCHES` dicts so
series stay distinct in grayscale [E]; one role per meaning for the whole paper [R].

rcParams via `apply(venue, stage)` [E]: white background, top/right spines off,
frameless legend, faint grid at most, 0.5 pt axes, `pdf.fonttype 42`,
`axes.axisbelow True`, fonts per profile.

`save(fig, name, mode="exact")` [R] — the two export modes are never mixed:
- `exact` (default, for LaTeX inclusion at scale 1): the PDF page is exactly the
  declared figsize — explicit `Bbox.from_bounds(0,0,W,H)`, `pad_inches=0`,
  **never** `bbox_inches="tight"`.
- `tight` (previews, slides only): `bbox_inches="tight"`; such a PDF is exempt from
  the width gate and is never the file the manuscript includes.
Every save writes: `name.pdf`, `name.png`, `gray/name.png`, and a sidecar
`name.meta.json` captured at save time (the only moment the Text objects exist):

```json
{"target_w_in": 6.5, "mode": "exact", "venue": "trb", "stage": "final",
 "config_sha256": "<hash of paper_config.yaml>", "pdf_sha256": "<hash of the PDF>",
 "texts": [{"pt": 8.0, "kind": "label", "s": "Crashes (thousands)"}, ...]}
```

`check_figures.py` validates the sidecar against the PDF hash first; a stale or
missing sidecar is itself a failure (metadata must belong to this exact PDF).

Helper API [E]: `panel_title(ax, "a", "Title")` → "(a) Title" left-aligned;
`panel_label(ax, "a")` Nature-style; `light_grid`, `despine`, `finish(fig)`
(sentence-case labels, `fig.align_labels()`), `tex_color_defs()` for LaTeX swatches.

## 4. Figure script contract

One file = one figure, `fNN_slug.py`, in `figures/`. Template:

```python
"""Figure 3. One-line statement of what the figure shows.

(a) What panel (a) shows, how it is computed, what each colour means.
Values come from results/estimates.json; nothing is typed by hand.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import style as S

def load():
    ...   # read from results_dir only — never hardcode a number

def main():
    d = load()
    S.apply("trb", "final")
    fig, axes = plt.subplots(1, 2, figsize=(S.FULL, 2.6))  # width fixed, height chosen
    ...
    S.panel_title(axes[0], "a", "Narrative over coded count")
    S.save(fig, "f03_plane")           # mode="exact"

if __name__ == "__main__":
    main()
```

Enforced rules [R]: docstring = caption draft (one line per panel); no number typed
by hand; no `plt.rcParams`, no hex, no `bbox_inches` inside a figure script — only
`S.*`; width is always `S.FULL` or `S.COL`; sentence case, units in axis labels
("Crashes (thousands)"); legend only when direct labeling is impossible; every text
obeys the per-element floors of §2.

## 5. Choosing the chart form — from the scientific question, not the look [R]

Before drawing, name the question the figure answers, then pick the form:

| the question is about…                              | draw                                   | not                        |
|-----------------------------------------------------|----------------------------------------|----------------------------|
| effect sizes with uncertainty (OR/RR/HR + CI)       | forest / dot plot with CI whiskers     | bar chart                  |
| comparing rates or model metrics across groups      | dot plot with CI, sorted               | grouped bars without CI    |
| predicted vs observed probability                   | calibration plot + histogram of p      | a table of Brier scores    |
| a matrix (space×time, group×outcome, agreement)     | heatmap (sequential ramp from §3)      | many small bars            |
| a yearly/temporal panel per unit                    | heatmap + sparkline column             | spaghetti lines            |
| distribution shape                                  | density/ECDF/raincloud                 | mean±SD bars ("dynamite")  |
| few exact values the reader must read               | a table, not a figure                  |                            |

If none fits, say which question the figure answers and justify the form in one line
in the docstring.

## 6. Statistical integrity rules — checked by the model, before drawing [R]

These are reviewer-grade checks that no script can make; run through them explicitly:
- Denominators: every percentage/rate names its denominator, and compared series share
  one (or the difference is stated in the caption draft).
- Units and scales: axis units stated; log axes flagged in the label; no truncated
  bar-chart axis; dual y-axes avoided (justify if unavoidable).
- Uncertainty: estimates carry CI/SE wherever the results file provides them; omitting
  uncertainty is a decision to state, not a default.
- Missingness: dropped or missing categories are named in the caption draft, never
  silently absent.
- Comparability: same y-limits across panels that invite comparison; sorting is by a
  stated criterion.
If any check cannot be satisfied from the results file, say so instead of drawing
around it.

## 7. Tables

Generated by `tables/make_tables.py` from results files — never hand-typed .tex [E].
Pick the environment by the table's shape [R]:

| shape                                   | environment                                   |
|-----------------------------------------|-----------------------------------------------|
| compact numeric table                   | `tabular` + booktabs                          |
| needs structured notes / star defs      | `threeparttable` + booktabs                   |
| long text cells that must wrap          | `tabularx` (X columns) + booktabs             |
| more rows than one page                 | `xltabular`                                   |

Rules [R]: booktabs only (`\toprule/\midrule/\bottomrule`), no vertical rules; `@{}`
at both edges; numbers right-aligned or decimal-aligned via `siunitx`; SE/CI beside
the estimate: `0.42 (0.03)` or `1.21 [1.05, 1.40]`; CI + exact p preferred, significance
stars optional — only if the venue convention expects them, defined in the note;
`\scriptsize\textit{Note.}` under the table; cell colour only from the palette ramp
(`\cellcolor[HTML]{...}`); placement (`[H]`, `[tbp]`, …) comes from the venue profile,
not hardcoded; one table per `tables/out/table_slug.tex`, `\input` in the manuscript.

## 8. Quality gates

`scripts/check_figures.py <pdf> --venue <venue> --stage <stage>` — all must pass:
1. sidecar exists and its `pdf_sha256` matches the PDF (stale metadata fails);
2. `mode == "exact"` for any figure the manuscript includes;
3. PDF MediaBox width == profile width (±0.01 in);
4. every sidecar text within its per-element floor **and ceiling**;
5. fonts embedded (`pdffonts`: all `emb=yes`);
6. no hex literal in `figures/*.py` except `style.py` (grep `#[0-9A-Fa-f]{6}`);
7. every figure script has a panel-describing docstring (AST parse);
8. grayscale proof exists.

`scripts/numbers_audit.py` — numeric audit, with the circularity rule [R]:
every printed claim is **recomputed from an upstream artefact** (the raw/intermediate
data the results were derived from), never merely re-read from the same JSON the
figure read. `check(claim_id, got, want, tol)` collects failures; exit 1 if any.
Numeric agreement is still not scientific correctness — §6 covers what the audit
cannot (a wrong denominator used consistently passes the audit).

Both scripts: failure ⇒ `sys.exit(1)`. This is gate zero.

## 9. Minimal executable tests (from day one)

Three smoke tests, run at bootstrap and on demand (`scripts/smoke_test.py`):
1. **A figure builds**: a 10-row synthetic results file → template figure → exact-mode
   PDF+PNG+sidecar produced, `check_figures.py` passes.
2. **A table compiles**: synthetic JSON → `make_tables.py` → the .tex compiles inside a
   minimal booktabs/threeparttable document (pdflatex, nonstopmode).
3. **Failure fails**: corrupt one downstream claim (not the shared source), run
   `numbers_audit.py`, assert exit code 1; delete the sidecar, run `check_figures.py`,
   assert exit code 1. If either exits 0, the gates are decorative — fix before use.

Everything heavier (visual regression, full test suites) is deliberately out of scope.

## 10. Hard rules

- Width = venue width exactly, included at scale 1; per-element font floors **and
  ceilings** respected; `exact` mode for anything the manuscript includes.
- One colour role per meaning for the whole paper; series also separated by
  marker/linestyle/hatch; grayscale proof always produced.
- Every number on a figure or table comes from a results file; audits recompute from
  upstream; gates exit 1 on failure and are themselves smoke-tested.
- Chart form chosen from the scientific question (§5); integrity checks of §6 run
  before drawing.
- Pipelines/schematics: decline and point to the paper-pipelines skill.

## Workflow summary

bootstrap (once per paper, §1) → for each figure: question → form (§5) → integrity
(§6) → script from §4 → `S.save` → gates (§8) → show the PNG, give the caption draft
and the `\includegraphics[width=\textwidth]{...}` line.

## Skill contents (canonical templates — copy, don't regenerate)

`assets/` holds complete, smoke-tested implementations of everything §1 generates.
If `assets/` is not beside this SKILL.md (the skill was installed as SKILL.md
only), fetch it from the canonical repo before bootstrapping:
`git clone --depth 1 https://github.com/ijamshidi87/paper-figures` (or download
`https://raw.githubusercontent.com/ijamshidi87/paper-figures/main/assets/<file>`).
Never re-write these files from memory when they can be fetched.
At bootstrap, copy each file to the target path named in its header comment, then
adapt only `paper_config.yaml` (venue, stage, results_dir, palette roles):

| asset                     | target path in the paper repo        |
|---------------------------|--------------------------------------|
| `assets/paper_config.yaml`| `paper_config.yaml`                  |
| `assets/style.py`         | `figures/style.py`                   |
| `assets/check_figures.py` | `scripts/check_figures.py`           |
| `assets/numbers_audit.py` | `scripts/numbers_audit.py`           |
| `assets/smoke_test.py`    | `scripts/smoke_test.py`              |
| `assets/make_tables.py`   | `tables/make_tables.py`              |
| `assets/fNN_template.py`  | `figures/fNN_slug.py` (one per figure)|

Per-paper claims go in `scripts/claims.py` (format in `numbers_audit.py`'s
docstring); per-paper table specs in `tables/tables_spec.py` (format in
`make_tables.py`'s docstring). `references/venue_profiles.md` records each
profile's source and verification notes; `references/attribution.md` records
the [E] provenance. Run `python scripts/smoke_test.py` from the repo root right
after copying, before producing any real figure.
