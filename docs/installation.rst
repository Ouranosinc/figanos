============
Installation
============

Official Source
---------------

To install figanos, run these commands in your terminal:

.. code-block:: console

    $ mamba install -c conda-forge gdal
    $ python -m pip install figanos

Development Installation (conda + pip)
--------------------------------------

For development purposes, we provide the means for generating a conda environment with the latest dependencies in an `environment.yml` file at the top-level of the `Github repo`_.

In order to get started, first clone the repo locally:

.. code-block:: console

    $ git clone git@github.com:Ouranosinc/figanos.git

Then you can create the environment and install the package:

.. code-block:: console

    $ cd figanos
    $ conda env create -f environment-dev.yml

Finally, perform an `--symlink` install of figanos:

.. code-block:: console

    $ flit install --symlink
    # Or
    $ make dev

.. _Github repo: https://github.com/Ouranosinc/figanos
