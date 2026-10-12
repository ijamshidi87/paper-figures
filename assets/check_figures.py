#!/usr/bin/env python3
# scripts/check_figures.py — quality gates for paper figures (paper-figures skill).
# Target path in a paper repo: <repo>/scripts/check_figures.py
"""Quality gates (§8 of the skill). All must pass; any failure => sys.exit(1).

  1. sidecar exists and its pdf_sha256 matches the PDF (stale metadata fails)
  2. mode == "exact" for any figure the manuscript includes
  3. PDF MediaBox width == profile width (±0.01 in), FULL or COL
  4. every sidecar text within its per-element floor AND ceiling
  5. fonts embedded (pdffonts: all emb = yes; byte-level fallback if absent)
  6. no hex literal in figures/*.py except style.py
  7. every figure script (fNN_*.py) has a panel-describing docstring (AST parse)
  8. grayscale proof exists

Usage:
  check_figures.py [pdf ...] [--venue V] [--stage S] [--figdir figures]
With no PDFs given, checks every PDF under <figdir>/out/. A "tight"-mode PDF
always fails gate 2 — it is a preview, never the included file.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}")
FIG_SCRIPT_RE = re.compile(r"^f\d{2,}_.+\.py$")
MEDIABOX_RE = re.compile(
    rb"/MediaBox\s*\[\s*([0-9.+-]+)\s+([0-9.+-]+)\s+([0-9.+-]+)\s+([0-9.+-]+)\s*\]")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_style(figdir: Path):
    sys.path.insert(0, str(figdir.resolve()))
    import style  # the repo's own figures/style.py
    return style


def mediabox_width_in(pdf: Path) -> float | None:
    m = MEDIABOX_RE.search(pdf.read_bytes())
    if not m:
        return None
    x0, _, x1, _ = (float(v) for v in m.groups())
    return (x1 - x0) / 72.0


def fonts_embedded(pdf: Path) -> tuple[bool, str]:
    """True iff every font in the PDF is embedded."""
    if shutil.which("pdffonts"):
        out = subprocess.run(["pdffonts", str(pdf)],
                             capture_output=True, text=True).stdout
        lines = [ln for ln in out.splitlines()[2:] if ln.strip()]
        if not lines:
            return True, "no fonts in PDF"
        # trailing columns are single tokens: ... emb sub uni object ID(gen)
        bad = [ln.split()[0] for ln in lines
               if len(ln.split()) >= 5 and ln.split()[-5] != "yes"]
        return (not bad), ("pdffonts: all embedded" if not bad
                           else f"pdffonts: not embedded: {', '.join(bad)}")
    # Fallback heuristic when poppler is absent: a FontFile stream must exist
    # for any declared BaseFont (matplotlib fonttype 42 always embeds).
    data = pdf.read_bytes()
    if b"/BaseFont" not in data:
        return True, "no fonts in PDF (heuristic)"
    ok = b"/FontFile" in data  # matches FontFile, FontFile2, FontFile3
    return ok, ("heuristic: FontFile stream present" if ok
                else "heuristic: /BaseFont without any /FontFile stream "
                     "(install poppler-utils for the authoritative check)")


def text_bounds(profile: dict, kind: str, abs_floor: float) -> tuple[float, float]:
    """Per-element [floor, ceiling] in pt (§2). Ceiling = inf where none stated."""
    tmin, tmax = profile["text_min"], profile["text_max"]
    tick_min, panel_pt = profile["tick_min"], profile["panel_pt"]
    hi = tmax if tmax is not None else float("inf")
    if kind == "tick" or kind == "footnote":
        lo = tick_min
    elif kind == "panel_label":
        # panel labels may exceed the regular ceiling, but only up to panel_pt
        lo = tmin
        if tmax is not None:
            hi = max(tmax, panel_pt)
    else:  # label, legend, annotation, title
        lo = tmin
    return max(lo, abs_floor), hi


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdfs", nargs="*", help="PDF(s); default: <figdir>/out/*.pdf")
    ap.add_argument("--venue", default=None,
                    help="expected venue (default: each sidecar's own)")
    ap.add_argument("--stage", default=None,
                    help="expected stage (default: each sidecar's own)")
    ap.add_argument("--figdir", default="figures",
                    help="directory holding style.py and the figure scripts")
    args = ap.parse_args()

    figdir = Path(args.figdir)
    if not (figdir / "style.py").exists():
        print(f"FAIL: {figdir}/style.py not found — run from the repo root "
              f"or pass --figdir")
        sys.exit(1)
    S = load_style(figdir)

    failures: list[str] = []

    def fail(msg: str) -> None:
        failures.append(msg)
        print(f"FAIL: {msg}")

    def ok(msg: str) -> None:
        print(f"  ok: {msg}")

    # ---- repo-level gates 6 and 7 -------------------------------------------
    for py in sorted(figdir.glob("*.py")):
        if py.name == "style.py":
            continue
        src = py.read_text(encoding="utf-8")
        if HEX_RE.search(src):
            fail(f"gate 6: hex literal in {py} — colours come only from style.C")
        else:
            ok(f"gate 6: no hex in {py.name}")
        if FIG_SCRIPT_RE.match(py.name):
            try:
                doc = ast.get_docstring(ast.parse(src))
            except SyntaxError as e:
                fail(f"gate 7: {py} does not parse: {e}")
                continue
            if not doc or len(doc.strip()) < 20:
                fail(f"gate 7: {py.name} lacks a panel-describing docstring "
                     f"(the caption draft)")
            else:
                ok(f"gate 7: docstring present in {py.name}")

    # ---- per-PDF gates 1–5 and 8 --------------------------------------------
    pdfs = [Path(p) for p in args.pdfs] or sorted((figdir / "out").glob("*.pdf"))
    if not pdfs:
        fail("no PDFs to check (none given, none in figures/out/)")
    for pdf in pdfs:
        print(f"-- {pdf}")
        if not pdf.exists():
            fail(f"{pdf} does not exist")
            continue
        side = pdf.with_suffix("").with_name(pdf.stem + ".meta.json")
        if not side.exists():
            fail(f"gate 1: sidecar {side.name} missing — metadata must belong "
                 f"to this exact PDF")
            continue
        meta = json.loads(side.read_text(encoding="utf-8"))

        # gate 1: hash binding
        if meta.get("pdf_sha256") != sha256(pdf):
            fail(f"gate 1: sidecar {side.name} is stale — pdf_sha256 does not "
                 f"match the PDF; re-run the figure script")
            continue
        ok("gate 1: sidecar matches PDF hash")
        cfg = Path("paper_config.yaml")
        if cfg.exists() and meta.get("config_sha256") not in (None, sha256(cfg)):
            print(f"  warn: paper_config.yaml changed since {pdf.name} was saved "
                  f"— re-run the figure script")

        venue = args.venue or meta.get("venue")
        stage = args.stage or meta.get("stage")
        if args.venue and meta.get("venue") != args.venue:
            fail(f"gate 2: {pdf.name} saved for venue {meta.get('venue')!r}, "
                 f"expected {args.venue!r}")
        if args.stage and meta.get("stage") != args.stage:
            fail(f"gate 2: {pdf.name} saved for stage {meta.get('stage')!r}, "
                 f"expected {args.stage!r}")
        if venue not in S.PROFILES:
            fail(f"unknown venue {venue!r} in sidecar")
            continue
        profile = S.PROFILES[venue]

        # gate 2: exact mode
        if meta.get("mode") != "exact":
            fail(f"gate 2: {pdf.name} saved with mode={meta.get('mode')!r} — "
                 f"only exact-mode PDFs may be included in the manuscript")
        else:
            ok("gate 2: mode == exact")

        # gate 3: MediaBox width == declared width == FULL or COL
        w_pdf = mediabox_width_in(pdf)
        full, col = profile["full_in"], profile["col_in"]
        targets = [full] + ([col] if col else [])
        if w_pdf is None:
            fail(f"gate 3: could not read MediaBox of {pdf.name}")
        elif meta.get("mode") == "exact":
            if not any(abs(w_pdf - t) <= 0.01 for t in targets):
                fail(f"gate 3: {pdf.name} MediaBox width {w_pdf:.3f} in is not "
                     f"the {venue} full ({full:.3f}) or column width (±0.01 in)")
            elif abs(w_pdf - float(meta.get("target_w_in", w_pdf))) > 0.01:
                fail(f"gate 3: {pdf.name} MediaBox {w_pdf:.3f} in differs from "
                     f"declared figsize {meta.get('target_w_in')} in")
            else:
                ok(f"gate 3: width {w_pdf:.3f} in matches {venue} profile")
        # (tight-mode PDFs are exempt from the width gate but already failed gate 2)

        # gate 4: per-element font floors AND ceilings
        bad_texts = []
        for t in meta.get("texts", []):
            lo, hi = text_bounds(profile, t.get("kind", "label"), S.ABS_FLOOR_PT)
            if not (lo - 1e-6 <= float(t["pt"]) <= hi + 1e-6):
                bad_texts.append(f"{t['pt']:g} pt {t.get('kind')} "
                                 f"{t['s']!r} (allowed {lo:g}–{hi:g})")
        if bad_texts:
            for b in bad_texts:
                fail(f"gate 4: {pdf.name}: {b}")
        else:
            ok(f"gate 4: all {len(meta.get('texts', []))} texts within "
               f"per-element bounds")

        # gate 5: fonts embedded
        emb, how = fonts_embedded(pdf)
        (ok if emb else fail)(f"gate 5: {how}" if emb
                              else f"gate 5: {pdf.name}: {how}")

        # gate 8: grayscale proof
        gray = pdf.parent / "gray" / (pdf.stem + ".png")
        if gray.exists():
            ok("gate 8: grayscale proof exists")
        else:
            fail(f"gate 8: grayscale proof {gray} missing")

    print(f"\n{'ALL GATES PASS' if not failures else f'{len(failures)} FAILURE(S)'}")
    sys.exit(1 if failures else 0)   # gate zero: real failure propagation


if __name__ == "__main__":
    main()
