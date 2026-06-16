# Data Directory

This directory contains input CSV files for the ScenarioMIP description paper figure repository.

All data files are version-controlled directly in this repository (no Git LFS). The full dataset, including regional files not used here, is archived on Zenodo.

## Files

| File | Size | Description |
|---|---|---|
| `history.csv` | 192 KB | Historical global emissions, with inventory provenance preserved in the `model` column (e.g. `GCB-extended`, `WMO 2022 AGAGE inversions_cmip-inverse-extended`) |
| `continuous_emissions_timeseries_1750_2500.csv` | 5.1 MB | Continuous emissions timeseries 1750-2500, history replicated per IAM scenario |
| `cdr_components_future.csv` | ~150 KB | Future-only CDR sub-component series (BECCS, DACCS, ocean, enhanced weathering), pre-summed to global per (model, scenario, variable). Regenerate via `scripts/export_cdr_components.py`. |
| `fair-inputs/emissions_1750-2500.csv` | 4.1 MB | FaIR model emissions input |
| `fair-inputs/species_configs_properties_1.4.1.csv` | 12 KB | FaIR species configuration |
| `fair-inputs/gwp_mass_adjusted_100y.csv` | 4 KB | GWP mass-adjusted 100-year values |
| `fair-inputs/volcanic_solar.csv` | 128 KB | Volcanic and solar forcing data |
| `fair-inputs/1.5.0/calibrated_constrained_parameters.csv` | 2.1 MB | FaIR calibrated ensemble parameters (also fetched from Zenodo at runtime) |
| `fair-inputs/1.5.0/calibrated_constrained_parameters_short.csv` | 8 KB | Reduced parameter set for testing |

Regional files (`history_regional.csv`, `scenarios_regional.csv`) are not included in this repository.
