"""Build notebooks/0505_extensions_plotting.ipynb from cell source strings.

The notebook is intentionally thin -- all figure code lives in
``scripts/plotting.py`` so that the notebook (interactive) and
``scripts/make_plots.py`` (headless CLI) share one source of truth.

Re-run after editing this file or ``plotting.py``:

    .venv/bin/python scripts/build_plotting_notebook.py
"""

from pathlib import Path

import nbformat as nbf

REPO_ROOT = Path(__file__).parent.parent
OUT_PATH = REPO_ROOT / "notebooks" / "0505_extensions_plotting.ipynb"


CELLS: list[tuple[str, str]] = [
    (
        "markdown",
        """\
# ScenarioMIP — extension plots

Interactive notebook. Every figure function lives in
`scripts/plotting.py`; this notebook just loads data, calls each
function, and shows the result inline. You can inspect `raw_output`,
`cdr_components`, and `fair` between cells, or copy a function body
in to tweak styling.

To render the same figures without Jupyter:

```bash
.venv/bin/python scripts/make_plots.py
```
""",
    ),
    (
        "markdown",
        "## Setup",
    ),
    (
        "code",
        """\
import sys
from pathlib import Path

# Make scripts/ importable from this notebook.
sys.path.insert(0, str(Path.cwd().parent / "scripts"))

import matplotlib.pyplot as plt
import plotting

raw_output, cdr_components, fair = plotting.load_data()
print(f"raw_output:     {raw_output.shape}")
print(f"cdr_components: {cdr_components.shape}")
print(f"fair:           {dict(fair.sizes)}")
""",
    ),
    (
        "markdown",
        "## Figure 1 — CO₂ flux extensions",
    ),
    (
        "code",
        """\
fig = plotting.fig_co2_extensions(raw_output, cdr_components)
fig.savefig(plotting.PLOTS_DIR / "co2_extensions_with_history.png", dpi=150, bbox_inches="tight")
plt.show()
""",
    ),
    (
        "markdown",
        "## Figure 2 — CO₂ emissions (annual + cumulative, 1750-2500)",
    ),
    (
        "code",
        """\
fig = plotting.fig_co2_emissions(fair)
fig.savefig(plotting.PLOTS_DIR / "co2_emissions.png")
plt.show()
""",
    ),
    (
        "markdown",
        "## Figure 3 — CO₂ and total GHG emissions (CO₂e)",
    ),
    (
        "code",
        """\
fig = plotting.fig_ghg_emissions(fair)
fig.savefig(plotting.PLOTS_DIR / "ghg_emissions.png")
plt.show()
""",
    ),
    (
        "markdown",
        "## Figure 4 — Temperature & emissions (2000-2150)",
    ),
    (
        "code",
        """\
fig = plotting.fig_temperature_emis(fair)
fig.savefig(plotting.PLOTS_DIR / "temperature_emis.png", dpi=600, bbox_inches="tight")
fig.savefig(plotting.PLOTS_DIR / "temperature_emis.pdf", format="pdf", bbox_inches="tight")
plt.show()
""",
    ),
    (
        "markdown",
        "## Figure 5 — Multi-panel diagnostics",
    ),
    (
        "code",
        """\
fig = plotting.fig_extensions(fair)
fig.savefig(plotting.PLOTS_DIR / "extensions.png", dpi=600, bbox_inches="tight")
fig.savefig(plotting.PLOTS_DIR / "extensions.pdf", format="pdf", bbox_inches="tight")
plt.show()
""",
    ),
    (
        "markdown",
        "## Figure 6 — Temperature ECDFs",
    ),
    (
        "code",
        """\
fig = plotting.fig_ecdfs(fair)
fig.savefig(plotting.PLOTS_DIR / "temperature_ecdfs.png", dpi=150, bbox_inches="tight")
plt.show()
""",
    ),
]


def main() -> None:
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {"display_name": "ScenarioMIP", "language": "python", "name": "scenariomip"},
        "language_info": {"name": "python"},
    }
    cells = []
    for kind, source in CELLS:
        if kind == "markdown":
            cells.append(nbf.v4.new_markdown_cell(source))
        elif kind == "code":
            cells.append(nbf.v4.new_code_cell(source))
        else:
            raise ValueError(kind)
    nb.cells = cells
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w") as f:
        nbf.write(nb, f)
    print(f"Wrote {OUT_PATH} ({len(cells)} cells)")


if __name__ == "__main__":
    main()
