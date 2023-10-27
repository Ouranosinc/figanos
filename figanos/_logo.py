import logging
import shutil
import urllib.parse
import urllib.request
import warnings
from pathlib import Path
from typing import Optional, Union

import platformdirs
import yaml

__all__ = ["Logos"]

LOGO_CONFIG_FILE = "logo_mapping.yaml"
OURANOS_LOGOS_URL = "https://raw.githubusercontent.com/Ouranosinc/.github/main/images/"
_figanos_logo = Path(__file__).parent / "data" / "figanos_logo.png"


class Logos:
    r"""Class for managing logos to be used in graphics.

    Methods
    -------
    default
        The path to the default logo.
        can be temporarily set to a different logo via Logos().default = pathlib.Path().
    installed()
        Retrieves a list of installed logos.
    install_ouranos_logos(\*, permitted: bool = False)
        Fetches and installs the Ouranos logos.
    set_logo(path: Union[str, Path], name: str = None)
        Sets the path and name to a logo file.
        If no logos are already set, the first one will be set as the default.
    reload_config()
        Reloads the logo configuration from the YAML file.

    Examples
    --------
    >>> from figanos import Logos
    >>> logos = Logos()
    >>> logos.default
    PosixPath('/home/user/.config/figanos/logos/figanos_logo.png')
    >>> logos.installed()
    ['default', 'figanos_logo']
    >>> logos.set_logo("path/to/logo.png", name="my_logo")
    PosixPath('/home/user/.config/figanos/logos/my_logo.png')
    >>> logos["my_logo"]
    PosixPath('/home/user/.config/figanos/logos/my_logo.png')
    >>> logos.default = "path/to/temporary/default/logo.png"
    >>> logos
    PosixPath("path/to/temporary/default/logo.png")
    >>> logos.reload_config()
    >>> logos.default
    PosixPath('/home/user/.config/figanos/logos/figanos_logo.png')
    """

    def __init__(self) -> None:
        """Initialize the Logo class instance."""
        self._config = None
        self._catalogue = None
        self._default = None
        self._logos = {}
        self.reload_config()

        if not self._logos.get("default"):
            warnings.warn(f"Setting default logo to {_figanos_logo}")
            self.set_logo(_figanos_logo)
            self.set_logo(_figanos_logo, name="default")

    @property
    def config(self) -> Path:
        """The path to the logo configuration folder."""
        if self._config is None:
            self._config = (
                Path(platformdirs.user_config_dir("figanos", ensure_exists=True))
                / "logos"
            )
        return self._config

    @property
    def catalogue(self) -> Path:
        """The path to the logo configuration file."""
        if self._catalogue is None:
            self._catalogue = self.config / LOGO_CONFIG_FILE
        return self._catalogue

    @property
    def default(self) -> str:
        """The path to the default logo."""
        return self._default

    @default.setter
    def default(self, value: Union[str, Path]):
        """Set a default logo."""
        self._default = value

    def _setup(self) -> None:
        if (
            not self.catalogue.exists()
            or yaml.safe_load(self.catalogue.read_text()) is None
        ):
            if not self.catalogue.exists():
                warnings.warn(
                    f"No logo configuration file found. Creating one at {self.catalogue}."
                )
            self.config.mkdir(parents=True, exist_ok=True)
            with open(self.catalogue, "w") as f:
                yaml.dump(dict(logos={}), f)

    def __str__(self) -> str:
        """Return the default logo filepath."""
        return f"{self._default}"

    def __repr__(self) -> str:
        """Return the default logo filepath."""
        return f"{self._default}"

    def __getitem__(self, args) -> Optional[str]:
        """Retrieve a logo filepath by its name.

        If it does not exist, it will be installed, with the filepath returned.
        """
        try:
            return self._logos[args]
        except (KeyError, TypeError):
            if isinstance(args, tuple):
                return self.set_logo(*args)
            else:
                return self.set_logo(args)

    def reload_config(self) -> None:
        """Reload the configuration from the YAML file."""
        self._setup()
        self._logos = yaml.safe_load(self.catalogue.read_text())["logos"]
        for logo_name, logo_path in self._logos.items():
            if not Path(logo_path).exists():
                warnings.warn(f"Logo file {logo_name} not found at {logo_path}.")
            setattr(self, logo_name, logo_path)

    def installed(self) -> list:
        """Retrieve a list of installed logos."""
        return list(self._logos.keys())

    def set_logo(
        self, path: Union[str, Path], name: Optional[str] = None
    ) -> Optional[str]:
        """Copy an image at a given path to the config folder and map it to a given name in the catalogue."""
        _logo_mapping = yaml.safe_load(self.catalogue.read_text())["logos"]

        logo_path = Path(path)
        if logo_path.exists() and logo_path.is_file():
            if name is None:
                name = logo_path.stem.replace("-", "_")
            install_logo_path = self.config / logo_path.name

            if not install_logo_path.exists():
                shutil.copy(logo_path, install_logo_path)

            logging.info("Setting %s logo to %s", name, install_logo_path)
            _logo_mapping[name] = str(install_logo_path)
            self.catalogue.write_text(yaml.dump(dict(logos=_logo_mapping)))
            self.reload_config()
            if name != "default":
                return self._logos[name]
            else:
                return self._default

        elif not logo_path.exists():
            warnings.warn(f"Logo file `{logo_path}` not found. Not setting logo.")
        elif not logo_path.is_file():
            warnings.warn(f"Logo path `{logo_path}` is a folder. Not setting logo.")

    def install_ouranos_logos(self, *, permitted: bool = False) -> None:
        """Fetch and install the Ouranos logo.

        The Ouranos logo is reserved for use by employees and project partners of Ouranos.

        Parameters
        ----------
        permitted : bool
            Whether the user has permission to use the Ouranos logo.
        """
        if permitted:
            for orientation in ["horizontal", "vertical"]:
                for colour in ["couleur", "blanc", "noir"]:
                    file = f"logo-ouranos-{orientation}-{colour}.svg"
                    if not (self.config / file).exists():
                        logo_url = urllib.parse.urljoin(OURANOS_LOGOS_URL, file)
                        try:
                            urllib.request.urlretrieve(logo_url, self.config / file)
                            self.set_logo(self.config / file)
                        except Exception as e:
                            logging.error(
                                f"Error downloading or setting Ouranos logo: {e}"
                            )

            if Path(self.default).stem == "figanos_logo":
                _default_ouranos_logo = (
                    self.config / "logo-ouranos-horizontal-couleur.svg"
                )
                warnings.warn(f"Setting default logo to {_default_ouranos_logo}.")
                self.set_logo(_default_ouranos_logo, name="default")
            self.reload_config()
            print(f"Ouranos logos installed at: {self.config}.")
        else:
            warnings.warn(
                "You have not indicated that you have permission to use the Ouranos logo. "
                "If you do, please set the `permitted` argument to `True`."
            )
