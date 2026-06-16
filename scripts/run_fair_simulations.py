"""Run FaIR v2.2 over the seven ScenarioMIP-aligned scenarios and save the
ensemble to ``data/fair-outputs/fair_run.nc`` for the plotting notebook.

Invoked automatically by ``notebooks/0505_extensions_plotting.ipynb`` if the
output file is missing. Can also be run manually:

    .venv/bin/python scripts/run_fair_simulations.py            # skip if output exists
    .venv/bin/python scripts/run_fair_simulations.py --force    # always re-run
    .venv/bin/python scripts/run_fair_simulations.py --memory-limited  # 5-member test ensemble
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import pooch
import xarray as xr
from fair import FAIR
from fair.interface import initialise
from fair.io import read_properties

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
FAIR_INPUTS = DATA_DIR / "fair-inputs"
OUT_PATH = DATA_DIR / "fair-outputs" / "fair_run.nc"

SCENARIOS = ["VL", "LN", "L", "ML", "M", "H", "HL"]

# AR6-calibrated parameter ensemble on Zenodo.
ZENODO_DOI = "10.5281/zenodo.7112539"
PARAMS_FILE = "calibrated_constrained_parameters.csv"
PARAMS_HASH = "md5:8a70a3fb05d0e0cf35e136de382582a5"


def fetch_full_ensemble() -> Path:
    """Download the full AR6 ensemble from Zenodo (cached locally)."""
    data_pooch = pooch.create(
        path=str(FAIR_INPUTS),
        base_url=f"doi:{ZENODO_DOI}",
        version="1.5.0",
        registry={PARAMS_FILE: PARAMS_HASH},
    )
    return Path(data_pooch.fetch(PARAMS_FILE))


def run(memory_limited: bool) -> xr.Dataset:
    f = FAIR()
    f.define_time(1750, 2501, 1)
    f.define_scenarios(SCENARIOS)

    species, properties = read_properties(str(FAIR_INPUTS / "species_configs_properties_1.4.1.csv"))
    f.define_species(species, properties)
    f.ch4_method = "Thornhill2021"

    if memory_limited:
        configs_path = FAIR_INPUTS / "1.5.0" / "calibrated_constrained_parameters_short.csv"
    else:
        fetch_full_ensemble()
        configs_path = FAIR_INPUTS / "1.5.0" / "calibrated_constrained_parameters.csv"

    df_configs = pd.read_csv(configs_path, index_col=0)
    f.define_configs(df_configs.index)
    f.allocate()
    print(f"Ensemble size: {len(df_configs)} configs")

    f.fill_from_csv(
        forcing_file=str(FAIR_INPUTS / "volcanic_solar.csv"),
        emissions_file=str(FAIR_INPUTS / "emissions_1750-2500.csv"),
    )
    for s in f.scenarios:
        f.forcing.loc[dict(scenario=s, specie="Solar")] = 0

    # Total GHG emissions in CO2-equivalent (AR6 GWP100, mass-adjusted).
    gwpmat = pd.read_csv(FAIR_INPUTS / "gwp_mass_adjusted_100y.csv", index_col=0)
    co2eo = f.emissions.sel(specie="CO2 FFI")[:, :, 0].copy() * 0
    for specie in f.emissions.specie.values:
        gwp = gwpmat["ar6_gwp_mass_adjusted"].get(specie, np.nan)
        if not np.isnan(gwp):
            co2eo = co2eo + f.emissions.sel(specie=specie)[:, :, 0] * gwp / 1e6
    co2e = co2eo * 1e6  # tonnes CO2e / yr

    f.fill_species_configs(str(FAIR_INPUTS / "species_configs_properties_1.4.1.csv"))
    f.override_defaults(str(configs_path))
    initialise(f.concentration, f.species_configs["baseline_concentration"])
    initialise(f.forcing, 0)
    initialise(f.temperature, 0)
    initialise(f.cumulative_emissions, 0)
    initialise(f.airborne_emissions, 0)
    initialise(f.ocean_heat_content_change, 0)

    print("Running FaIR...")
    f.run()

    return xr.Dataset(
        {
            "emissions": f.emissions.isel(config=0, drop=True),
            "co2e": co2e,
            "temperature": f.temperature.isel(layer=0, drop=True),
            "co2_concentration": f.concentration.sel(specie="CO2", drop=True),
            "forcing_sum": f.forcing_sum.rename("forcing_sum"),
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="overwrite existing output")
    parser.add_argument(
        "--memory-limited", action="store_true",
        help="use the 5-member test ensemble instead of the full AR6 set",
    )
    args = parser.parse_args()

    if OUT_PATH.exists() and not args.force:
        print(f"{OUT_PATH} already exists; pass --force to re-run.")
        return

    out = run(memory_limited=args.memory_limited)
    encoding = {v: {"dtype": "float32", "zlib": True, "complevel": 4} for v in out.data_vars}
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_netcdf(OUT_PATH, encoding=encoding)
    print(f"Saved {OUT_PATH}")


if __name__ == "__main__":
    main()
