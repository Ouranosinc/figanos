import logging
import shutil
import urllib.request
import warnings
from pathlib import Path
from typing import Optional, Union

import platformdirs
import yaml

__all__ = ["Logos"]

LOGO_CONFIG_FILE = "logo_mapping.yaml"
OURANOS_LOGO_URL_TEMPLATE = (
    "https://raw.githubusercontent.com/Ouranosinc/.github/main/images/"
    "ouranos_logo_{orientation}_{colour}.png"
)


class Logos:
    """Class for managing logos to be used in graphics.

    Attributes
    ----------
    config : Path
        The path to the folder where the logo configuration file is stored.
    catalogue : Path
        The path to the logo configuration file.

    Methods
    -------
    set_logo(path: Union[str, Path], name: str = None)
        Sets the path and name to a logo file.
        If no logos are already set, the first one will be set as the default.
    install_ouranos_logos(permitted: bool = False)
        Fetches and installs the Ouranos logos.
    """

    def __init__(self) -> None:
        """Constructor for the Logo class."""
        self.config = (
            Path(platformdirs.user_config_dir("figanos", ensure_exists=True)) / "logos"
        )
        self.catalogue = self.config / LOGO_CONFIG_FILE
        self._logos = {}
        self._setup()

        _logos = yaml.safe_load(self.catalogue.read_text())
        if not _logos.get("logos"):
            warnings.warn(
                "No entries found in the logo configuration file. "
                "Consider setting some logos with the figanos.Logo().set_logo() method."
            )
        else:
            self._logos = _logos["logos"]
            for logo_name, logo_path in self._logos["logos"].items():
                if not Path(logo_path).exists():
                    warnings.warn(f"Logo file {logo_path} does not exist.")
                setattr(self, logo_name, logo_path)

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
        return self._logos.get(name)

    def reload_config(self) -> None:
        """Reload the configuration from the YAML file."""
        _logo_mapping = yaml.safe_load(self.catalogue.read_text())
        self._logos = _logo_mapping.get("logos", {})

    def set_logo(self, path: Union[str, Path], name: Optional[str] = None) -> None:
        """Copies the logo at a given path to the config folder and maps it to a given name in the logo config."""
        _logo_mapping = yaml.safe_load(self.catalogue.read_text())

        logo_path = Path(path)
        if logo_path.exists() and logo_path.is_file():
            if name is None:
                name = logo_path.stem
            install_logo_path = self.config / logo_path.name

            if not install_logo_path.exists():
                shutil.copy(logo_path, install_logo_path)

            if name != "default" and not _logo_mapping["logos"].get("default"):
                logging.info("Setting default logo to %s", install_logo_path)
                _logo_mapping["logos"]["default"] = str(install_logo_path)

            logging.info("Setting %s logo to %s", name, install_logo_path)
            _logo_mapping["logos"][name] = str(install_logo_path)
            self.catalogue.write_text(yaml.dump(_logo_mapping))
            self.reload_config()

        else:
            warnings.warn(f"Logo file {logo_path} does not exist.")

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
                    file = self.config / f"ouranos_logo_{orientation}_{colour}.png"
                    logo_url = OURANOS_LOGO_URL_TEMPLATE.format(
                        orientation=orientation, colour=colour
                    )
                    try:
                        urllib.request.urlretrieve(logo_url, file)
                        self.set_logo(file)
                    except Exception as e:
                        logging.error(f"Error downloading or setting Ouranos logo: {e}")

            _logo_mapping = yaml.safe_load(self.catalogue.read_text())
            if not _logo_mapping["logos"].get("default"):
                logging.info("Setting default logo ouranos_logo_horizontal_couleur.png")
                _logo_mapping["logos"]["default"] = str(
                    self.config / "ouranos_logo_horizontal_couleur.png"
                )
                self.catalogue.write_text(yaml.dump(_logo_mapping))
            self.reload_config()
        else:
            warnings.warn(
                "You have not indicated that you have permission to use the Ouranos logo. "
                "If you do, please set the `permitted` argument to `True`."
            )
