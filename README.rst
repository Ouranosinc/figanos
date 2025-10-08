=======
figanos
=======

+----------------------------+-----------------------------------------------------+
| Versions                   | |pypi| |conda|                                      |
+----------------------------+-----------------------------------------------------+
| Documentation and Support  | |docs| |versions|                                   |
+----------------------------+-----------------------------------------------------+
| Open Source                | |license| |ossf-score|                              |
+----------------------------+-----------------------------------------------------+
| Coding Standards           | |ruff| |ossf-bp| |pre-commit|                       |
+----------------------------+-----------------------------------------------------+
| Development Status         | |status| |build| |coveralls|                        |
+----------------------------+-----------------------------------------------------+

Figanos: Tool to create FIGures in the OurANOS style

Pour nous partager vos codes à ajouter dans figanos, s.v.p créer un issue sur le repo github avec une description de la fonction et le code de celle-ci.

* Free software: Apache Software License 2.0
* Documentation: https://figanos.readthedocs.io.

Features
--------

* timeseries(): Creates time series as line plots.
* gridmap(): Plots gridded georeferenced data on a map.
* scattermap(): Make a scatter plot of georeferenced data on a map.
* gdfmap(): Plots geometries (through a GeoDataFrame) on a map.
* stripes(): Create climate stripe diagrams.
* violin(): Create seaborn violin plots with extra options.
* heatmap(): Create seaborn heatmaps with extra options.
* taylordiagram(): Create Taylor diagram.

Quick Install
-------------

`figanos` requires GDAL, which can be a bit tricky depending on your operating system.
We recommend using `conda` to manage your Python environment and dependencies, as it simplifies the installation process for these packages.

.. code-block:: shell

    $ conda install -c conda-forge figanos

or if you prefer using `pip` with a system-provided `gdal`, you can install `figanos` from PyPI:

.. code-block:: shell

    $ python -m pip install figanos

Credits
-------

This package was created with Cookiecutter_ and the `Ouranosinc/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/cookiecutter/cookiecutter
.. _`Ouranosinc/cookiecutter-pypackage`: https://github.com/Ouranosinc/cookiecutter-pypackage

.. |build| image:: https://github.com/Ouranosinc/figanos/actions/workflows/main.yml/badge.svg
        :target: https://github.com/Ouranosinc/figanos/actions
        :alt: Build Status

.. |conda| image:: https://img.shields.io/conda/vn/conda-forge/figanos.svg
        :target: https://anaconda.org/conda-forge/figanos
        :alt: Conda-forge Build Version

.. |coveralls| image:: https://coveralls.io/repos/github/Ouranosinc/figanos/badge.svg
        :target: https://coveralls.io/github/Ouranosinc/figanos
        :alt: Coveralls

.. |docs| image:: https://readthedocs.org/projects/figanos/badge/?version=latest
        :target: https://figanos.readthedocs.io/en/latest/
        :alt: Documentation Status

.. |license| image:: https://img.shields.io/pypi/l/figanos
        :target: https://github.com/Ouranosinc/figanos/blob/main/LICENSE
        :alt: License

.. |ossf-bp| image:: https://bestpractices.coreinfrastructure.org/projects/9945/badge
        :target: https://bestpractices.coreinfrastructure.org/projects/9945
        :alt: Open Source Security Foundation Best Practices

.. |ossf-score| image:: https://api.securityscorecards.dev/projects/github.com/Ouranosinc/figanos/badge
        :target: https://securityscorecards.dev/viewer/?uri=github.com/Ouranosinc/figanos
        :alt: OpenSSF Scorecard

.. |pre-commit| image:: https://results.pre-commit.ci/badge/github/Ouranosinc/figanos/main.svg
        :target: https://results.pre-commit.ci/latest/github/Ouranosinc/figanos/main
        :alt: pre-commit.ci status

.. |pypi| image:: https://img.shields.io/pypi/v/figanos.svg
        :target: https://pypi.python.org/pypi/figanos
        :alt: PyPI

.. |ruff| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
        :target: https://github.com/astral-sh/ruff
        :alt: Ruff

.. |status| image:: https://www.repostatus.org/badges/latest/active.svg
        :target: https://www.repostatus.org/#active
        :alt: Project Status: Active – The project has reached a stable, usable state and is being actively developed.

.. |versions| image:: https://img.shields.io/pypi/pyversions/figanos.svg
        :target: https://pypi.python.org/pypi/figanos
        :alt: Supported Python Versions
