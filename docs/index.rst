Welcome to figanos's documentation!
===================================

Figanos: Tool to create **fig**\ ures\  in\  the Our\ **anos**\  style.

Overview
^^^^^^^^

Figanos is a dictionary-based function interface that wraps `Matplotlib <https://matplotlib.org>`_ and `Xarray <https://docs.xarray.dev/en/stable/>`_ plotting functions to create common climate data plots. Its inputs are most commonly xarray DataArrays or Datasets, and it is best used when these arrays are the output of workflows incorporating `Xscen <https://github.com/Ouranosinc/xscen>`_ and/or `Xclim <https://xclim.readthedocs.io/en/stable/>`_. Style-wise, the plots follow the general guidelines offered by the `IPCC visual style guide 2022 <https://www.ipcc.ch/site/assets/uploads/2022/09/IPCC_AR6_WGI_VisualStyleGuide_2022.pdf>`_, but aim to create a look that could be distinctively associated with `Ouranos <https://www.ouranos.ca/en>`_.


The following features are included in the package:

* Automatically recognizes some common data structures (e.g. climate ensembles) using variable and coordinate names and creates the appropriate plots.
* Automatically links attributes from xarray objects to plot elements (title, axes), with customization options.
* Automatically assigns colors to some common variables and, following the IPCC visual guidelines.
* Provides options to visually enhance the plots, and includes a default style to ensure coherence when creating multiple plots.
* Returns a `matplotlib axes object <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.html#matplotlib.axes.Axes>`_ that is fully customisable through matplotlib functions and methods.


Need help?
^^^^^^^^^^
* Ouranos employees can ask questions on the Ouranos private StackOverflow where you can tag subjects and people. (https://stackoverflow.com/c/ouranos/questions ).
* Potential bugs in figanos can be reported as an issue here: https://github.com/Ouranosinc/figanos/issues .
* Problems with data on Ouranos' servers can be reported as an issue here: https://github.com/Ouranosinc/miranda/issues
* To be aware of changes in figanos, you can "watch" the github repo. You can customize the watch function to notify you of new releases. (https://github.com/Ouranosinc/figanos )

.. toctree::
   :maxdepth: 2
   :caption: Table of Contents:

   installation
   usage
   gallery
   notebooks/index
   api
   contributing
   releasing
   authors
   changelog

.. toctree::
   :maxdepth: 1
   :caption: All Modules

   apidoc/modules
