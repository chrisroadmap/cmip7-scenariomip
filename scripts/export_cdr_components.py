"""Export CDR component breakdown to a portable CSV.

One-off helper. Depends on the upstream harmonisation repo
(emissions_harmonization_historical) and must be run from that repo's
pixi environment, e.g.:

    cd /path/to/emissions_harmonization_historical
    pixi run python /path/to/ScenarioMIP_final/scripts/export_cdr_components.py

Output: data/cdr_components_future.csv -- BECCS, DACCS, Ocean, Enhanced
Weathering pre-summed across regions to per-(model, scenario, variable)
for future years only. CDR sub-components live in the `gridding`
workflow at regional resolution; we aggregate to global totals here.

The continuous historical+future series for Gross Positive Emissions,
AFOLU, and Energy & Industrial Processes is already shipped in
data/continuous_emissions_timeseries_1750_2500.csv.
"""

from pathlib import Path

from emissions_harmonization_historical.constants_5000 import EXTENSIONS_OUTPUT_DB

CDR_SUB_VARS = [
    "Emissions|CO2|BECCS",
    "Emissions|CO2|Direct Air Capture",
    "Emissions|CO2|Ocean",
    "Emissions|CO2|Enhanced Weathering",
]

OUT_PATH = Path(__file__).parent.parent / "data" / "cdr_components_future.csv"


def main() -> None:
    df = EXTENSIONS_OUTPUT_DB.load()
    df.columns = [
        float(c) if str(c).replace(".", "").replace("-", "").replace("+", "").isdigit() else c
        for c in df.columns
    ]
    df = df.loc[df.index.get_level_values("variable").isin(CDR_SUB_VARS)]
    summed = df.groupby(level=["model", "scenario", "variable"]).sum()
    print(f"Writing {summed.shape[0]} rows x {summed.shape[1]} cols to {OUT_PATH}")
    summed.to_csv(OUT_PATH)


if __name__ == "__main__":
    main()
