=====
Usage
=====

Quickstart
~~~~~~~~~~

To use figanos in a project::

    import figanos.matplotlib as fg
    fg.utils.set_mpl_style('ouranos')

The style can be applied to any matplotlib figures, even if they are not created with figanos.

Installing Logos
~~~~~~~~~~~~~~~~

Custom logos can be installed via the `figanos.Logos().set_logo()`` class method. Logos are stored for convenience and can be called by name when creating figures.

The logos are stored in the user's home configuration directory in the ``figanos`` data folder (On Linux, the `$XDG_CONFIG_HOME` folder). The ``set_logo()`` method takes the following arguments:

.. code-block:: python

    from figanos import Logos

    logos = Logos().set_logo(
        "/path/to/my/file.png",  # Path to the logo file
        "my_custom_logo",  # Name of the logo, optional
    )

    logos.my_custom_logo  # Returns the installed logo path

On installation, the `default` logo will be set to the `figanos_logo.png` file. To set it to a different logo, simply call the `set_logo()` method with the path to the desired logo with the name set as `default`.

For users who are permitted to use the Ouranos logos, the logos can be installed with the following command:

.. code-block:: python

    from figanos import Logos

    logos = Logos().install_ouranos_logos(permitted=True)

    logos.installed()  # Returns the installed logo path
    # ['default',
    # 'ouranos_logo_horizontal_blanc',
    # 'ouranos_logo_horizontal_couleur',
    # 'ouranos_logo_horizontal_noir',
    # 'ouranos_logo_vertical_blanc',
    # 'ouranos_logo_vertical_couleur',
    # 'ouranos_logo_vertical_noir']
