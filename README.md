# ScenarioMIP Extension: FaIR Climate Simulations

This repository reproduces plots for the published ScenarioMIP CMIP7 description paper:

Van Vuuren, D. P., O'Neill, B. C., Tebaldi, C., Sanderson, B. M., Chini, L. P., Friedlingstein, P., Hasegawa, T., Riahi, K., Govindasamy, B., Bauer, N., Eyring, V., Fall, C. M. N., Frieler, K., Gidden, M. J., Gohar, L. K., Högner, A., Jones, A. D., Kikstra, J., King, A., Knutti, R., Kriegler, E., Lawrence, P., Lennard, C., Lowe, J., Mathison, C., Mehmood, S., Nicholls, Z., Prado, L. F., Zhang, Q., Rose, S. K., Ruane, A. C., Sandstad, M., Schleussner, C.-F., Seferian, R., Sillmann, J., Smith, C., Sörensson, A. A., Panickal, S., Tachiiri, K., Vaughan, N., Vishwanathan, S. S., Yokohata, T., Zecchetto, M., and Ziehn, T.: The Scenario Model Intercomparison Project for CMIP7 (ScenarioMIP-CMIP7), Geosci. Model Dev., 19, 2627–2656, https://doi.org/10.5194/gmd-19-2627-2026, 2026.

The repo runs the [FaIR v2.2](https://github.com/OMS-NetZero/FAIR) climate model over 1750–2501 across seven ScenarioMIP-aligned scenarios (VL through HL) and renders every figure in the paper. Choose one of two paths: a single command via the script (no Jupyter required), or interactive cells in a notebook.

## Requirements

- Python 3.10+

## Setup

```bash
git clone https://github.com/benmsanderson/scenariomip-paper-plots.git
cd scenariomip-paper-plots
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Quickstart: render every figure (without Jupyter)

```bash
.venv/bin/python scripts/make_plots.py
```

This runs the FaIR simulation if it hasn't been run yet (a few minutes on
the full AR6 ensemble; ~26 MB NetCDF cached at `data/fair-outputs/`),
then writes all eight figure files to `plots/`. Use `--out-dir` to write
elsewhere:

```bash
.venv/bin/python scripts/make_plots.py --out-dir /tmp/plots
```

To force the FaIR simulation to re-run, or to use the 5-member test
ensemble for quick iteration:

```bash
.venv/bin/python scripts/run_fair_simulations.py --force
.venv/bin/python scripts/run_fair_simulations.py --memory-limited
```

## Interactive use (notebook)

For inspecting intermediates or tweaking figure styling cell-by-cell:

```bash
python -m ipykernel install --user --name scenariomip --display-name "ScenarioMIP"
jupyter lab
```

Then open [notebooks/0505_extensions_plotting.ipynb](notebooks/0505_extensions_plotting.ipynb).
The notebook imports the same figure functions as the script — edits to
`scripts/plotting.py` are picked up by both paths (use `importlib.reload(plotting)`
in the notebook).

## File layout

| File | Description |
|---|---|
| [scripts/run_fair_simulations.py](scripts/run_fair_simulations.py) | Runs FaIR and saves the ensemble (emissions, CO₂e, temperature, CO₂ concentration, forcing) to `data/fair-outputs/fair_run.nc`. The AR6 calibration is fetched from Zenodo on first run. |
| [scripts/plotting.py](scripts/plotting.py) | Single source of truth for figure code: `load_data()`, six `fig_*` functions, and `make_all_plots()`. Imported by both the CLI and the notebook. |
| [scripts/make_plots.py](scripts/make_plots.py) | Headless CLI that renders every figure to `plots/`. |
| [scripts/build_plotting_notebook.py](scripts/build_plotting_notebook.py) | Regenerates `notebooks/0505_extensions_plotting.ipynb` from cell source strings; only owns notebook-cell layout. Edit `plotting.py` for figure-content changes. |
| [notebooks/0505_extensions_plotting.ipynb](notebooks/0505_extensions_plotting.ipynb) | Interactive front-end for `plotting.py`. |

## Data

See [data/README.md](data/README.md) for a description of the input files. All data files are version-controlled directly in this repository. FaIR calibration parameters are also fetched from Zenodo at runtime. The full dataset (including regional files) is archived on Zenodo.

## Scenarios

Seven scenarios are included, spanning a wide range of future emissions pathways:

| ID | Description |
|---|---|
| VL | Very low emissions |
| LN | Low-negative emissions |
| L | Low emissions |
| ML | Medium-low emissions |
| M | Medium emissions |
| H | High emissions |
| HL | High-legacy / very high emissions |
