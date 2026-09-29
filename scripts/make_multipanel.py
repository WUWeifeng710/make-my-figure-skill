#!/usr/bin/env python3
"""make_multipanel.py — Assemble individual plot specs into a labelled
multi-panel figure (Figure 1A, 1B, ...) with a reproducible sidecar.

Each panel is defined by its own PlotSpec JSON (or a Make My Figure plot type +
data file). Panels are rendered on demand, embedded in a clean grid with bold
vector labels, and exported together with a FigureSpec-style sidecar.

Usage
-----
# Two panels from two PlotSpec files
python make_multipanel.py --panel A=specA.json --panel B=specB.json \
    --name "Figure 1" --out ./figs/figure1 --formats svg,png

# Panels from plot types + data files directly
python make_multipanel.py \
    --panel A=volcano_plot:data1.csv \
    --panel B=boxplot_or_violin_with_points:data2.csv \
    --cols 2 --out ./figs/figure1
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib  # noqa: E402

matplotlib.use("Agg")


def _err(msg: str) -> None:
    print(f"[make_multipanel] ERROR: {msg}", file=sys.stderr)


def _parse_panel(spec: str) -> Dict[str, Any]:
    """Parse 'LABEL=value'. value is either a PlotSpec JSON path, a
    'plot_type:data_path' spec, or a bare data file path."""
    label, _, value = spec.partition("=")
    if not label or not value:
        _err(f"panel must be LABEL=... ({spec!r})")
        sys.exit(2)

    # A value that is an existing path is treated as a file. This covers:
    #   - a PlotSpec JSON path (handled below)
    #   - a bare data file path (rendered with the plot type's default mapping)
    #   - an absolute Windows path containing a drive-letter colon (e.g. C:\\...),
    #     which must NOT be confused with a 'plot_type:data' separator.
    if os.path.exists(value):
        if value.lower().endswith(".json"):
            with open(value, "r", encoding="utf-8") as fh:
                spec_dict = json.load(fh)
            if "plot_spec" in spec_dict and isinstance(spec_dict["plot_spec"], dict):
                spec_dict = spec_dict["plot_spec"]
            # Resolve a relative input_table against the PlotSpec's own directory.
            tbl = spec_dict.get("input_table")
            if tbl and not os.path.isabs(tbl) and not os.path.exists(tbl):
                resolved = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(value)), tbl))
                if os.path.exists(resolved):
                    spec_dict["input_table"] = resolved
            return {"label": label, "plot_spec": spec_dict}
        # Bare existing data file: infer plot type later via --recommend-style
        # profiling is out of scope here, so fall through to error with a hint.
        _err(f"'{value}' is a file but not a .json PlotSpec; provide it as "
             f"'LABEL=plot_type:{value}' to use a plot type with this data file.")
        sys.exit(2)

    # Not an existing path: interpret 'plot_type:data_path'. The FIRST colon
    # separates plot_type from the data path, so a Windows data path such as
    # 'volcano_plot:C:\\dir\\data.csv' splits correctly.
    if ":" in value:
        plot_type, _, data_path = value.partition(":")
        if not plot_type or not data_path:
            _err(f"invalid panel value: {value!r} (expected 'plot_type:data_path')")
            sys.exit(2)
        return {"label": label, "plot_type": plot_type, "table": data_path}
    _err(f"cannot interpret panel value: {value!r}")
    sys.exit(2)


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--panel", action="append", required=True, metavar="LABEL=VALUE",
                   help="LABEL=A for a PlotSpec JSON path, or LABEL=plot_type:data.csv. Repeatable.")
    p.add_argument("--name", default="Figure 1", help="Figure name (default: 'Figure 1').")
    p.add_argument("--out", required=True, help="Output base path (no extension).")
    p.add_argument("--formats", default="svg,png", help="Comma-separated export formats.")
    p.add_argument("--cols", type=int, help="Number of grid columns (auto if omitted).")
    p.add_argument("--width-mm", type=float, default=174.0, help="Figure width in mm (default 174 = double column).")
    p.add_argument("--height-mm", type=float, help="Figure height in mm (auto if omitted).")
    p.add_argument("--panel-dpi", type=int, default=300, help="Raster DPI for embedded panel content.")
    args = p.parse_args(argv)

    from make_my_figure_core import load_table, default_mapping, make_spec
    from make_my_figure_core.panels import (MultiPanelFigure, Panel,
                                            build_figure, export_multipanel,
                                            multipanel_sidecar, panel_warnings)

    mpf = MultiPanelFigure(name=args.name)
    mpf.layout.fig_width_mm = args.width_mm
    if args.height_mm:
        mpf.layout.fig_height_mm = args.height_mm
    if args.cols:
        mpf.layout.ncols = args.cols
    mpf.layout.panel_dpi = args.panel_dpi

    for raw in args.panel:
        d = _parse_panel(raw)
        panel = Panel(label=d["label"])
        if "plot_spec" in d:
            panel.plot_spec = d["plot_spec"]
            # Load the referenced table so the panel can render on demand.
            if panel.plot_spec.get("input_table"):
                panel.table = load_table(panel.plot_spec["input_table"]).dataframe
        else:
            pt, data_path = d["plot_type"], d["table"]
            spec = make_spec(pt, data_path, "publication", mapping=default_mapping(pt))
            panel.plot_spec = spec
            panel.table = load_table(data_path).dataframe
        panel.source_name = d.get("table") or panel.plot_spec.get("input_table", "")
        mpf.add_panel(panel)

    # Build, validate, export
    fig = build_figure(mpf)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    files = export_multipanel(fig, args.out, args.formats.split(","), dpi=args.panel_dpi)
    sidecar = multipanel_sidecar(mpf, args.out)
    print(f"Multi-panel figure '{args.name}' with {len(mpf.panels)} panels:")
    print(f"  files: {files}")
    print(f"  sidecar: {sidecar}")
    for w in panel_warnings(fig):
        print(f"  warning: {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
