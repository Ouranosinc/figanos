============
Installation
============

..
    We strongly recommend installing figanos in an Anaconda Python environment.
    Furthermore, due to the complexity of some packages, the default dependency solver can take a long time to resolve the environment.
    If `mamba` is not already your default solver, consider running the following commands in order to speed up the process:

        .. code-block:: console

            conda install -n base conda-libmamba-solver
            conda config --set solver libmamba

If you don't have `pip`_ installed, this `Python installation guide`_ can guide you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


Official Source
---------------

`figanos` requires GDAL, which can be a bit tricky depending on your operating system.
We recommend using `conda` to manage your Python environment and dependencies, as it simplifies the installation process for these packages.

.. code-block:: console

    conda install -c conda-forge figanos

or if you prefer using `pip` with a system-provided `gdal`, you can install `figanos` from PyPI:

.. code-block:: console

    python -m pip install figanos

Development Installation (conda + pip)
--------------------------------------

For development purposes, we provide the means for generating a conda environment with the latest dependencies in an `environment.yml` file at the top-level of the `Github repo <https://github.com/Ouranosinc/figanos>`_.

In order to get started, first clone the repo locally:

.. code-block:: console

    git clone git@github.com:Ouranosinc/figanos.git

Then you can create the environment and install the package:

.. code-block:: console

    cd figanos
    conda env create -f environment-dev.yml

Finally, perform an `--editable` install of `figanos`:

.. code-block:: console

    python -m pip install -e .
    # Or
    make dev
