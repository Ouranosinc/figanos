=========
Changelog
=========

..
    `Unreleased <https://github.com/Ouranosinc/figanos>`_ (latest)
    --------------------------------------------------------------

    Contributors:

    Changes
    ^^^^^^^
    * No change.

    Fixes
    ^^^^^
    * No change.

.. _changes_0.6.0:

`v0.6.0 <https://github.com/Ouranosinc/figanos/tree/0.6.0>`_ (2026-01-30)
-------------------------------------------------------------------------
Contributors: Sarah-Claude Bourdeau-Goulet (:user:`Sarahclaude`), Juliette Lavoie (:user:`juliettelavoie`), Trevor James Smith (:user:`Zeitsperre`).

Changes
^^^^^^^
* Add possibility to trace the boundary of ``gdfmap`` (:pull:`332`).
* Updated cookiecutter template to latest version (:pull:`362`, :pull:`367`):
    * `ruff` has been configured to provide more linting checks and `black`-like formatting.
    * Removed dependencies and `pre-commit` hooks for `black`, `isort` and `blackdocs`.
    * Added `CITATION.cff` file for better citation metadata.
    * `pyproject.toml` is now `PEP 639 <https://peps.python.org/pep-0639/>`_ compliant.
    * Contributor Covenant agreement is now version 3.0.
    * Migrate from `tox.ini` to `tox.toml`.
    * Drop `python-coveralss` for `coverallsapp/github-action`.
* Make ``get_var_group`` usable externally (:pull:`365`).
* `figanos` now supports Python 3.14 (:pull:`383`).

Fixes
^^^^^
* The `categorical_colors.json` file has been fixed to have the RGB values of IPCC (:pull:`324`, :issue:`239`).
* Fix cbar argument of ``gdfmap`` (:pull:`332`, :issue:`332`).
* Allow ``vmin`` and ``vmax`` to be used with ``divergent`` (:pull:`342`).
* ``fg.matplotlib.hatchmap`` multiplots with colors='none' now works with `xarray` v2025.9.0 (:pull:`360`, :issue:`358`).

.. _changes_0.5.0:

`v0.5.0 <https://github.com/Ouranosinc/figanos/tree/0.5.0>`_ (2025-05-06)
-------------------------------------------------------------------------
Contributors: Juliette Lavoie (:user:`juliettelavoie`), Trevor James Smith (:user:`Zeitsperre`).

Changes
^^^^^^^
* `figanos` now supports Python 3.13 and has dropped support for Python 3.9 (:pull:`322`).
* Several base dependencies have been updated to more modern versions (:pull:`322`):
  * `numpy` has been updated to `>=1.25.0` (no longer pinned below `2.0.0`).
  * `pint` has been updated to `>=0.18.0`.
  * `scikit-image` has been updated to `>=0.21.0`.
  * `xarray` has been updated to `>=2023.11.0`.

Fixes
^^^^^
* The `fg.utils.get_rotpole` function now accepts more general inputs (:pull:`308`).

.. _changes_0.4.0:

`v0.4.0 <https://github.com/Ouranosinc/figanos/tree/0.4.0>`_ (2025-03-10)
-------------------------------------------------------------------------
Contributors to this version: Trevor James Smith (:user:`Zeitsperre`), Marco Braun (:user:`vindelico`), Pascal Bourgault (:user:`aulemahal`), Sarah-Claude Bourdeau-Goulet (:user:`Sarahclaude`), Éric Dupuis (:user:`coxipi`), Juliette Lavoie (:user:`juliettelavoie`).

New features and enhancements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* `figanos` now supports Python 3.12. (:pull:`210`).
* Use list or ndarray as levels for colorbar in gridmap and small bug fixes (:pull:`176`).
* Added style sheet ``transparent.mplstyle`` (:issue:`183`, :pull:`185`)
* Fix ``NaN`` issues, extreme values in sizes legend and added ``edgecolors`` in ``fg.matplotlib.scattermap``  (:pull:`184`).
* New function ``fg.data`` for fetching package data and defined `matplotlib` style definitions. (:pull:`211`).
* New argument ``enumerate_subplots`` for `gridmap`, `timeseries`, `hatchmap` and `scattermap`(:pull:`220`).
* ``fg.taylordiagram`` can now accept datasets with many dimensions (not only `taylor_params`), provided that they all share the same `ref_std` (e.g. normalized taylor diagrams)  (:pull:`214`).
* A new optional way to organize points in a ``fg.taylordiagram``  with  `colors_key`, `markers_key`  : DataArrays with a common dimension value or a common attribute are grouped with the same color/marker (:pull:`214`).
* Heatmap (``fg.matplotlib.heatmap``) now supports `row,col` arguments in `plot_kw`, allowing to plot a grid of heatmaps. (:issue:`208`, :pull:`219`).
* New function ``fg.matplotlib.triheatmap`` (:pull:`199`).
* Reorganized the documentation and add gallery (:issue:`278`, :issue:`274`, :issue:`202`, :pull:`279`).
* Added a new `pooch`-based mechanism for fetching and caching testing data used in the notebooks (``fg.pitou().fetch()``). (:pull:`279`).
* No-legend option in ``hatchmap``; use ``edgecolor`` and ``edgecolors`` as aliases (:pull:`195`)

Breaking changes
^^^^^^^^^^^^^^^^
* `figanos` no longer supports Python 3.8. (:pull:`210`).
* `figanos` now uses a `'src' layout <https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout>`_ for the package. (:pull:`210`).
* `cartopy` has been pinned above v0.23.0 due to a licensing issue. (:pull:`210`).
* `twine` and `wheel` have been removed from the ``dev`` requirements. (:pull:`210`).
* ``fg.taylordiagram`` returns a tuple of `(fig, floating_ax, legend)` instead of only `floating_ax`. (:pull:`214`).

Internal changes
^^^^^^^^^^^^^^^^
* Updated the `cookiecutter` template to the latest version. (:pull:`168`):
    * Addresses a handful of misconfigurations in the GitHub Workflows.
    * Updated `ruff` to v0.2.0 and `black` to v24.2.0.
* Removed several unnecessary `noqa` comments from the codebase. (:pull:`168`).
* Updated the `cookiecutter` template to the latest version. (:pull:`210`):
    * GitHub Workflows have been updated to point to commits rather than tags.
    * The `dependabot` configuration has been updated to run updates on a monthly schedule.
    * Updated `ruff` to v0.3.0 and `black` to v24.4.2.
    * `CHANGES.rst` has been renamed to `CHANGELOG.rst`.
    * Maintainer-specific documentation has been added to new documentation page `releasing.rst`.
* `figanos` now has a `CODE_OF_CONDUCT.rst` file adapting the Contributor Covenant v2.1 conventions. (:pull:`210`).
* Updated the `cookiecutter` template to the latest version. (:pull:`246`):
    * Styling conventions now use ruff and numpydoc-validation to ensure code and docstrings are valid.
    * `tox` now uses `tox-gh` to help automate build configurations on GitHub Workflows.
    * CI configurations have been updated to use hashed commits for PyPI-sourced dependencies.
    * `flake8-alphabetize` has been replaced with `ruff` for some linting checks.
* Updated the notebook coding conventions to adapt to changes in `xclim-testdata`. (:pull:`246`).
* Workflows now make better use of caching to speed up the CI testing process. (:pull:`262`).
* Updated the `cookiecutter` template to the latest version. (:pull:`273`):
    * Several development dependencies have been updated to their latest versions.
    * Updated the GitHub Actions in Workflows to their latest versions.
* The documentation has been adapted to use the latest testing data fetching mechanism from `xclim`. (:pull:`273`).
* Updated the `cookiecutter` template to the latest version. Dependencies and GitHub Actions have been updated. (:pull:`282`).
* The `bump-version.yml` GitHub Workflow has been updated to use the Ouranos Helper Bot instead of personal access tokens. (:pull:`287`).
* Updated the `cookiecutter` template to the latest version. (:pull:`295`):
    * Added a CodeQL Advanced configuration.
    * Updated versions of many GitHub Actions and Python dependencies.
    * Removed `coveralls` from the CI dependencies.
    * Added `pre-commit` hooks for `vulture` (dead code) and `codespell` (typos).

Bug fixes
^^^^^^^^^
* Creating the colormap in `fg.matplotlib.scattermap` is now done like `fg.matplotlib.gridmap` (:pull:`238`, :issue:`239`).
* Updated the default testing data URL in the `pitou` function to point to the correct branch. (:pull:`282`).

.. _changes_0.3.0:

v0.3.0 (2024-02-16)
-------------------
Contributors to this version: Sarah-Claude Bourdeau-Goulet (:user:`Sarahclaude`), Pascal Bourgault (:user:`aulemahal`), Trevor James Smith (:user:`Zeitsperre`), Juliette Lavoie (:user:`juliettelavoie`), Gabriel Rondeau-Genesse (:user:`RondeauG`).

New features and enhancements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* New function ``fg.matplotlib.hatchmap`` (:pull:`107`).
* Support for translating figures. Activating a locale through `xclim`'s ``metadata_locales`` option will try to use metadata saved by `xclim` or `xscen` in this locale and to translate common terms appearing in the figures. `figanos` currently ships with French translations of those terms. (:pull:`109`, :issue:`64`).
* New ``figanos.Logos`` class added to manage and install logos stored in user's Home configuration directory. The ``figanos.utils.plot_logo`` function call signature has changed to support the new system. (:issue:`115`, :pull:`119`).
* Logo sizing and placement now depends on `scikit-image` for resizing, and uses ``"width"`` and ``"height"`` instead of ``"zoom"``. (:issue:`123`, :pull:`119`).
* Logo plotting now supports both PNG and SVG file types (via `cairosvg`). (:pull:`119`).
* Use small geojson in the notebook. (:pull:`124`).
* Add the Colours of Figanos page (:issue:`126`, :pull:`127`).
* Figanos now adheres to PEPs 517/518/621 using the `flit` backend for building and packaging. (:pull:`135`).
* New function ``fg.partition`` (:pull:`134`).
* Add wrapper around ``xarray.plot.facetgrid`` for map functions (``fg.gridmap``, ``fg.scattermap``, ``fg.hatchmap``). (:issue:`51`, :pull:`136`).
* `figanos` now uses `Semantic Versioning v2.0 <https://semver.org/spec/v2.0.0.html>`_. (:pull:`143`).
* Add wrapper around ``xarray.plot.facetgrid`` for multiple functions (``fg.gridmap``, ``fg.scattermap``, ``fg.hatchmap``, ``fg.timeseries``). (:issue:`51`, :pull:`136`).

Bug fixes
^^^^^^^^^
* Fixed packaging issue with the `Manifest.in` not bundling a YAML file loaded on import. (:pull:`118`).

Internal changes
^^^^^^^^^^^^^^^^
* Clean up of the dependencies to remove the notebooks deps from the core deps.
* `figanos` now uses Trusted Publishing to publish the package on PyPI and TestPyPI. (:pull:`113`).
* The official Ouranos logos have been removed from the repository. They can now be installed if required via the ``figanos.Logos.install_ouranos_logos`` class method. (:issue:`115`, :pull:`119`).
* Documentation adjustments. (:pull:`121`):
    * Added a few `pre-commit` hooks for cleaning up notebooks and ensuring that docstrings are properly formatted.
    * Cleaned up the docstrings of a few functions, added some module-level strings, minor typo fixes.
    * Set `nbsphinx` in the documentation to always run (with th exception of one complex cell).
    * The `environment-dev.yml` Python version is set to `3.11` to reduce the dependency solver complexity.
* The `cookiecutter` template has been updated to the latest commits via `cruft`. (:pull:`138`, :pull:`143`):
    * `Manifest.in`, `requirements_dev.txt`, `requirements_docs.txt` and `setup.py` have been removed.
    * `pyproject.toml` has been added, with most package configurations migrated into it.
    * `HISTORY.rst` has been renamed to `CHANGES.rst`.
    * `dependabot` has been added to the GitHub workflows to manage workflow and package dependency pins.
    * `bump-version.yml` has been added to automate patch versioning of the package.
    * `pre-commit` hooks have been updated to the latest versions; `check-toml` and `toml-sort` have been added to cleanup the `pyproject.toml` file.
    * `ruff` has been added to the linting tools to replace most `flake8` and `pydocstyle` verifications.
    *  GitHub workflows now run proper pytest suites for `conda`-based testing.
    * `figanos` now uses the `actions/labeler` action to automatically label pull requests based on their content.
    * GitHub workflows are now using the `step-security/harden-runner` action to harden the runner environment.
    * The OpenSSF `scorecard.yml` workflow has been added to the GitHub workflows to evaluate package security.

Bug fixes
^^^^^^^^^
* Fixed an issue with the `divergent` argument getting ignored (:pull:`132`).
* Some small documentation fixes for working uniquely in a `conda` environment. (:pull:`138`).

.. _changes_0.2.0:

v0.2.0 (2023-06-19)
-------------------
Contributors to this version: Sarah-Claude Bourdeau-Goulet (:user:`Sarahclaude`), Trevor James Smith (:user:`Zeitsperre`), Juliette Lavoie (:user:`juliettelavoie`).

New features and enhancements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* Improved documentation to reduce warnings, now using the `sphinx-book-theme`. (:pull:`97`, :pull:`98`).
* Python3.7 support has been dropped. (:pull:`100`).

Bug fixes
^^^^^^^^^
* Fixed issue in environment.yml that was installing two versions of cartopy. (:pull:`97`).

Internal changes
^^^^^^^^^^^^^^^^
* Updated autogenerated boilerplate (Ouranosinc/cookiecutter-pypackage) via `cruft`. (:pull:`100`):
    * General updates to pre-commit hooks, development dependencies, documentation.
    * Added configurations for Pull Request and Issues templates, Zenodo.
    * Documentation now makes use of sphinx directives for usernames, issues, and pull request hyperlinks (via `sphinx.ext.extlinks`).
    * GitHub Workflows have been added for automated testing, and publishing.
    * Some sphinx extensions have been added/enabled (`sphinx-codeautolink`, `sphinx-copybutton`).
    * Automated testing with `tox` now updated to use v4.0+ conventions.
    * Removed all references to `travis.ci`.

.. _changes_0.1.0:

v0.1.0 (2023-06-08)
-------------------
Contributors to this version: Sarah-Claude Bourdeau-Goulet (:user:`Sarahclaude`), Alexis Beaupré-Laperrière (:user:`Beauprel`), Trevor James Smith (:user:`Zeitsperre`), Juliette Lavoie (:user:`juliettelavoie`).

* First release on PyPI.
