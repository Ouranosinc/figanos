============
Installation
============


To install spirograph, run these commands in your terminal:

.. code-block:: console

    $ git clone git@github.com:Ouranosinc/spirograph.git
    $ cd spirograph
    $ conda env create -f environment.yml
    $ pip install . # add -e if you want the develop mode

Note:
When working in a Jupyter Notebook launched from an environment
that is not spirograph, problems may arise with certain functions,
such as gdfmap(). Installing PyProj to this environment should resolve
this issue.

.. comment out for now
    Stable release
    --------------

    To install spirograph, run this command in your terminal:

    .. code-block:: console

        $ pip install spirograph

    This is the preferred method to install spirograph, as it will always install the most recent stable release.

    If you don't have `pip`_ installed, this `Python installation guide`_ can guide
    you through the process.

    .. _pip: https://pip.pypa.io
    .. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


    From sources
    ------------

    The sources for spirograph can be downloaded from the `Github repo`_.

    You can either clone the public repository:

    .. code-block:: console

        $ git clone git@github.com:Zeitsperre/spirograph

    Or download the `tarball`_:

    .. code-block:: console

        $ curl -OJL https://github.com/Zeitsperre/spirograph/tarball/master

    Once you have a copy of the source, you can install it with:

    .. code-block:: console

        $ python setup.py install


    .. _Github repo: https://github.com/Zeitsperre/spirograph
    .. _tarball: https://github.com/Zeitsperre/spirograph/tarball/master
..
