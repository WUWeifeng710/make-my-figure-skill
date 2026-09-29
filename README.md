# make-my-figure

**Publication-ready scientific plotting & multi-panel figures, as an agent Skill.**

This Skill wraps the [MakeMyFigure](https://github.com/surPoudel/make-my-figure) engine
(`make_my_figure_core`) so an AI agent can turn tabular data
(CSV/TSV/TXT/Excel) into 39 journal-style plots and multi-panel composite
figures — with machine-readable JSON sidecars that make every figure
reproducible.

It runs fully **locally**: no R, no GUI, no cloud upload. All wrapper scripts
force the Matplotlib `Agg` backend, so they work headless on servers and in
script environments.

## Source

Based on the MakeMyFigure preprint:

> Poudel S, Shrestha HK, Crawford JC, Demontis F, Green DR. **MakeMyFigure: An
> Interactive Platform for Reproducible Quantitative Data Visualization,
> Analysis, and Scientific Figure Construction.** *bioRxiv* 2026.09.15.751916
> (2026).

- **DOI:** [10.64898/2026.09.15.751916](https://doi.org/10.64898/2026.09.15.751916)
- **Upstream repository:** <https://github.com/surPoudel/make-my-figure>
- **License of the engine:** MIT (see the upstream `LICENSE`)

## Features

- **39 plot types** — bar & grouped bar, box/violin, dot/strip, beeswarm,
  raincloud, histogram, ridge, Q-Q, scatter with regression, Bland-Altman,
  line/time-course, slopegraph, swimmer, spider, clustered heatmap,
  hierarchical clustering, dendrogram, PCA, volcano, MA, forest, ROC,
  precision-recall, calibration, confusion matrix, Kaplan-Meier survival,
  dose-response, Manhattan, oncoprint, lollipop, stacked composition, UpSet,
  Sankey, network, chord diagram, enrichment dot plot, waterfall, embedding
  scatter.
- **18 statistical tests** (SciPy/statsmodels, no R) — Student's/Welch's/paired
  t, Mann-Whitney U, Wilcoxon, one-/two-way/repeated-measures ANOVA,
  Kruskal-Wallis + Dunn, chi-square, Fisher's exact, log-rank, Cox PH, Pearson,
  Spearman, linear & GLM regression, with BH/Holm/Bonferroni correction and
  significance annotation on the figure.
- **Reproducibility records** — every export writes `.plot_spec.json` (how the
  figure was made) and `.stats_spec.json` (every p-value drawn); a PlotSpec can
  be reloaded with `--spec` to rebuild the exact same figure.
- **Multi-panel composites** — assemble single panels into a labelled
  Figure 1A/B/C… with a FigureSpec sidecar.
- **Data profiling & recommendations** — the engine profiles a table and
  suggests compatible plots and tests (advisory only).

## Installation (agent prompt)

Give an agent this Skill by copying the `make-my-figure` folder into your agent's
skills directory (the exact location is host-specific — consult your agent's
documentation), then instruct it with a prompt such as:

> "Use the `make-my-figure` skill to create publication-ready figures. Read
> `SKILL.md` first, install the engine from its GitHub release wheel
> (`make_my_figure_core-1.1.1-py3-none-any.whl`, see the Prerequisite section of
> `SKILL.md`), then use the wrapper scripts in `scripts/` to load data, choose a
> plot type, run statistics, and export figures plus their PlotSpec/StatsSpec
> sidecars. Deliver figures and sidecar JSON to the user and confirm
> `publication_check: passed`."

Manual install of the engine (once per machine). **The engine is not on PyPI**;
install it from the GitHub release, from the tagged source, or from a local clone:

```powershell
# A) release wheel (recommended) — download from
#    https://github.com/surPoudel/make-my-figure/releases/tag/v1.1.1
python -m pip install .\make_my_figure_core-1.1.1-py3-none-any.whl
# B) python -m pip install "git+https://github.com/surPoudel/make-my-figure.git@v1.1.1"
# C) git clone --branch v1.1.1 https://github.com/surPoudel/make-my-figure.git
#    python -m pip install .\make-my-figure
```

Dependencies: pandas, numpy, matplotlib, scipy, statsmodels, openpyxl,
jsonschema, networkx, adjustText, pillow (Python 3.10–3.12 recommended).

## Usage

```
make-my-figure/
├── SKILL.md                     # Skill instructions & workflow
├── README.md
├── scripts/
│   ├── make_figure.py           # single figure: data -> map -> stats -> plot -> export + sidecars
│   └── make_multipanel.py       # assemble panels into a labelled composite + FigureSpec sidecar
└── references/
    └── api_reference.md         # direct Python API reference
```

List plot types with default column mappings:

```powershell
python scripts/make_figure.py --list-plots
```

Single figure (volcano):

```powershell
python scripts/make_figure.py `
  --data data.csv --plot volcano_plot `
  --mapping '{"x":"log2_fold_change","p":"adjusted_p_value","label":"label","p_cutoff":0.05,"lfc_cutoff":1.0}' `
  --out ./figs/volcano --formats svg,png,pdf
```

Single figure with statistics (Welch t-test). On Windows/PowerShell, prefer
JSON files to avoid inline quoting issues:

```powershell
python scripts/make_figure.py `
  --data data.csv --plot boxplot_or_violin_with_points `
  --mapping-file mapping.json --stats-file stats.json `
  --out ./figs/box --formats svg,png
```

Multi-panel composite (Figure 1A/B):

```powershell
python scripts/make_multipanel.py `
  --panel "A=specA.json" --panel "B=specB.json" `
  --name "Figure 1" --cols 2 --out ./figs/figure1 --formats svg,png
```

Run `python scripts/make_figure.py --help` for the full argument reference, or
read `SKILL.md` for the complete workflow.

## Cite

If figures produced with this Skill contribute to published work, please cite
the preprint above and name the engine version you used.

## License

This Skill is a thin wrapper/authoring layer around the upstream
MakeMyFigure engine (MIT). It contains no code from the upstream repository
except usage of its published Python API; upstream license applies to the
engine itself. See the upstream repository for full terms.
