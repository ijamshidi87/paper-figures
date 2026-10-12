# paper-figures — a Claude skill for publication-ready figures and tables

A lightweight [Claude skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)
that builds matplotlib data figures and LaTeX tables for research manuscripts in a
fixed design system, with quality gates that actually fail.

- **Okabe-Ito role palette** — one colour per meaning for the whole paper, plus
  parallel markers / line styles / hatches so every series survives grayscale.
- **Venue-exact widths** — TRR/TRB, Nature, Elsevier, ACM (acmsmall), IEEE, generic;
  per-element font floors *and* ceilings (e.g. Nature's 7 pt max).
- **Exact-size export** — vector PDF + PNG + grayscale proof + a hash-bound
  `.meta.json` sidecar recording every text element's size.
- **Tables from results files** — booktabs / threeparttable / tabularx / xltabular,
  chosen by the table's shape; never hand-typed `.tex`.
- **Gates that exit 1** — `check_figures.py` (8 gates) and `numbers_audit.py`
  (claims recomputed from upstream data), both smoke-tested to prove they fail.

Not for pipeline/framework/schematic diagrams (those belong to a separate
`paper-pipelines` skill).

## Install

**Claude (claude.ai / desktop):** download this repo as a ZIP and upload it under
*Settings → Capabilities → Skills*. The folder must contain `SKILL.md` at its top
level.

**Claude Code:** clone into your skills directory:

```bash
git clone https://github.com/ijamshidi87/paper-figures ~/.claude/skills/paper-figures
```

If only `SKILL.md` is installed, the skill fetches `assets/` from this repo at
bootstrap.

## Use in a paper repo

Ask Claude for a figure or table for your paper. On first use it bootstraps the repo:

| asset                      | copied to                    |
|----------------------------|------------------------------|
| `assets/paper_config.yaml` | `paper_config.yaml`          |
| `assets/style.py`          | `figures/style.py`           |
| `assets/check_figures.py`  | `scripts/check_figures.py`   |
| `assets/numbers_audit.py`  | `scripts/numbers_audit.py`   |
| `assets/smoke_test.py`     | `scripts/smoke_test.py`      |
| `assets/make_tables.py`    | `tables/make_tables.py`      |
| `assets/fNN_template.py`   | `figures/fNN_slug.py`        |

Then, from the paper repo root:

```bash
python scripts/smoke_test.py                       # 3 smoke tests, exit 1 on failure
python figures/f03_plane.py                        # one file = one figure
python scripts/check_figures.py --venue trb --stage final
python scripts/numbers_audit.py scripts/claims.py
python tables/make_tables.py tables/tables_spec.py
```

Requirements: Python ≥ 3.10, matplotlib, Pillow; `pdffonts` (poppler-utils) for the
authoritative font-embedding gate; a LaTeX install with booktabs/threeparttable for
the table-compile smoke test.

## Verified

All three smoke tests pass on all six venue profiles, and each gate was checked
against a deliberate violation (tight-mode export, wrong width, over-ceiling text,
hex literal in a figure script, missing docstring, stale sidecar, empty audit).

## Provenance

Rules marked **[E]** were extracted from Amir Rafe's public MIT-licensed paper
repositories; the code here is a fresh implementation. See
[`references/attribution.md`](references/attribution.md).

## License

[MIT](LICENSE)
