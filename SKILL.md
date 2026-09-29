---
name: make-my-figure
description: Wrapper skill for generating publication-ready scientific plots and multi-panel figures. Based on the MakeMyFigure engine (make_my_figure_core, MIT license, DOI:10.64898/2026.09.15.751916), it turns CSV/TSV/TXT/Excel tables into 39 journal-style charts (bar, box/violin, volcano, heatmap, PCA, Kaplan-Meier survival, ROC, forest, UMAP, etc.) and writes PlotSpec/StatsSpec JSON reproducibility sidecars. For computational biology, bioinformatics, omics and experimental science figure making. Use when the user wants "turn a data table into a paper-grade figure", "multi-panel composite figure", "reproducible scientific plotting", or "a figure with statistical tests (t-test, ANOVA, rank tests, etc.)". 中文触发示例：把数据表画成发表级图表、火山图/箱线图/生存曲线并标注显著性、多面板 Figure 拼图、可复现作图记录。
---

# Make My Figure (publication-ready scientific plotting)

Turn tabular data (CSV/TSV/TXT/Excel) into paper-grade figures and **automatically record reproducible JSON specs**. Runs fully locally, no R, no GUI; driven headless through the `make_my_figure_core` engine.

## When to use / when not to use

- **Use**: to turn a data table into a publication-grade single figure or a multi-panel composite; to draw statistical-test significance onto a plot; to get a reproducible PlotSpec sidecar; omics / bioinformatics / experimental figures.
- **Do not use**: when raw RNA-seq differential-expression modeling is required (DESeq2/edgeR/limma remain dedicated tools; this engine only plots their precomputed results); fully custom non-standard layouts.
- **Statistics stance**: 18 built-in tests are implemented with SciPy/statsmodels, no R. Statistics were cross-validated against R implementations (2,625 comparisons, no failures), but **imported differential-expression tables are never recomputed** — they are plotted as given.

## Prerequisite: install the engine

The engine is distributed on GitHub Releases — **it is NOT on PyPI**, so
`pip install make_my_figure_core` fails with "No matching distribution found".
That error is expected; it does not mean the network is broken. Install once per
machine, in this order of preference:

```powershell
# Option A (recommended): release wheel, pinned to v1.1.1
#   Download make_my_figure_core-1.1.1-py3-none-any.whl from
#   https://github.com/surPoudel/make-my-figure/releases/tag/v1.1.1
#   (SHA-256: e9caff5b18cef9298695883beb18cd964255c750a3b44ce3f14025eb01009722)
python -m pip install .\make_my_figure_core-1.1.1-py3-none-any.whl

# Option B: straight from the tagged source
python -m pip install "git+https://github.com/surPoudel/make-my-figure.git@v1.1.1"

# Option C: clone, then install locally (works behind proxies that reset git+https)
git clone --branch v1.1.1 --depth 1 https://github.com/surPoudel/make-my-figure.git
python -m pip install .\make-my-figure
```

Dependencies: pandas, numpy, matplotlib, scipy, statsmodels, openpyxl, jsonschema, networkx, adjustText, pillow (Python 3.10–3.12 recommended).

**Self-check after install (required, report the actual output):**

```powershell
python -c "import make_my_figure_core as m; print(m.__version__)"   # expect >= 1.1.1
```

If the import fails, stop and report the full error text verbatim — do not retry
silently. If the version is older than 1.1.1, treat the capability lists in this
skill as a guide and trust the live `--list-plots` output over the documentation.

> **Headless**: all wrapper scripts force the matplotlib `Agg` backend, so no display/GUI is needed — they run fine on servers and script environments.

## Quick start (two commands)

The skill ships two scripts under `scripts/`. First list supported plot types with their default column mappings:

```powershell
python <skill_dir>/scripts/make_figure.py --list-plots
```

**Single figure** (volcano example):

```powershell
python <skill_dir>/scripts/make_figure.py `
  --data data.csv --plot volcano_plot `
  --mapping '{"x":"log2_fold_change","p":"adjusted_p_value","label":"label","p_cutoff":0.05,"lfc_cutoff":1.0}' `
  --out ./figs/volcano --formats svg,png,pdf
```

**Single figure with a statistical test** (Welch t-test + significance annotation). Inline JSON quoting is error-prone on Windows/PowerShell, so **prefer writing mapping/stats to JSON files**:

```powershell
# mapping.json: {"x":"group","y":"response","kind":"box"}
# stats.json:   {"enabled":true,"test":"welch_t","correction":"none","alpha":0.05,"annotate":true}
python <skill_dir>/scripts/make_figure.py `
  --data data.csv --plot boxplot_or_violin_with_points `
  --mapping-file mapping.json --stats-file stats.json `
  --out ./figs/box --formats svg,png
```

(On bash/macOS/Linux you can also pass inline `--mapping '{"x":"group","y":"response"}'` `--stats '{"enabled":true,"test":"welch_t"}'`; prefer files on Windows/PowerShell.)

**Multi-panel composite** (Figure 1A/B, assembled from two PlotSpecs):

```powershell
python <skill_dir>/scripts/make_multipanel.py `
  --panel "A=specA.json" --panel "B=specB.json" `
  --name "Figure 1" --cols 2 --out ./figs/figure1 --formats svg,png
```

(Panel content is embedded as raster at `--panel-dpi`; labels/titles stay vector. The run writes `figure1.svg`/`figure1.png` **plus the composite reproducibility record `figure1.figure_spec.json`** — deliver that sidecar too.)

## Recommended workflow (for the agent)

Process a user's plotting request in this order:

1. **Probe the data**: run `--recommend` to get engine suggestions (advisory; the user makes the final choice):
   `python make_figure.py --data data.csv --recommend` → prints column types and recommended plots.
2. **Choose a plot type**: pick one that matches the data from `--list-plots`; real data usually needs an **explicit `--mapping`** (defaults target example mock data whose column names may not match your table).
3. **Choose statistics**: provide `--stats` when significance annotation is needed (see "Statistical tests"); use `--recommend` if unsure which test.
4. **Render & export**: default `svg,png` (vector keeps editable text); set `--width-mm` to journal column width (single 89, double 174).
5. **Deliver**: hand the exported figure to the user, **and deliver the PlotSpec/StatsSpec sidecar JSON** (the reproducibility record).
6. **Verify**: check `publication_check: passed=True`; explain any warnings to the user.

## Plot types at a glance (39)

| Category | plot_type ids (the list command prints all) |
|---|---|
| Comparisons | `barplot_with_error_bar` `grouped_barplot_with_error_bar` `boxplot_or_violin_with_points` `dot_strip_plot` `beeswarm_plot` `raincloud_plot` |
| Distributions | `histogram_distribution` `ridge_or_density_plot` `qq_plot` |
| Relationships | `scatterplot_with_regression` `bland_altman_plot` |
| Time / trajectory | `lineplot_timecourse_with_error_band` `paired_slopegraph` `swimmer_plot` `spider_plot` |
| Matrix / omics | `heatmap_clustered_matrix` `hierarchical_clustering` `hierarchical_dendrogram` `pca_scatter_from_matrix` `volcano_plot` `ma_plot` |
| Statistical / model | `forest_plot` `roc_curve` `precision_recall_curve` `calibration_plot` `confusion_matrix` `kaplan_meier_survival_curve` `dose_response_curve` |
| Genomics summaries | `manhattan_plot` `oncoprint_mutation_heatmap` `lollipop_mutation_plot` |
| Composition / set / flow / network | `stacked_bar_composition` `upset_plot` `sankey_plot` `network_graph` `chord_diagram` |
| Other | `enrichment_dotplot` `waterfall_plot` `embedding_scatter` |

## Statistical tests (18)

`test` values for `--stats`: `students_t` `welch_t` `paired_t` `mann_whitney` `wilcoxon` `one_way_anova` `two_way_anova` `rm_anova` `kruskal_wallis` `dunn` `chi_square` `fishers_exact` `logrank` `cox_ph` `pearson` `spearman` `linear_regression` `glm`.

Multiple-testing correction: `correction` = `benjamini_hochberg` | `holm` | `bonferroni` | `none`. Full field structure in `references/api_reference.md`.

## Common CLI arguments

| Argument | Description |
|---|---|
| `--data PATH` | Input table (csv/tsv/txt/xlsx; multi-sheet xlsx auto-detected) |
| `--plot TYPE` | Plot type id (see `--list-plots`) |
| `--mapping JSON` | Column-role mapping; nearly always required for real data (use `--mapping-file PATH` on Windows) |
| `--stats JSON` | Statistics config (`enabled,test,correction,alpha,annotate,...`; use `--stats-file PATH` on Windows) |
| `--spec PATH` | Existing PlotSpec JSON to rebuild the exact same figure |
| `--style NAME` | Style profile name, default `publication` |
| `--out BASE` | Output base path (no extension); writes figure files + `.plot_spec.json` + `.stats_spec.json` |
| `--formats` | `svg,png,pdf,tiff,eps`, default `svg,png` |
| `--dpi` | Raster DPI, default 300 |
| `--width-mm/--height-mm` | Figure size in mm; single 89, double 174 |
| `--recommend` | Print the engine's plot and statistics suggestions for a table |

## Programmatic API (advanced)

Use the package directly: `from make_my_figure_core import load_table, available_plot_types, default_mapping, make_spec, render, render_to_files`. Multi-panel via `make_my_figure_core.panels` (`Panel, MultiPanelFigure, FigureLayout, build_figure, export_multipanel, multipanel_sidecar`). Statistics via `make_my_figure_core.statistics.run_statistics`. Full signatures in `references/api_reference.md`.

## Reproducibility and delivery

- Every export writes `.plot_spec.json` (how the figure was made) and `.stats_spec.json` (every p-value drawn on the figure); multi-panel runs add `.figure_spec.json`.
- Reload a PlotSpec with `--spec` to rebuild the exact figure.
- Cite: Poudel S, et al. *bioRxiv* 2026.09.15.751916 (2026). Note the engine version on the figure.

## Troubleshooting

- `pip install make_my_figure_core` → "No matching distribution found": **expected**, the engine is not published on PyPI. Use wheel / git+https / local clone as in "Prerequisite" above.
- `git: Connection was reset` / `schannel` errors to github.com: download the release wheel with a browser (Option A) or install from a local clone (Option C).
- Windows app-control (WDAC/Smart App Control) blocking `statsmodels` or new pandas wheels: create the environment with pinned `pandas==2.2.3` and `numpy<2`, or use a Python 3.10–3.12 environment where those wheels are allowed.
- `findfont: Helvetica/Arial not found` warnings during rendering: cosmetic; Matplotlib falls back to DejaVu Sans and the figure stays valid.
- `Glyph ... missing from font(s)` warnings: your data labels contain CJK/non-Latin characters the publication font stack cannot draw (they render as boxes). Prefer ASCII column/row labels for figures, or map them to English names before plotting.
- After an engine upgrade, if a documented plot type or flag is missing: trust `python <skill_dir>/scripts/make_figure.py --list-plots` output over this document, and check `__version__` against the v1.1.1 baseline this skill was written for.
