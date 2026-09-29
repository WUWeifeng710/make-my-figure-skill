# Make My Figure — Core API Reference

> Wraps `make_my_figure_core` v1.1.1 (github.com/surPoudel/make-my-figure, MIT). This document is for scenarios that call the Python API directly (instead of the CLI wrapper scripts).

## Contents

- [Top-level imports](#top-level-imports)
- [Data loading (load_table)](#data-loading-load_table)
- [PlotSpec construction & validation](#plotspec-construction--validation)
- [Rendering & export](#rendering--export)
- [Statistics engine (run_statistics)](#statistics-engine-run_statistics)
- [Multi-panel figures (panels)](#multi-panel-figures-panels)
- [PlotSpec / StatsSpec schema](#plotspec--statsspec-schema)
- [Plot types & default mappings](#plot-types--default-mappings)

## Top-level imports

```python
from make_my_figure_core import (
    __version__,
    load_table, TableInfo,
    validate_plot_spec, SpecValidationError,
    StyleProfile, load_profile, list_profiles,
    render, render_to_files, export_bundle_bytes, figure_to_bytes,
    available_plot_types, default_mapping, display_name, make_spec,
    RenderResult,
    mock_data, presets, resource_path,
)
```

## Data loading (load_table)

```python
from make_my_figure_core import load_table

info = load_table("data.csv")      # also .tsv/.txt/.xlsx
df = info.dataframe                # pandas DataFrame
info.columns                       # column names
info.numeric_columns               # numeric columns
info.categorical_columns           # categorical columns
info.n_rows                        # row count
info.warnings                      # load warnings
info.provenance()                  # worksheet provenance (useful for multi-sheet xlsx)
```

Multi-sheet xlsx worksheets are detected and exposed through `source_*` provenance fields.

## PlotSpec construction & validation

```python
from make_my_figure_core import make_spec, default_mapping, validate_plot_spec

spec = make_spec(
    "volcano_plot",                       # plot type id
    "data.csv",                           # input table path
    "publication",                        # style profile name
    mapping=default_mapping("volcano_plot"),  # column-role mapping
    statistics={"enabled": True, "test": "welch_t", ...},  # optional
    output={"formats": ["svg","png"], "dpi": 300, "width_mm": 89},  # optional
)

validate_plot_spec(spec, known_plot_types=available_plot_types(),
                   known_styles=list_profiles())  # raises SpecValidationError on failure
```

`make_spec` fills sensible defaults; when `mapping` is omitted it uses `default_mapping(plot_type)`.

## Rendering & export

```python
from make_my_figure_core import render, render_to_files, export_bundle_bytes, figure_to_bytes

# Render to memory
result = render(spec, df)                 # df is the DataFrame from load_table
fig = result.figure                        # matplotlib Figure
result.warnings                            # non-fatal warnings
result.metadata["publication_check"]       # readiness check {passed, warnings, summary}

# Render and write files (figure + PlotSpec sidecar + StatsSpec sidecar)
out = render_to_files(spec, df, "outputs/fig", formats=["svg","png","pdf"])
out["files"]        # list of figure files
out["sidecar"]      # .plot_spec.json
out["stats_sidecar"]  # .stats_spec.json (written only when statistics ran)

# In-memory bytes / ZIP bundle
png_bytes = figure_to_bytes(fig, "png", dpi=300)
bundle = export_bundle_bytes(spec, result, formats=["svg","png","pdf"])
```

Supported export formats: `svg, png, pdf, tiff, eps`. Vector formats keep editable text (`svg.fonttype=none`, PDF `fonttype=42`).

## Statistics engine (run_statistics)

```python
from make_my_figure_core.statistics import (
    run_statistics, TESTS, recommend_tests, adjust_pvalues, apply_correction,
)
from make_my_figure_core.statistics.models import StatResult, StatsReport

report = run_statistics(df, test="welch_t", ...)   # returns StatsReport
```

**18 tests** (`TESTS` keys): `students_t, welch_t, paired_t, mann_whitney, wilcoxon, one_way_anova, two_way_anova, rm_anova, kruskal_wallis, dunn, chi_square, fishers_exact, logrank, cox_ph, pearson, spearman, linear_regression, glm`.

**Multiple-testing correction**: `adjust_pvalues(pvals, method=...)`, method is `benjamini_hochberg, holm, bonferroni`.

**Design principle**: never fabricate a p-value; every `StatResult` records the exact test name, groups, sample size, pairing, p-value, adjusted p-value, correction method, effect size and confidence interval.

## Multi-panel figures (panels)

```python
from make_my_figure_core.panels import (
    Panel, MultiPanelFigure, FigureLayout,
    build_figure, export_multipanel, multipanel_sidecar,
    import_external_panel, panel_from_dict, panel_warnings,
)

mpf = MultiPanelFigure(name="Figure 1")
mpf.layout.fig_width_mm = 174.0      # double-column width
mpf.layout.ncols = 2
mpf.layout.panel_dpi = 300

# Panel 1: rendered on demand from PlotSpec + table
p1 = Panel(label="A")
p1.plot_spec = specA
p1.table = load_table(specA["input_table"]).dataframe
mpf.add_panel(p1)

# Panel 2: supplied as an already-rendered Figure
p2 = Panel(label="B", figure=existing_fig)
mpf.add_panel(p2)

fig = build_figure(mpf)               # composite with bold vector panel labels
files = export_multipanel(fig, "outputs/figure1", ["svg","png"], dpi=300)
sidecar = multipanel_sidecar(mpf, "outputs/figure1")   # .figure_spec.json
```

Notes: a panel may use `plot_spec+table` (rendered on demand, reproducible) or an already-rendered `figure`; external images use `import_external_panel`. Composite embeds panel content as `panel_dpi` raster; labels/titles stay vector.

## PlotSpec / StatsSpec schema

### PlotSpec fields

```json
{
  "plot_type": "volcano_plot",
  "input_table": "data.csv",
  "mapping": {"x": "log2_fold_change", "p": "adjusted_p_value", ...},
  "journal_style": "publication",
  "output": {"formats": ["svg","png"], "width_mm": 89, "height_mm": 70, "dpi": 300},
  "layout": {"column_width": "single", "legend_location": "upper right", ...},
  "style": {"base_font_pt": 8, ...},
  "statistics": {...},
  "annotations": [...],
  "source": {"source_workbook_name": "...", ...}
}
```

- `layout`: uniform layout controls (tick rotation/spacing, axis-label spacing, title spacing, margins, legend location, `auto_fix_layout`).
- `style`: per-plot refinements on top of the style profile (font sizes, line widths, markers, palette).
- `annotations`: manual annotation layer (normalized axes coords 0–1).
- `source`: worksheet provenance, recorded for multi-sheet workbooks.

### StatsSpec fields (`--stats`)

```json
{
  "enabled": true,
  "test": "welch_t",
  "comparison_mode": "all_pairs",
  "correction": "none",
  "alpha": 0.05,
  "alternative": "two-sided",
  "posthoc": false,
  "posthoc_test": "welch_t",
  "value_column": null, "group_column": null, "subgroup_column": null,
  "subject_column": null, "time_column": null, "event_column": null,
  "x_column": null, "y_column": null, "row_column": null, "col_column": null,
  "reference_group": null, "selected_pairs": null,
  "annotate": true,
  "annotation": {"mode": "both", "digits": 3, "sci_threshold": 0.001,
                 "show_effect": false, "show_nonsignificant": true,
                 "font_size": null, "line_width": null,
                 "bracket_height_frac": 0.03, "gap_frac": 0.06, "top_margin_frac": 0.12}
}
```

`comparison_mode`: `all_pairs` or `vs_reference` (with `reference_group`). `annotate` controls drawing significance brackets and stars on the figure.

## Plot types & default mappings

Full list: run `python <skill>/scripts/make_figure.py --list-plots`.

Common default mappings (quick reference — **override explicitly for real data**):

| plot_type | default mapping |
|---|---|
| `barplot_with_error_bar` | x=condition, y=measurement, error=sem, color=condition |
| `boxplot_or_violin_with_points` | x=group, y=value, kind=box, points=true |
| `volcano_plot` | x=log2_fold_change, p=adjusted_p_value, label=label, lfc_cutoff=1.0, p_cutoff=0.05 |
| `scatterplot_with_regression` | x=x_marker, y=y_response, color=group, fit_line=true |
| `heatmap_clustered_matrix` | row_id=gene, cluster_rows=true, cluster_columns=true, color_scale=diverging |
| `lineplot_timecourse_with_error_band` | x=time_hours, y=signal, color=treatment, error=sem |
| `pca_scatter_from_matrix` | matrix_row_id=gene, metadata_key=sample_id, color=group, shape=batch |
| `kaplan_meier_survival_curve` | time=time_months, event=event, group=group |
| `roc_curve` | label=true_label, score=score_model_a, score2=score_model_b |
| `forest_plot` | label=subgroup, estimate=hazard_ratio, lower=ci_low, upper=ci_high, reference=1.0 |

## Limitations & notes

- Default mappings target the repository's example mock data, so **real data usually needs an explicit `--mapping`**.
- Imported differential-expression (DE) tables are plotted as given, never recomputed; use dedicated tools (DESeq2/edgeR) to model before plotting.
- Three plot types (volcano/lollipop/network) place labels with an unseeded repulsion search, so label coordinates may vary slightly between renders (data marks are unaffected).
- Single-plot exports are fully vector; multi-panel composites embed panel content as raster.
