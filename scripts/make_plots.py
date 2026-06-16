"""Render every paper figure to ``plots/`` without Jupyter.

    .venv/bin/python scripts/make_plots.py
    .venv/bin/python scripts/make_plots.py --out-dir /tmp/plots

If ``data/fair-outputs/fair_run.nc`` is missing, the FaIR simulation is
run first (a few minutes).
"""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless backend; must be set before pyplot import

from plotting import PLOTS_DIR, load_data, make_all_plots  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=PLOTS_DIR, help=f"Output directory (default: {PLOTS_DIR})")
    args = parser.parse_args()

    raw_output, cdr_components, fair = load_data()
    outputs = make_all_plots(raw_output, cdr_components, fair, out_dir=args.out_dir)

    print(f"Wrote {sum(len(v) for v in outputs.values())} files to {args.out_dir}:")
    for name, paths in outputs.items():
        for p in paths:
            print(f"  {name:<18s} {p.name}")


if __name__ == "__main__":
    main()
