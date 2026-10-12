#!/usr/bin/env python3
# scripts/numbers_audit.py — numeric audit for the paper (paper-figures skill).
# Target path in a paper repo: <repo>/scripts/numbers_audit.py
"""Numeric audit with the circularity rule [R]: every printed claim is
RECOMPUTED FROM AN UPSTREAM ARTEFACT (the raw/intermediate data the results
were derived from), never merely re-read from the same JSON the figure read.

Claims live in a claims file (default: scripts/claims.py) that defines

    def claims(check):
        # want = recomputed from upstream (raw CSV / intermediate parquet ...)
        # got  = the number as the figures/tables consume it (results file)
        check("t1_mean_crashes", got=est["mean"], want=raw_mean(...), tol=1e-9)

check(claim_id, got, want, tol=0.0) collects failures; this script exits 1 if
any check fails — or if no claims are registered at all, because an empty audit
is a decorative gate. Numeric agreement is still not scientific correctness:
§6 of the skill covers what the audit cannot (a wrong denominator used
consistently passes the audit).

Usage:  numbers_audit.py [claims_file.py]
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


class Audit:
    """Collects check() results; report() prints them; failures drive exit 1."""

    def __init__(self) -> None:
        self.results: list[tuple[str, float, float, float, bool]] = []

    def check(self, claim_id: str, got, want, tol: float = 0.0) -> bool:
        try:
            got_f, want_f = float(got), float(want)
            passed = abs(got_f - want_f) <= tol
        except (TypeError, ValueError):
            got_f = want_f = float("nan")
            passed = got == want  # non-numeric claims compare exactly
        self.results.append((claim_id, got, want, tol, passed))
        return passed

    @property
    def failures(self) -> list:
        return [r for r in self.results if not r[4]]

    def report(self) -> None:
        for claim_id, got, want, tol, passed in self.results:
            mark = " ok " if passed else "FAIL"
            print(f"{mark}: {claim_id}: printed {got!r} vs recomputed {want!r} "
                  f"(tol {tol})")
        print(f"\n{len(self.results)} claim(s), {len(self.failures)} failed")


# ---- small helpers for common upstream recomputations ------------------------
def read_csv(path: str | Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def csv_column(path: str | Path, col: str) -> list[float]:
    return [float(r[col]) for r in read_csv(path)]


def csv_mean(path: str | Path, col: str) -> float:
    vals = csv_column(path, col)
    return sum(vals) / len(vals)


def read_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run_claims_file(path: Path) -> Audit:
    """Execute a claims file (defines claims(check)) and return the Audit."""
    ns: dict = {"__file__": str(path), "__name__": "claims"}
    code = compile(path.read_text(encoding="utf-8"), str(path), "exec")
    exec(code, ns)
    if "claims" not in ns or not callable(ns["claims"]):
        print(f"FAIL: {path} does not define a callable claims(check)")
        sys.exit(1)
    audit = Audit()
    ns["claims"](audit.check)
    return audit


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("scripts/claims.py")
    if not path.exists():
        print(f"FAIL: claims file {path} not found — register at least one "
              f"claim per printed number (see this script's docstring)")
        sys.exit(1)
    audit = run_claims_file(path)
    audit.report()
    if not audit.results:
        print("FAIL: no claims registered — an empty audit is a decorative gate")
        sys.exit(1)
    sys.exit(1 if audit.failures else 0)   # gate zero: real failure propagation


if __name__ == "__main__":
    main()
