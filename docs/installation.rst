============
Installation
============


To install figanos, run these commands in your terminal:

.. code-block:: console

    $ git clone git@github.com:Ouranosinc/figanos.git
    $ cd figanos
    $ conda env create -f environment.yml
    $ pip install . # add -e if you want the develop mode

Note:
When working in a Jupyter Notebook launched from an environment
that is not figanos, problems may arise with certain functions,
such as gdfmap(). Installing PyProj to this environment should resolve
this issue.

.. comment out for now
    Stable release
    --------------

    To install figanos, run this command in your terminal:

    .. code-block:: console

        $ pip install figanos

    This is the preferred method to install figanos, as it will always install the most recent stable release.

    If you don't have `pip`_ installed, this `Python installation guide`_ can guide
    you through the process.

    .. _pip: https://pip.pypa.io
    .. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


    From sources
    ------------

    The sources for figanos can be downloaded from the `Github repo`_.

    You can either clone the public repository:

    .. code-block:: console

        $ git clone git@github.com:Zeitsperre/figanos

    Or download the `tarball`_:

    .. code-block:: console

        $ curl -OJL https://github.com/Zeitsperre/figanos/tarball/master

    Once you have a copy of the source, you can install it with:

    .. code-block:: console

        $ python setup.py install


    .. _Github repo: https://github.com/Zeitsperre/figanos
    .. _tarball: https://github.com/Zeitsperre/figanos/tarball/master
..
