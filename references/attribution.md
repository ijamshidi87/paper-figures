# Provenance and attribution

Rules in SKILL.md marked **[E] (extracted practice)** were observed in Amir Rafe's
public, MIT-licensed paper repositories: the fixed-role Okabe-Ito palette, parallel
marker/linestyle/hatch encodings for grayscale robustness, `apply()`-style rcParams
profiles, one-file-one-figure scripts named `fNN_slug.py`, tables generated from
results files, and the style-audit script pattern.

The code in `assets/` is a fresh implementation of those practices written for this
skill — it is not copied verbatim. **If you ever copy code verbatim from one of the
source repos into a paper, keep a one-line attribution comment with the repo URL**
(MIT license requirement in spirit; also plain good practice).

Two cautionary examples from the source repos are encoded as requirements here,
because [E] is evidence, not law:

- `f04_calibration.py` shipped 4.8 pt text — below any venue floor. Hence the
  per-element floors with an absolute 5 pt minimum, checked by gate 4.
- `r7_style_audit.py` ended with `sys.exit(0 if ... else 0)` — a gate that could
  never fail. Hence smoke test 3 ("failure fails"), which corrupts a claim and
  deletes a sidecar and asserts both gates actually exit 1.

Rules marked **[R]** are this skill's own requirements and win wherever [E] and [R]
conflict.
