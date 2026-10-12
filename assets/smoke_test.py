#!/usr/bin/env python3
# scripts/smoke_test.py — the three minimal executable tests (paper-figures skill, §9).
# Target path in a paper repo: <repo>/scripts/smoke_test.py  — run from the repo root.
"""Three smoke tests, run at bootstrap and on demand. Exit 1 if any fails.

1. A figure builds: 10-row synthetic results file -> template-style figure ->
   exact-mode PDF+PNG+sidecar produced, check_figures.py passes.
2. A table compiles: synthetic JSON -> make_tables.py -> the .tex compiles inside
   a minimal booktabs/threeparttable document (pdflatex, nonstopmode; if no LaTeX
   engine is installed, a structural check runs instead and says so).
3. Failure fails: corrupt one downstream claim (not the shared source) ->
   numbers_audit.py must exit 1; delete the sidecar -> check_figures.py must
   exit 1. If either exits 0, the gates are decorative — fix before use.

Usage:  python scripts/smoke_test.py [--keep]
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable

SMOKE_FIGURE = '''\
"""Smoke figure. Dot plot of ten synthetic group estimates with 95% CI whiskers.

(a) Point estimates with CI whiskers, sorted as generated; blue (obs role) is
the only series. Values come from results/_smoke/rows.csv; nothing is typed
by hand. Chart form (section 5): effect sizes with uncertainty -> dot plot.
"""
import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
import style as S  # noqa: E402

RESULTS = Path(__file__).parent.parent / "results" / "_smoke"


def load():
    with open(RESULTS / "rows.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    rows = load()
    S.apply_from_config()
    fig, ax = plt.subplots(figsize=(S.FULL, 2.4))
    y = range(len(rows))
    ax.hlines(y, [float(r["lo"]) for r in rows], [float(r["hi"]) for r in rows],
              color=S.C["obs"], linewidth=1.0)
    ax.plot([float(r["est"]) for r in rows], y, S.MARKERS["obs"],
            color=S.C["obs"], markersize=3.5, linestyle="none")
    ax.set_yticks(list(y), [r["group"] for r in rows])
    ax.set_xlabel("Estimate (95% CI)")
    S.light_grid(ax, axis="x")
    S.panel_title(ax, "a", "Synthetic estimates by group")
    S.finish(fig)
    S.save(fig, "f99_smoke")


if __name__ == "__main__":
    main()
'''

SMOKE_TABLE_SPEC = '''\
"""Smoke table spec: threeparttable from results/_smoke/table.json."""
import json
from pathlib import Path

RESULTS = Path(__file__).parent.parent / "results" / "_smoke"


def build(T):
    d = json.loads((RESULTS / "table.json").read_text(encoding="utf-8"))
    rows = [[m["model"], fmt_est_ci(m["or"], m["lo"], m["hi"]), fmt_p(m["p"])]
            for m in d["models"]]
    T.add(Table("smoke", caption="Smoke test: synthetic model estimates.",
                label="tab:smoke", columns=["Model", "OR [95% CI]", "p"],
                rows=rows,
                notes="OR = odds ratio; CI = confidence interval. Synthetic."))
'''

SMOKE_CLAIMS = '''\
"""Smoke claims: recompute the printed mean from the UPSTREAM raw.csv."""
from pathlib import Path

from numbers_audit import csv_mean, read_json

RESULTS = Path(__file__).parent.parent / "results" / "_smoke"


def claims(check):
    est = read_json(RESULTS / "estimates.json")          # downstream (printed)
    want = csv_mean(RESULTS / "raw.csv", "value")        # recomputed upstream
    check("smoke_mean_value", got=est["mean"], want=want, tol=1e-9)
'''

TEX_DOC = r"""\documentclass{article}
\usepackage{booktabs}
\usepackage{threeparttable}
\usepackage{tabularx}
\usepackage{float}
\usepackage[table]{xcolor}
\begin{document}
\input{%s}
\end{document}
"""


def run(cmd: list[str], cwd: Path = ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--keep", action="store_true",
                    help="keep the smoke artefacts for inspection")
    args = ap.parse_args()

    smoke_dir = ROOT / "results" / "_smoke"
    smoke_dir.mkdir(parents=True, exist_ok=True)
    fig_py = ROOT / "figures" / "f99_smoke.py"
    spec_py = ROOT / "tables" / "_smoke_spec.py"
    claims_py = ROOT / "scripts" / "_smoke_claims.py"
    out = ROOT / "figures" / "out"
    created = [fig_py, spec_py, claims_py]
    failures: list[str] = []

    def result(name: str, passed: bool, detail: str = "") -> None:
        print(f"{'PASS' if passed else 'FAIL'}: {name}" + (f" — {detail}" if detail else ""))
        if not passed:
            failures.append(name)

    # ---- test 1: a figure builds and the gates pass ---------------------------
    rng = random.Random(42)
    with open(smoke_dir / "rows.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["group", "est", "lo", "hi"])
        for i in range(10):
            est = rng.uniform(0.5, 2.0)
            w.writerow([f"G{i+1:02d}", round(est, 3),
                        round(est - rng.uniform(0.05, 0.3), 3),
                        round(est + rng.uniform(0.05, 0.3), 3)])
    fig_py.write_text(SMOKE_FIGURE, encoding="utf-8")
    r = run([PY, str(fig_py)])
    if r.returncode != 0:
        result("1 figure builds", False, r.stderr.strip()[-400:])
    else:
        pdf = out / "f99_smoke.pdf"
        produced = all((out / n).exists() for n in
                       ("f99_smoke.pdf", "f99_smoke.png", "f99_smoke.meta.json")) \
            and (out / "gray" / "f99_smoke.png").exists()
        if not produced:
            result("1 figure builds", False, "PDF/PNG/gray/sidecar not all produced")
        else:
            rc = run([PY, "scripts/check_figures.py", str(pdf)])
            result("1 figure builds (gates pass)", rc.returncode == 0,
                   "" if rc.returncode == 0 else rc.stdout.strip()[-400:])

    # ---- test 2: a table compiles --------------------------------------------
    (smoke_dir / "table.json").write_text(json.dumps({"models": [
        {"model": "Poisson", "or": 1.21, "lo": 1.05, "hi": 1.40, "p": 0.008},
        {"model": "Neg. binomial", "or": 1.18, "lo": 0.98, "hi": 1.41, "p": 0.078},
        {"model": "Zero-inflated", "or": 1.25, "lo": 1.07, "hi": 1.46, "p": 0.0004},
    ]}), encoding="utf-8")
    spec_py.write_text(SMOKE_TABLE_SPEC, encoding="utf-8")
    r = run([PY, "tables/make_tables.py", str(spec_py)])
    tex = ROOT / "tables" / "out" / "table_smoke.tex"
    if r.returncode != 0 or not tex.exists():
        result("2 table compiles", False, (r.stdout + r.stderr).strip()[-400:])
    else:
        engine = shutil.which("pdflatex") or shutil.which("lualatex")
        if engine:
            with tempfile.TemporaryDirectory() as td:
                doc = Path(td) / "doc.tex"
                doc.write_text(TEX_DOC % tex.resolve().as_posix(), encoding="utf-8")
                rc = run([engine, "-interaction=nonstopmode", "-halt-on-error",
                          doc.name], cwd=Path(td))
                result("2 table compiles (pdflatex)", rc.returncode == 0,
                       "" if rc.returncode == 0 else rc.stdout.strip()[-400:])
        else:
            src = tex.read_text(encoding="utf-8")
            ok = all(k in src for k in ("\\toprule", "\\midrule", "\\bottomrule")) \
                and "\\hline" not in src and "|" not in src.split("\n")[0]
            result("2 table compiles (structural check only — no LaTeX engine "
                   "found; install texlive for the real compile)", ok)

    # ---- test 3: failure fails ------------------------------------------------
    raw_vals = [round(rng.uniform(10, 20), 4) for _ in range(10)]
    with open(smoke_dir / "raw.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["value"])
        w.writerows([[v] for v in raw_vals])
    est_path = smoke_dir / "estimates.json"
    good = {"mean": sum(raw_vals) / len(raw_vals)}
    est_path.write_text(json.dumps(good), encoding="utf-8")
    claims_py.write_text(SMOKE_CLAIMS, encoding="utf-8")

    rc = run([PY, "scripts/numbers_audit.py", str(claims_py)])
    result("3a audit passes on consistent claim", rc.returncode == 0,
           "" if rc.returncode == 0 else rc.stdout.strip()[-300:])

    # corrupt the DOWNSTREAM claim (not the shared upstream source)
    est_path.write_text(json.dumps({"mean": good["mean"] + 1.0}), encoding="utf-8")
    rc = run([PY, "scripts/numbers_audit.py", str(claims_py)])
    result("3b corrupted claim -> numbers_audit exits 1", rc.returncode == 1,
           "" if rc.returncode == 1 else
           f"exit code {rc.returncode} — the audit gate is decorative")
    est_path.write_text(json.dumps(good), encoding="utf-8")

    sidecar = out / "f99_smoke.meta.json"
    if sidecar.exists():
        hidden = sidecar.with_suffix(".json.hidden")
        sidecar.rename(hidden)
        rc = run([PY, "scripts/check_figures.py", str(out / "f99_smoke.pdf")])
        result("3c missing sidecar -> check_figures exits 1", rc.returncode == 1,
               "" if rc.returncode == 1 else
               f"exit code {rc.returncode} — the figure gate is decorative")
        hidden.rename(sidecar)
    else:
        result("3c missing sidecar -> check_figures exits 1", False,
               "no sidecar from test 1 to remove")

    # ---- cleanup ---------------------------------------------------------------
    if not args.keep:
        for p in created:
            p.unlink(missing_ok=True)
        for n in ("f99_smoke.pdf", "f99_smoke.png", "f99_smoke.meta.json"):
            (out / n).unlink(missing_ok=True)
        (out / "gray" / "f99_smoke.png").unlink(missing_ok=True)
        (ROOT / "tables" / "out" / "table_smoke.tex").unlink(missing_ok=True)
        shutil.rmtree(smoke_dir, ignore_errors=True)

    print(f"\n{'ALL SMOKE TESTS PASS' if not failures else f'{len(failures)} SMOKE FAILURE(S)'}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
