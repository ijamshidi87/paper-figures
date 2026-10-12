#!/usr/bin/env python3
# tables/make_tables.py — LaTeX tables generated from results files (paper-figures skill).
# Target path in a paper repo: <repo>/tables/make_tables.py
"""Tables are generated from results files — never hand-typed .tex [E].

A spec file (default: tables/tables_spec.py) defines

    def build(T):
        rows = [...]                    # read from results/*.json|csv — no literals
        T.add(Table("model_fit", caption="...", label="tab:fit",
                    columns=["Model", "AIC", "RMSE"], rows=rows,
                    notes="OR = odds ratio; CI = 95% confidence interval."))

Environment is chosen from the table's shape (§7): tabular+booktabs by default;
threeparttable when there are notes or star definitions; tabularx when a column
must wrap (wrap_cols); xltabular when long=True. Booktabs only, @{} at both
edges, numbers right-aligned (decimal alignment via a siunitx align string is
the author's option). Placement comes from the venue profile in figures/style.py,
never hardcoded. One file per table: tables/out/table_<slug>.tex, \\input in the
manuscript.

Usage:  make_tables.py [spec_file.py]
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "figures"))
try:
    import style as S  # venue placement + palette for \cellcolor
except ImportError:  # pragma: no cover - style.py is generated at bootstrap
    S = None

_ESC = {"&": r"\&", "%": r"\%", "#": r"\#", "_": r"\_"}


def esc(s) -> str:
    """Escape the LaTeX specials that appear in prose cells."""
    out = str(s)
    for k, v in _ESC.items():
        out = out.replace(k, v)
    return out


# ---- number formatting: SE/CI beside the estimate [R] ------------------------
def fmt_est_se(est: float, se: float, nd: int = 2) -> str:
    return f"{est:.{nd}f} ({se:.{nd}f})"


def fmt_est_ci(est: float, lo: float, hi: float, nd: int = 2) -> str:
    return f"{est:.{nd}f} [{lo:.{nd}f}, {hi:.{nd}f}]"


def fmt_p(p: float) -> str:
    """Exact p preferred; APA-style floor below 0.001 ($<$ renders in OT1 too)."""
    return "$<$0.001" if p < 0.001 else f"{p:.3f}"


def cellcolor(role: str, frac: float = 0.75) -> str:
    """\\cellcolor from the palette ramp only (tint of a role colour)."""
    if S is None:
        raise RuntimeError("figures/style.py not found; cell colour comes "
                           "only from the palette ramp")
    r, g, b = S.tint(S.C[role], frac)
    hexv = f"{round(r*255):02X}{round(g*255):02X}{round(b*255):02X}"
    return f"\\cellcolor[HTML]{{{hexv}}}"


def _venue_placement() -> str:
    if S is not None:
        cfg = S.read_config()
        venue = cfg.get("venue", "generic")
        return S.PROFILES.get(venue, S.PROFILES["generic"])["placement"]
    return "tbp"


class Table:
    """One table: shape decides the environment; render() emits booktabs LaTeX."""

    def __init__(self, slug: str, caption: str, label: str,
                 columns: list[str], rows: list[list],
                 notes: str | None = None, align: str | None = None,
                 wrap_cols: tuple[int, ...] = (), long: bool = False,
                 stars: str | None = None, placement: str | None = None,
                 escape: bool = True) -> None:
        self.slug, self.caption, self.label = slug, caption, label
        self.columns, self.rows = columns, rows
        self.notes, self.stars = notes, stars
        self.wrap_cols, self.long = tuple(wrap_cols), long
        self.placement = placement  # None -> venue profile
        self.escape = escape
        n = len(columns)
        if align is None:
            cols = []
            for i in range(n):
                if i in self.wrap_cols:
                    cols.append("X")           # tabularx wrapping column
                else:
                    cols.append("l" if i == 0 else "r")  # numbers right-aligned
            align = "".join(cols)
        self.align = f"@{{}}{align}@{{}}"      # @{} at both edges [R]

    # -- environment choice by shape (§7) --------------------------------------
    @property
    def env(self) -> str:
        if self.long:
            return "xltabular"
        if self.wrap_cols:
            return "tabularx"
        if self.notes or self.stars:
            return "threeparttable"
        return "tabular"

    def _cell(self, v) -> str:
        return esc(v) if self.escape else str(v)

    def _body(self) -> str:
        head = " & ".join(f"\\textbf{{{esc(c)}}}" for c in self.columns)
        lines = ["\\toprule", head + " \\\\", "\\midrule"]
        lines += [" & ".join(self._cell(v) for v in row) + " \\\\"
                  for row in self.rows]
        lines.append("\\bottomrule")
        return "\n".join(lines)

    def _note_block(self) -> str:
        parts = []
        if self.notes:
            parts.append(f"\\textit{{Note.}} {esc(self.notes)}")
        if self.stars:
            parts.append(esc(self.stars))   # star definitions, venue-dependent
        return " ".join(parts)

    def render(self) -> str:
        placement = self.placement or _venue_placement()
        env = self.env
        out = [f"% tables/out/table_{self.slug}.tex — generated by "
               f"tables/make_tables.py; do not edit by hand.",
               f"\\begin{{table}}[{placement}]", "\\centering",
               f"\\caption{{{esc(self.caption)}}}",
               f"\\label{{{self.label}}}"]
        note = self._note_block()
        if env == "threeparttable":
            out += ["\\begin{threeparttable}",
                    f"\\begin{{tabular}}{{{self.align}}}",
                    self._body(), "\\end{tabular}"]
            if note:
                out += ["\\begin{tablenotes}[flushleft]", "\\scriptsize",
                        f"\\item[] {note}", "\\end{tablenotes}"]
            out.append("\\end{threeparttable}")
        elif env == "tabularx":
            out += [f"\\begin{{tabularx}}{{\\linewidth}}{{{self.align}}}",
                    self._body(), "\\end{tabularx}"]
            if note:
                out.append(f"\\par\\smallskip{{\\scriptsize {note}\\par}}")
        elif env == "xltabular":
            # xltabular floats itself; drop the table wrapper
            out = [out[0],
                   f"\\begin{{xltabular}}{{\\linewidth}}{{{self.align}}}",
                   f"\\caption{{{esc(self.caption)}}}\\label{{{self.label}}}\\\\",
                   self._body(), "\\end{xltabular}"]
            if note:
                out.append(f"{{\\scriptsize {note}\\par}}")
            return "\n".join(out) + "\n"
        else:  # plain tabular + booktabs
            out += [f"\\begin{{tabular}}{{{self.align}}}",
                    self._body(), "\\end{tabular}"]
            if note:
                out.append(f"\\par\\smallskip{{\\scriptsize {note}\\par}}")
        out.append("\\end{table}")
        return "\n".join(out) + "\n"

    def write(self, outdir: Path | None = None) -> Path:
        outdir = outdir or HERE / "out"
        outdir.mkdir(parents=True, exist_ok=True)
        path = outdir / f"table_{self.slug}.tex"
        path.write_text(self.render(), encoding="utf-8")
        return path


class Registry:
    def __init__(self) -> None:
        self.tables: list[Table] = []

    def add(self, table: Table) -> Table:
        self.tables.append(table)
        return table

    def write_all(self, outdir: Path | None = None) -> list[Path]:
        return [t.write(outdir) for t in self.tables]


def run_spec_file(path: Path) -> Registry:
    ns: dict = {"__file__": str(path), "__name__": "tables_spec",
                "Table": Table,
                "fmt_est_se": fmt_est_se, "fmt_est_ci": fmt_est_ci,
                "fmt_p": fmt_p, "cellcolor": cellcolor}
    code = compile(path.read_text(encoding="utf-8"), str(path), "exec")
    exec(code, ns)
    if "build" not in ns or not callable(ns["build"]):
        print(f"FAIL: {path} does not define a callable build(T)")
        sys.exit(1)
    reg = Registry()
    ns["build"](reg)
    return reg


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "tables_spec.py"
    if not path.exists():
        print(f"FAIL: spec file {path} not found — tables are generated from "
              f"results files, never hand-typed")
        sys.exit(1)
    reg = run_spec_file(path)
    if not reg.tables:
        print("FAIL: spec registered no tables")
        sys.exit(1)
    for p in reg.write_all():
        print(f"wrote {p}")
    sys.exit(0)


if __name__ == "__main__":
    main()
