=====
Usage
=====

Quickstart
~~~~~~~~~~
To use figanos in a project:

.. code-block:: python

    import figanos.matplotlib as fg

    fg.utils.set_mpl_style("ouranos")

The style can be applied to any matplotlib figures, even if they are not created with figanos.

Logo Management
~~~~~~~~~~~~~~~
Figanos stores logos for convenience so that they can be called by name when creating figures. On installation, the `default` logo will be set to the `figanos_logo.png` file. Files are saved in the user's home configuration folder (`XDG_CONFIG_HOME` on Linux), in the `figanos/logos` folder.

For users who are permitted to use the Ouranos logos, they can be installed with the following command. You only need to run this once when setting up a new environment with figanos.

.. code-block:: python

    from figanos import Logos

    logos = Logos()

    logos.default  # Returns the path to the default logo
    # '/home/username/.config/figanos/logos/figanos_logo.png'

    logos.install_ouranos_logos(permitted=True)
    # "Ouranos logos installed at /home/username/.config/figanos/logos"

    logos.installed()  # Returns the installed logo names
    # ['default',
    # 'figanos_logo',
    # 'ouranos_logo_horizontal_blanc',
    # 'ouranos_logo_horizontal_couleur',
    # 'ouranos_logo_horizontal_noir',
    # 'ouranos_logo_vertical_blanc',
    # 'ouranos_logo_vertical_couleur',
    # 'ouranos_logo_vertical_noir']

Custom Logos
^^^^^^^^^^^^
Custom logos can also be installed via the `figanos.Logos().set_logo()`` class method.

The ``set_logo()`` method takes the following arguments:

.. code-block:: python

    from figanos import Logos

    logos = Logos().set_logo(
        "/path/to/my/file.png",  # Path to the logo file
        "my_custom_logo",  # Name of the logo, optional
        # If no name is provided, the name will be the file name without the extension
    )

    logos.my_custom_logo  # Returns the installed logo path

To change the default to an already-installed logo, simply call the `set_logo()` method with the logo.<option> and the name set as `default`. For example:

.. code-block:: python

    # To set the default logo to the horizontal white Ouranos logo
    logos.set_logo(logos.ouranos_logo_horizontal_blanc, "default")
