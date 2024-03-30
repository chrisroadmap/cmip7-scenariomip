# explore-extensions
Extending emissions pathways beyond 2125 - in a very stylised way

## how to reproduce
1. clone the repository
2. install the environment with `conda env create -f environment.yml`
3. activate environment `conda activate explore-extensions`
4. run `nbstripout --install` to commit clean notebooks
5. run `jupyter notebook`
6. navigate to the `notebooks` directory and run `extensions.ipynb`

## notes
This repo contains a development version of `fair-2.2` that allows for quick importing of scenarios from CSV files. When eventually committed to the main branch, this repo might not work out of the box. Raise an issue if you get problems.

and on that basis, you can easily modify the scenarios yourself by hacking the CSV files in `data/emissions/`.