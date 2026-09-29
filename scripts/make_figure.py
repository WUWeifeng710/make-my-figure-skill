#!/usr/bin/env python3
"""make_figure.py — Programmatic entry point for the Make My Figure engine.

Turn a tabular data file (CSV/TSV/TXT/Excel) into publication-ready scientific
plots / multi-panel figures, with a machine-readable PlotSpec sidecar for
reproducibility.

This is a thin CLI wrapper over the `make_my_figure_core` package. Install that
package first (see SKILL.md). Headless by design: forces the Matplotlib "Agg"
backend, so it works without a display or a GUI.

Usage examples
--------------
# List all supported plot types and their default column mappings
python make_figure.py --list-plots

# Render one plot with auto-detected default mapping
python make_figure.py --data data.csv --plot volcano_plot --out ./figs/volcano

# Render with an explicit column mapping and a statistical test
python make_figure.py --data data.csv --plot boxplot_or_violin_with_points \
    --mapping '{"x":"group","y":"response","kind":"box"}' \
    --stats '{"enabled":true,"test":"welch_t","correction":"none","alpha":0.05}' \
    --out ./figs/box --formats svg,png,pdf

# Print what plots the engine recommends for a table (advisory only)
python make_figure.py --data data.csv --recommend

# Load a full PlotSpec JSON and rebuild the figure exactly
python make_figure.py --spec spec.json --data data.csv --out ./figs/rebuilt
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

# Headless Matplotlib backend — must be set before importing matplotlib.
os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib  # noqa: E402

matplotlib.use("Agg")


def _err(msg: str) -> None:
    print(f"[make_figure] ERROR: {msg}", file=sys.stderr)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", help="Path to the input table (csv/tsv/txt/xlsx).")
    p.add_argument("--spec", help="Path to an existing PlotSpec JSON to rebuild exactly.")
    p.add_argument("--plot", help="Plot type id (see --list-plots).")
    p.add_argument("--mapping", help='JSON string of column roles, e.g. {"x":"group","y":"value"}. '
                                     "When omitted, the engine's default mapping is used.")
    p.add_argument("--mapping-file", help="Path to a JSON file containing the column-role mapping. "
                                          "Preferred over --mapping on Windows/PowerShell (inline JSON "
                                          "quoting is error-prone there).")
    p.add_argument("--stats", help='JSON string of statistics config, e.g. '
                                   '{"enabled":true,"test":"welch_t"}.')
    p.add_argument("--stats-file", help="Path to a JSON file containing the statistics config. "
                                        "Preferred over --stats on Windows/PowerShell.")
    p.add_argument("--style", default="publication", help="Journal style profile name (default: publication).")
    p.add_argument("--out", help="Output base path (no extension). Figure files and "
                                 "the PlotSpec/StatsSpec sidecars are written here.")
    p.add_argument("--formats", help="Comma-separated export formats "
                                     "(svg,png,pdf,tiff,eps). Default: svg,png.")
    p.add_argument("--dpi", type=int, help="Raster DPI (default: 300).")
    p.add_argument("--width-mm", type=float, help="Figure width in mm (journal column width).")
    p.add_argument("--height-mm", type=float, help="Figure height in mm.")
    p.add_argument("--recommend", action="store_true",
                   help="Print plot/statistics recommendations for the table, then exit.")
    p.add_argument("--list-plots", action="store_true",
                   help="List supported plot types with default column mappings, then exit.")
    return p


def _list_plots() -> None:
    from make_my_figure_core import available_plot_types, default_mapping, display_name
    print(f"{len(available_plot_types())} supported plot types:\n")
    for pt in available_plot_types():
        print(f"- {pt:40s}  {display_name(pt)}\n    default mapping: "
              f"{json.dumps(default_mapping(pt), ensure_ascii=False)}")
    sys.exit(0)


def _recommend(data_path: str) -> None:
    from make_my_figure_core import load_table
    from make_my_figure_core.recommendations import recommend_for_table
    info = load_table(data_path)
    print(f"Table: {data_path}  ({info.n_rows} rows x {len(info.columns)} columns)")
    print(f"  columns: {info.columns}")
    print(f"  numeric: {info.numeric_columns}")
    print(f"  categorical: {info.categorical_columns}\n")
    rec = recommend_for_table(info.dataframe, table_name=os.path.basename(data_path))
    recs = getattr(rec, "recommendations", None) or []
    if not recs:
        print("(engine returned no plot recommendations for this table)")
    print("Recommended plots (advisory):")
    for r in recs:
        pt = getattr(r, "plot_type", None) or "?"
        why = getattr(r, "why", "") or getattr(r, "display_name", "")
        conf = getattr(r, "confidence", None)
        conf_s = f"  (confidence {conf:.2f})" if isinstance(conf, (int, float)) else ""
        print(f"- {pt}{conf_s}  {why}")
        st = getattr(r, "suggested_statistics", None)
        if st:
            print(f"    suggested statistics: {json.dumps(st, ensure_ascii=False)}")
    notes = getattr(rec, "notes", None) or []
    for n in notes:
        print(f"note: {n}")
    sys.exit(0)


def _load_spec(spec_path: str, data_path: Optional[str]) -> Dict[str, Any]:
    with open(spec_path, "r", encoding="utf-8") as fh:
        spec = json.load(fh)
    # A saved sidecar may be wrapped: {"plot_spec": {...}, ...}
    if "plot_spec" in spec and isinstance(spec["plot_spec"], dict):
        spec = spec["plot_spec"]
    if data_path:
        spec["input_table"] = data_path
    return spec


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.list_plots:
        _list_plots()
    if args.recommend:
        if not args.data:
            _err("--recommend requires --data")
            return 2
        _recommend(args.data)

    if not args.data:
        _err("--data is required (or use --spec + --data)")
        return 2
    if not args.out:
        _err("--out is required for rendering")
        return 2

    from make_my_figure_core import (default_mapping, load_table, make_spec,
                                     render_to_files)

    def _read_json_file(path: str, what: str) -> Optional[Dict[str, Any]]:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception as e:  # noqa: BLE001
            _err(f"cannot read {what} file {path}: {e}")
            sys.exit(2)

    def _parse_json_arg(raw: Optional[str], what: str) -> Optional[Dict[str, Any]]:
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            _err(f"--{what} is not valid JSON: {e}. On Windows/PowerShell prefer "
                 f"writing the JSON to a file and passing --{what}-file PATH instead.")
            sys.exit(2)

    # 1) Build or load the PlotSpec
    if args.spec:
        spec = _load_spec(args.spec, args.data)
    else:
        if not args.plot:
            _err("--plot is required when not using --spec")
            return 2
        # Resolve mapping: explicit --mapping/--mapping-file wins; only when NEITHER
        # is provided do we fall back to the engine's default mapping. An explicitly
        # passed empty mapping {} is kept as-is (it is a valid user choice), never
        # silently replaced by the default.
        mapping = None
        if args.mapping_file:
            mapping = _read_json_file(args.mapping_file, "mapping")
        elif args.mapping is not None:
            mapping = _parse_json_arg(args.mapping, "mapping")
        else:
            mapping = default_mapping(args.plot)
        stats = _read_json_file(args.stats_file, "stats") if args.stats_file else \
            _parse_json_arg(args.stats, "stats")
        output: Dict[str, Any] = {"formats": args.formats.split(",") if args.formats else ["svg", "png"],
                                  "dpi": args.dpi if args.dpi else 300}
        if args.width_mm:
            output["width_mm"] = args.width_mm
        if args.height_mm:
            output["height_mm"] = args.height_mm
        spec = make_spec(args.plot, args.data, args.style,
                         mapping=mapping, statistics=stats, output=output)

    # 2) Load data
    info = load_table(spec["input_table"])

    # 3) Render and export (figure files + PlotSpec sidecar + StatsSpec sidecar)
    #    render_to_files reads dpi/formats from the spec's output block.
    #    IMPORTANT: only override output settings when the user EXPLICITLY passed
    #    --dpi / --formats (args default is None). When --spec is used to rebuild
    #    an existing figure and these flags are omitted, keep the original spec's
    #    output settings so the "exact rebuild" promise holds.
    spec.setdefault("output", {})
    if args.dpi is not None:
        spec["output"]["dpi"] = args.dpi
    if args.formats is not None:
        spec["output"]["formats"] = args.formats.split(",")
    fmts = spec.get("output", {}).get("formats") or ["svg", "png"]
    out = render_to_files(spec, info.dataframe, args.out, formats=fmts)

    print(f"Figure rendered from {spec['input_table']} (plot_type={spec.get('plot_type')})")
    print(f"  files: {out['files']}")
    print(f"  sidecar: {out['sidecar']}")
    if out.get("stats_sidecar"):
        print(f"  stats_sidecar: {out['stats_sidecar']}")
    pub = out.get("metadata", {}).get("publication_check", {})
    if pub:
        print(f"  publication_check: passed={pub.get('passed')}  warnings={pub.get('warnings')}")
    if out.get("warnings"):
        print(f"  warnings: {out['warnings']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
