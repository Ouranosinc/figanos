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

    Attributes
    ----------
    config : Path
        The path to the folder where the logo configuration file is stored.
    catalogue : Path
        The path to the logo configuration file.
    default : str
        The path to the default logo.

    Methods
    -------
    installed()
        Retrieves a list of installed logos.
    install_ouranos_logos(\*, permitted: bool = False)
        Fetches and installs the Ouranos logos.
    set_logo(path: Union[str, Path], name: str = None)
        Sets the path and name to a logo file.
        If no logos are already set, the first one will be set as the default.
    reload_config()
        Reloads the logo configuration from the YAML file.
    """

    default = None

    def __init__(self) -> None:
        """Constructor for the Logo class."""
        self.config = (
            Path(platformdirs.user_config_dir("figanos", ensure_exists=True)) / "logos"
        )
        self.catalogue = self.config / LOGO_CONFIG_FILE
        self._logos = {}
        self.reload_config()

        if not self._logos.get("default"):
            warnings.warn(f"Setting default logo to {_figanos_logo}")
            self.set_logo(_figanos_logo)
            self.set_logo(_figanos_logo, name="default")

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

    def __str__(self):
        return f"{self.__getitem__('default')}"

    def __repr__(self):
        return f"{self._logos.items()}"

    def __getitem__(self, name: str) -> Optional[str]:
        """Retrieve a logo path by its name."""
        return self._logos.get(name, None)

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

    def set_logo(self, path: Union[str, Path], name: Optional[str] = None) -> None:
        """Copies the logo at a given path to the config folder and maps it to a given name in the logo config."""
        _logo_mapping = yaml.safe_load(self.catalogue.read_text())["logos"]

        logo_path = Path(path)
        if logo_path.exists() and logo_path.is_file():
            if name is None:
                name = logo_path.stem
            install_logo_path = self.config / logo_path.name

            if not install_logo_path.exists():
                shutil.copy(logo_path, install_logo_path)

            logging.info("Setting %s logo to %s", name, install_logo_path)
            _logo_mapping[name] = str(install_logo_path)
            self.catalogue.write_text(yaml.dump(dict(logos=_logo_mapping)))
            self.reload_config()

        elif not logo_path.exists():
            warnings.warn(f"Logo file {logo_path} not found. Not setting logo.")
        elif not logo_path.is_file():
            warnings.warn(f"Logo path {logo_path} is a folder. Not setting logo.")

    def install_ouranos_logos(self, *, permitted: bool = False) -> None:
        """Fetches and installs the Ouranos logo.

        The Ouranos logo is reserved for use by employees and project partners of Ouranos.

        Parameters
        ----------
        permitted : bool
            Whether the user has permission to use the Ouranos logo.
        """
        if permitted:
            for orientation in ["horizontal", "vertical"]:
                for colour in ["couleur", "blanc", "noir"]:
                    file = f"ouranos_logo_{orientation}_{colour}.png"
                    logo_url = urllib.parse.urljoin(OURANOS_LOGOS_URL, file)
                    try:
                        urllib.request.urlretrieve(logo_url, self.config / file)
                        self.set_logo(self.config / file)
                    except Exception as e:
                        logging.error(f"Error downloading or setting Ouranos logo: {e}")

            if Path(self.default).stem == "figanos_logo":
                _default_ouranos_logo = (
                    self.config / "ouranos_logo_vertical_couleur.png"
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
