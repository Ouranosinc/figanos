=========
Changelog
=========

0.4.0 (unreleased)
------------------
Contributors to this version: Trevor James Smith (:user:`Zeitsperre`), Marco Braun (:user:`vindelico`), Pascal Bourgault (:user:`aulemahal`), Sarah-Claude Bourdeau-Goulet (:user:`Sarahclaude`)

New features and enhancements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* No-legend option in ``hatchmap``; use ``edgecolor`` and ``edgecolors`` as aliases (:pull:`195`)
* Use list or ndarray as levels for colorbar in gridmap and small bug fixes (:pull:`176`).
* Added style sheet ``transparent.mplstyle`` (:issue:`183`, :pull:`185`)
* Fix NaN issues, extreme values in sizes legend and added edgecolors in ``fg.matplotlib.scattermap``  (:pull:`184`).

Internal changes
^^^^^^^^^^^^^^^^
* Updated the `cookiecutter` template to the latest version. (:pull:`168`):
    * Addresses a handful of misconfigurations in the GitHub Workflows.
    * Updated `ruff` to v0.2.0 and `black` to v24.2.0.
* Removed several unnecessary `noqa` comments from the codebase. (:pull:`168`).

0.3.0 (2024-02-16)
------------------
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

0.2.0 (2023-06-19)
------------------
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

0.1.0 (2023-06-08)
------------------
Contributors to this version: Sarah-Claude Bourdeau-Goulet (:user:`Sarahclaude`), Alexis Beaupré-Laperrière (:user:`Beauprel`), Trevor James Smith (:user:`Zeitsperre`), Juliette Lavoie (:user:`juliettelavoie`).

* First release on PyPI.
