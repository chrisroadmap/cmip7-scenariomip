"""Reusable plotting code for the ScenarioMIP description paper.

Imported by:
- ``notebooks/0505_extensions_plotting.ipynb`` (interactive use)
- ``scripts/make_plots.py`` (headless CLI -- no Jupyter required)

Each ``fig_*`` function returns a Matplotlib Figure; callers decide whether
to save, display, or close it. ``make_all_plots`` runs the whole set.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
PLOTS_DIR = REPO_ROOT / "plots"
FAIR_OUTPUT_PATH = DATA_DIR / "fair-outputs" / "fair_run.nc"
SIM_SCRIPT = REPO_ROOT / "scripts" / "run_fair_simulations.py"

# ---------------------------------------------------------------------------
# Constants and scenario metadata
# ---------------------------------------------------------------------------

BASELINE_YEAR = 2100
CDR_LIMIT = -1460                        # Gt CO2 cumulative ceiling
PROVED_FOSSIL_RESERVES = 2032 + 2400     # Gt CO2
PROBABLE_FOSSIL_RESERVES = 8036 + 2400   # Gt CO2

# Long IAM-scenario names in the raw_output CSV mapped to short codes.
scenario_model_match = {
    "VL": ["SSP1 - Very Low Emissions", "REMIND-MAgPIE 3.5-4.11", "tab:blue"],
    "LN": ["SSP2 - Low Overshoot_a", "AIM 3.0", "tab:cyan"],
    "L":  ["SSP2 - Low Emissions", "MESSAGEix-GLOBIOM-GAINS 2.1-M-R12", "tab:green"],
    "ML": ["SSP2 - Medium-Low Emissions", "COFFEE 1.6", "tab:pink"],
    "M":  ["SSP2 - Medium Emissions", "IMAGE 3.4", "tab:purple"],
    "H":  ["SSP3 - High Emissions", "GCAM 8s", "tab:red"],
    "HL": ["SSP5 - Medium-Low Emissions_a", "WITCH 6.0", "tab:brown"],
}
scenario_to_code = {info[0]: code for code, info in scenario_model_match.items()}

# Component colors (CO2-flux figure).
COLORS = {
    "Gross_Positive":      "#8B4513",
    "BECCS":               "#BEDB3C",
    "DACCS":               "#DF23D9",
    "Ocean":               "#4D3EBD",
    "Enhanced_Weathering": "#A6A6A6",
    "AFOLU":               "#51E390",
}

# Per-scenario line colors (FaIR-output figures).
SNAMES = ["VL", "LN", "L", "ML", "M", "H", "HL"]
scenario_colors = {
    "HL": "#E744F6",
    "H":  "#a41212",
    "M":  "#fc7b03",
    "ML": "#dec820",
    "L":  "#20A359",
    "LN": "#22e5db",
    "VL": "#16188F",
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data(run_fair_if_missing: bool = True) -> tuple[pd.DataFrame, pd.DataFrame, xr.Dataset]:
    """Load raw emissions CSVs and the FaIR ensemble NetCDF.

    If ``fair_run.nc`` is missing and ``run_fair_if_missing`` is True, the
    FaIR simulation script is invoked first (takes a few minutes).
    """
    raw_output = pd.read_csv(DATA_DIR / "continuous_emissions_timeseries_1750_2500.csv")
    raw_output = raw_output.set_index(["model", "scenario", "region", "workflow", "variable", "unit"])
    raw_output.columns = raw_output.columns.astype(float)

    cdr_components = pd.read_csv(DATA_DIR / "cdr_components_future.csv")
    cdr_components = cdr_components.set_index(["model", "scenario", "variable"])
    cdr_components.columns = cdr_components.columns.astype(float)

    if not FAIR_OUTPUT_PATH.exists():
        if not run_fair_if_missing:
            raise FileNotFoundError(f"{FAIR_OUTPUT_PATH} missing; run {SIM_SCRIPT} first.")
        print(f"{FAIR_OUTPUT_PATH} not found -- running FaIR simulation (a few minutes)...")
        subprocess.run([sys.executable, str(SIM_SCRIPT)], check=True)
    fair = xr.open_dataset(FAIR_OUTPUT_PATH)

    return raw_output, cdr_components, fair


# ---------------------------------------------------------------------------
# CO2-flux figure helpers
# ---------------------------------------------------------------------------

def _series_by_scenario_variable(df: pd.DataFrame, scenario: str, variable: str, years) -> np.ndarray:
    mask = (
        (df.index.get_level_values("scenario") == scenario)
        & (df.index.get_level_values("variable") == variable)
    )
    sub = df.loc[mask, years]
    if sub.empty:
        return np.zeros(len(years))
    return sub.sum(axis=0).values


def _cdr_future_padded(cdr_components, scenario, variable, all_years, future_years):
    mask = (
        (cdr_components.index.get_level_values("scenario") == scenario)
        & (cdr_components.index.get_level_values("variable") == variable)
    )
    vals = cdr_components.loc[mask, future_years].sum(axis=0).values
    return np.concatenate([np.zeros(len(all_years) - len(future_years)), vals])


def _get_scenario_data(raw_output, cdr_components, scenario, all_years, future_years):
    return {
        "gross_pos": _series_by_scenario_variable(raw_output, scenario, "Emissions|CO2|Gross Positive Emissions", all_years) / 1000,
        "fossil":    _series_by_scenario_variable(raw_output, scenario, "Emissions|CO2|Energy and Industrial Processes", all_years) / 1000,
        "afolu":     _series_by_scenario_variable(raw_output, scenario, "Emissions|CO2|AFOLU", all_years) / 1000,
        "beccs":     _cdr_future_padded(cdr_components, scenario, "Emissions|CO2|BECCS",               all_years, future_years) / 1000,
        "daccs":     _cdr_future_padded(cdr_components, scenario, "Emissions|CO2|Direct Air Capture",  all_years, future_years) / 1000,
        "ocean":     _cdr_future_padded(cdr_components, scenario, "Emissions|CO2|Ocean",               all_years, future_years) / 1000,
        "ew":        _cdr_future_padded(cdr_components, scenario, "Emissions|CO2|Enhanced Weathering", all_years, future_years) / 1000,
    }


def _plot_annual(ax, data, years):
    afolu_pos = np.clip(data["afolu"], 0, None)
    afolu_neg = np.clip(data["afolu"], None, 0)

    y1_pos = data["gross_pos"]
    y2_pos = y1_pos + afolu_pos
    y1_neg = data["beccs"]
    y2_neg = y1_neg + data["daccs"]
    y3_neg = y2_neg + data["ocean"]
    y4_neg = y3_neg + data["ew"]
    y5_neg = y4_neg + afolu_neg

    ax.fill_between(years, 0,       y1_pos, alpha=0.7, color=COLORS["Gross_Positive"],      label="Gross FF&I")
    ax.fill_between(years, y1_pos,  y2_pos, alpha=0.7, color=COLORS["AFOLU"],               label="AFOLU")
    ax.fill_between(years, 0,       y1_neg, alpha=0.7, color=COLORS["BECCS"],               label="BECCS")
    ax.fill_between(years, y1_neg,  y2_neg, alpha=0.7, color=COLORS["DACCS"],               label="DACCS")
    ax.fill_between(years, y2_neg,  y3_neg, alpha=0.7, color=COLORS["Ocean"],               label="Ocean CDR")
    ax.fill_between(years, y3_neg,  y4_neg, alpha=0.7, color=COLORS["Enhanced_Weathering"], label="Enhanced Weathering")
    ax.fill_between(years, y4_neg,  y5_neg, alpha=0.7, color=COLORS["AFOLU"])

    ax.plot(years, data["fossil"] + data["afolu"], "k-", linewidth=2, alpha=0.8, label="Net Emissions")


def _plot_cumulative(ax, data, years):
    afolu_pos = np.clip(data["afolu"], 0, None)
    afolu_neg = np.clip(data["afolu"], None, 0)

    gp_cum    = np.cumsum(data["gross_pos"])
    afolu_cum = np.cumsum(afolu_pos + afolu_neg)
    beccs_cum = np.cumsum(data["beccs"])
    daccs_cum = np.cumsum(data["daccs"])
    ocean_cum = np.cumsum(data["ocean"])
    ew_cum    = np.cumsum(data["ew"])

    y1_pos = gp_cum
    y2_pos = y1_pos + afolu_cum
    y1_neg = beccs_cum
    y2_neg = y1_neg + daccs_cum
    y3_neg = y2_neg + ocean_cum
    y4_neg = y3_neg + ew_cum

    ax.fill_between(years, 0,      y1_pos, alpha=0.7, color=COLORS["Gross_Positive"])
    ax.fill_between(years, y1_pos, y2_pos, alpha=0.7, color=COLORS["AFOLU"])
    ax.fill_between(years, 0,      y1_neg, alpha=0.7, color=COLORS["BECCS"])
    ax.fill_between(years, y1_neg, y2_neg, alpha=0.7, color=COLORS["DACCS"])
    ax.fill_between(years, y2_neg, y3_neg, alpha=0.7, color=COLORS["Ocean"])
    ax.fill_between(years, y3_neg, y4_neg, alpha=0.7, color=COLORS["Enhanced_Weathering"])

    fossil_cum = np.cumsum(data["fossil"])
    ax.plot(years, fossil_cum + afolu_cum, "k-", linewidth=2, alpha=0.8, label="Net Emissions")


def _format_axes(ax_annual, ax_cumul, scenario, row_index, all_years):
    for ax, suffix in [(ax_annual, "Annual Gross Fluxes"), (ax_cumul, "Cumulative Gross Fluxes")]:
        ax.set_title(f"{scenario_to_code[scenario]} {suffix}", fontsize=12, fontweight="bold")
        ax.set_xlabel("Year", fontsize=11)
        ax.set_ylabel(
            "CO₂ Flux (Gt CO₂/yr)" if ax is ax_annual else "Cumulative CO₂ (Gt CO₂)",
            fontsize=11,
        )
        ax.tick_params(axis="both", which="major", labelsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(all_years[0], all_years[-1])
        ax.axvline(x=BASELINE_YEAR, color="red", linestyle="--", alpha=0.5, linewidth=1)
        ax.axhline(y=0, color="black", linestyle="-", alpha=0.3, linewidth=2)

        if ax is ax_cumul:
            ax.axhline(y=CDR_LIMIT,                color="green", linestyle="-",  alpha=0.3, linewidth=3, label="Cumulative CDR limit")
            ax.axhline(y=PROVED_FOSSIL_RESERVES,   color="red",   linestyle="-",  alpha=0.3, linewidth=3, label="Proved Fossil Reserves")
            ax.axhline(y=PROBABLE_FOSSIL_RESERVES, color="red",   linestyle="--", alpha=0.3, linewidth=3, label="Proved + Probable Fossil Reserves")
        if row_index == 0:
            ax.legend(loc="upper right", fontsize=9)


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def fig_co2_extensions(raw_output, cdr_components) -> plt.Figure:
    """CO₂ flux extensions: annual + cumulative panels per scenario, with CDR breakdown."""
    all_years = sorted(c for c in raw_output.columns if isinstance(c, (int, float)))
    future_years = sorted(c for c in cdr_components.columns if isinstance(c, (int, float)))

    scenarios = sorted(
        set(raw_output.index.get_level_values("scenario"))
        & set(cdr_components.index.get_level_values("scenario"))
    )
    n = len(scenarios)

    fig, axes = plt.subplots(n, 2, figsize=(10, 3 * n))
    if n == 1:
        axes = axes.reshape(1, -1)

    years_arr = np.array(all_years)
    for i, scenario in enumerate(scenarios):
        data = _get_scenario_data(raw_output, cdr_components, scenario, all_years, future_years)
        _plot_annual(axes[i, 0], data, years_arr)
        _plot_cumulative(axes[i, 1], data, years_arr)
        _format_axes(axes[i, 0], axes[i, 1], scenario, i, all_years)

    plt.tight_layout()
    return fig


def _fair_views(fair: xr.Dataset):
    """Common slices/anomalies used by the FaIR-output figures."""
    temperature = fair["temperature"]
    T_BASELINE = temperature.sel(timebounds=np.arange(1850, 1902)).mean(dim="timebounds")
    return {
        "timepoints":         fair["emissions"].timepoints.values,
        "timebounds":         temperature.timebounds.values,
        "scenarios":          temperature.scenario.values,
        "emissions":          fair["emissions"],
        "co2e":               fair["co2e"],
        "temperature":        temperature,
        "temperature_anom":   temperature - T_BASELINE,
        "co2_concentration":  fair["co2_concentration"],
        "forcing_sum":        fair["forcing_sum"],
    }


def fig_co2_emissions(fair: xr.Dataset) -> plt.Figure:
    """Annual + cumulative CO₂ emissions across all scenarios (1750-2500)."""
    v = _fair_views(fair)
    fig, ax = plt.subplots(1, 2, figsize=(14, 5))
    for scenario in v["scenarios"]:
        co2 = v["emissions"].sel(scenario=scenario, specie="CO2 FFI") + v["emissions"].sel(scenario=scenario, specie="CO2 AFOLU")
        ax[0].plot(v["timepoints"], co2, label=scenario, color=scenario_colors[scenario])
        ax[1].plot(v["timepoints"], co2.cumsum(), label=scenario, color=scenario_colors[scenario])
    ax[0].set_ylabel("CO$_2$ emissions, GtCO$_2$ yr$^{-1}$")
    ax[1].set_ylabel("Cumulative CO$_2$ emissions, GtCO$_2$")
    for a in ax:
        a.axhline(ls=":", color="k", lw=0.5)
        a.legend()
        a.grid()
    return fig


def fig_ghg_emissions(fair: xr.Dataset) -> plt.Figure:
    """CO₂ vs total GHG (CO₂e) emissions, 2015-2300 zoom."""
    v = _fair_views(fair)
    fig, ax = plt.subplots(1, 2, figsize=(14, 5))
    for scenario in v["scenarios"]:
        co2 = v["emissions"].sel(scenario=scenario, specie="CO2 FFI") + v["emissions"].sel(scenario=scenario, specie="CO2 AFOLU")
        ax[0].plot(v["timepoints"], co2, label=scenario, color=scenario_colors[scenario])
        ax[1].plot(v["timepoints"], v["co2e"].sel(scenario=scenario) / 1e6, label=scenario, color=scenario_colors[scenario])
    ax[0].set_ylabel("CO$_2$ emissions, GtCO$_2$ yr$^{-1}$")
    ax[0].set_xlim(2015, 2300); ax[0].set_ylim(-40, 100); ax[0].legend()
    ax[1].set_ylabel("GHG emissions, GtCO$_2$eq yr$^{-1}$")
    ax[1].set_xlim(2015, 2300); ax[1].set_ylim(-50, 100)
    for a in ax:
        a.axhline(ls=":", color="k", lw=0.5)
        a.grid()
    return fig


def fig_temperature_emis(fair: xr.Dataset) -> plt.Figure:
    """GHG emissions with uncertainty band + temperature 2000-2150 (33-66 pct)."""
    v = _fair_views(fair)
    scenarios = v["scenarios"]
    timepoints, timebounds = v["timepoints"], v["timebounds"]
    co2e = v["co2e"]

    fig, ax = plt.subplots(1, 2, figsize=(12, 5))
    unc = np.tanh((co2e.sel(scenario=scenarios[0]) - co2e.sel(scenario=scenarios[-2])) / 1e6 / 10) * 8

    for scenario in scenarios:
        ax[0].fill_between(
            timebounds[:351],
            co2e.sel(scenario=scenario)[:351] / 1e6 - unc[:351],
            co2e.sel(scenario=scenario)[:351] / 1e6 + unc[:351],
            color=scenario_colors[scenario], lw=0, alpha=0.3,
        )
        ax[0].fill_between(
            timepoints[350:],
            co2e.sel(scenario=scenario)[350:] / 1e6 - unc[350:],
            co2e.sel(scenario=scenario)[350:] / 1e6 + unc[350:],
            color=scenario_colors[scenario], hatch="XXX", lw=0, alpha=0.1,
        )
        ax[0].plot(timepoints[:275], co2e.sel(scenario=scenario)[:275] / 1e6, color="k")

    ax[0].text(2030, -39, "IAM generated \nscenarios \n(2025-2100)")
    ax[0].text(2105, -39, "Priority extension\nperiod \n(2101-2150)")
    ax[0].set_ylabel("GHG emissions, GtCO$_2$eq yr$^{-1}$")
    ax[0].axhline(ls=":", color="k", lw=0.5)
    ax[0].set_xlim(2000, 2150); ax[0].set_ylim(-50, 100)
    ax[0].grid(); ax[0].set_title("(a)")

    for scenario in scenarios:
        ta = v["temperature_anom"].sel(scenario=scenario)
        ax[1].fill_between(
            timebounds,
            ta.quantile(0.33, dim="config"),
            ta.quantile(0.66, dim="config"),
            color=scenario_colors[scenario], lw=0, alpha=0.3, label=scenario,
        )
    hist = v["temperature_anom"].sel(scenario=scenarios[-1])
    ax[1].fill_between(
        timebounds[:274],
        hist[:274].quantile(0.33, dim="config"),
        hist[:274].quantile(0.66, dim="config"),
        color="k", alpha=0.5,
    )
    ax[1].axhline(0, ls=":", color="k", lw=0.5)
    ax[1].set_ylabel("Temperature above 1850-1900, K")
    ax[1].set_ylim(0, 5); ax[1].set_xlim(2000, 2150)
    ax[1].grid(); ax[1].legend(); ax[1].set_title("(b)")
    return fig


def fig_extensions(fair: xr.Dataset) -> plt.Figure:
    """8-panel diagnostic plot: emissions, forcing, concentration, temperature."""
    v = _fair_views(fair)
    scenarios = v["scenarios"]
    timepoints, timebounds = v["timepoints"], v["timebounds"]
    emissions = v["emissions"]
    co2e = v["co2e"]
    forcing_sum = v["forcing_sum"]
    co2_concentration = v["co2_concentration"]
    temperature_anom = v["temperature_anom"]

    fig, ax = plt.subplots(nrows=4, ncols=2, figsize=(14, 16))
    ax = ax.flatten()
    hist = slice(0, 273)

    # Annual CO2
    for scenario in scenarios:
        co2 = emissions.sel(scenario=scenario, specie="CO2 FFI") + emissions.sel(scenario=scenario, specie="CO2 AFOLU")
        ax[0].plot(timepoints, co2, label=scenario, color=scenario_colors[scenario])
    ax[0].plot(timepoints[hist], co2[hist], color="k")
    ax[0].set_ylabel("CO$_2$ emissions, GtCO$_2$ yr$^{-1}$"); ax[0].legend()

    # Cumulative CO2
    for scenario in scenarios:
        co2 = emissions.sel(scenario=scenario, specie="CO2 FFI") + emissions.sel(scenario=scenario, specie="CO2 AFOLU")
        ax[1].plot(timepoints, co2.cumsum(), color=scenario_colors[scenario])
    ax[1].plot(timepoints[hist], co2.cumsum()[hist], color="k")
    ax[1].set_ylabel("Cumulative CO$_2$ emissions, GtCO$_2$")

    # CH4
    for scenario in scenarios:
        ax[2].plot(timepoints, emissions.sel(scenario=scenario, specie="CH4"), color=scenario_colors[scenario])
    ax[2].plot(timepoints[hist], emissions.sel(scenario=scenarios[-1], specie="CH4")[hist], color="k")
    ax[2].set_ylabel("CH$_4$ emissions, MtCH$_4$ yr$^{-1}$")

    # SO2
    for scenario in scenarios:
        ax[3].plot(timepoints, emissions.sel(scenario=scenario, specie="Sulfur"), color=scenario_colors[scenario])
    ax[3].plot(timepoints[hist], emissions.sel(scenario=scenarios[-1], specie="Sulfur")[hist], color="k")
    ax[3].set_ylabel("SO$_2$ emissions, MtS yr$^{-1}$")

    # GHG (CO2e)
    for scenario in scenarios:
        ax[4].plot(timepoints, co2e.sel(scenario=scenario) / 1e6, color=scenario_colors[scenario])
    ax[4].plot(timepoints[hist], co2e.sel(scenario=scenarios[-1])[hist] / 1e6, color="k")
    ax[4].set_ylabel("GHG emissions, GtCO$_2$eq yr$^{-1}$")

    # ERF
    for scenario in scenarios:
        fs = forcing_sum.sel(scenario=scenario)
        ax[5].fill_between(timebounds, fs.quantile(0.05, dim="config"), fs.quantile(0.95, dim="config"),
                           color=scenario_colors[scenario], lw=0, alpha=0.1)
        ax[5].plot(timebounds[274:], fs.median(dim="config")[274:],
                   path_effects=[pe.Stroke(linewidth=4, foreground="w", alpha=0.8), pe.Normal()],
                   color=scenario_colors[scenario])
        ax[5].plot(timebounds, fs.median(dim="config"), color=scenario_colors[scenario])
    ax[5].plot(timebounds[hist], fs.median(dim="config")[hist], color="k")
    ax[5].set_ylabel("Effective radiative forcing, W m$^{-2}$")

    # CO2 concentration
    for scenario in scenarios:
        co2c = co2_concentration.sel(scenario=scenario)
        ax[6].fill_between(timebounds, co2c.quantile(0.05, dim="config"), co2c.quantile(0.95, dim="config"),
                           color=scenario_colors[scenario], lw=0, alpha=0.1)
        ax[6].plot(timebounds[274:], co2c.median(dim="config")[274:],
                   path_effects=[pe.Stroke(linewidth=5, foreground="w", alpha=0.8), pe.Normal()],
                   color=scenario_colors[scenario])
        ax[6].plot(timebounds, co2c.median(dim="config"), color=scenario_colors[scenario])
    ax[6].plot(timebounds[hist], co2c.median(dim="config")[hist], color="k")
    ax[6].axhline(0, ls=":", color="k", lw=0.5)
    ax[6].set_ylabel("Atmospheric CO$_2$ concentration, ppm"); ax[6].set_ylim(0, 1500)

    # Temperature anomaly
    for scenario in scenarios:
        ta = temperature_anom.sel(scenario=scenario)
        ax[7].fill_between(timebounds, ta.quantile(0.05, dim="config"), ta.quantile(0.95, dim="config"),
                           color=scenario_colors[scenario], lw=0, alpha=0.1)
        ax[7].plot(timebounds[274:], ta.median(dim="config")[274:],
                   path_effects=[pe.Stroke(linewidth=4, foreground="w", alpha=0.8), pe.Normal()],
                   color=scenario_colors[scenario])
        ax[7].plot(timebounds, ta.median(dim="config"), label=scenario, color=scenario_colors[scenario])
    ax[7].plot(timebounds[hist], ta.median(dim="config")[hist], color="k")
    ax[7].axhline(0, ls=":", color="k", lw=0.5)
    ax[7].set_ylabel("Temperature above 1850-1900, K"); ax[7].set_ylim(-1, 8); ax[7].legend()

    for a in ax:
        a.axhline(ls=":", color="k", lw=0.5)
        a.grid()
    return fig


def fig_ecdfs(fair: xr.Dataset) -> plt.Figure:
    """ECDFs of temperature anomaly at 2100, 2300, and peak (relative to 1850)."""
    v = _fair_views(fair)
    temperature = v["temperature"]
    scenarios = v["scenarios"]

    T_2100 = temperature.sel(timebounds=2100) - temperature.sel(timebounds=1850)
    T_2300 = temperature.sel(timebounds=2300) - temperature.sel(timebounds=1850)
    T_peak = temperature.max(dim="timebounds") - temperature.sel(timebounds=1850)

    panels = [
        (T_2100, "Temperature anomaly in 2100 relative to 1850, K"),
        (T_2300, "Temperature anomaly in 2300 relative to 1850, K"),
        (T_peak, "Maximum temperature anomaly relative to 1850, K"),
    ]
    fig, ax = plt.subplots(3, 1, figsize=(12, 8))
    for a, (T, title) in zip(ax, panels):
        for scenario in scenarios:
            a.ecdf(T.sel(scenario=scenario), color=scenario_colors[scenario], label=scenario)
        a.set_title(title); a.set_xlabel("K"); a.set_ylabel("Cumulative probability")
        a.set_yticks([0.1, 0.25, 0.33, 0.5, 0.66, 0.75, 0.9])
        a.set_xticks(np.array([-0.5, 0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]) * 2)
        a.set_xlim([-1, 10])
        a.legend(loc="upper right"); a.grid()
    plt.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Batch entrypoint
# ---------------------------------------------------------------------------

def make_all_plots(raw_output, cdr_components, fair, out_dir: Path = PLOTS_DIR) -> dict[str, list[Path]]:
    """Render every paper figure and write to ``out_dir``. Returns name -> paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, list[Path]] = {}

    def _save(name, fig, *targets):
        paths = []
        for fname, kwargs in targets:
            p = out_dir / fname
            fig.savefig(p, **kwargs)
            paths.append(p)
        plt.close(fig)
        outputs[name] = paths

    _save("co2_extensions", fig_co2_extensions(raw_output, cdr_components),
          ("co2_extensions_with_history.png", dict(dpi=150, bbox_inches="tight")))
    _save("co2_emissions",  fig_co2_emissions(fair),
          ("co2_emissions.png", {}))
    _save("ghg_emissions",  fig_ghg_emissions(fair),
          ("ghg_emissions.png", {}))
    _save("temperature",    fig_temperature_emis(fair),
          ("temperature_emis.png", dict(dpi=600, bbox_inches="tight")),
          ("temperature_emis.pdf", dict(format="pdf", bbox_inches="tight")))
    _save("extensions",     fig_extensions(fair),
          ("extensions.png", dict(dpi=600, bbox_inches="tight")),
          ("extensions.pdf", dict(format="pdf", bbox_inches="tight")))
    _save("ecdfs",          fig_ecdfs(fair),
          ("temperature_ecdfs.png", dict(dpi=150, bbox_inches="tight")))

    return outputs
