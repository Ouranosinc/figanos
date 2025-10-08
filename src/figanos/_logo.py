from __future__ import annotations
import logging
import shutil
import urllib.parse
import urllib.request
import warnings
from pathlib import Path
from urllib.error import URLError

import platformdirs
import yaml


__all__ = ["Logos"]

logger = logging.getLogger(__name__)

LOGO_CONFIG_FILE = "logo_mapping.yaml"
OURANOS_LOGOS_URL = "https://raw.githubusercontent.com/Ouranosinc/.github/main/images/"
_figanos_logo = Path(__file__).parent / "data" / "figanos_logo.png"


class Logos:
    r"""
    Class for managing logos to be used in graphics.

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
        self._config: Path = Path(platformdirs.user_config_dir("figanos")) / "logos"
        self._catalogue: Path = self._config / LOGO_CONFIG_FILE
        self._default: Path = self._config / "figanos_logo.png"
        self._logos: dict[str, str] = {}
        self.reload_config()

        if not self._logos.get("default"):
            warnings.warn(f"Setting default logo to {_figanos_logo}", stacklevel=2)
            self.set_logo(_figanos_logo)
            self.set_logo(_figanos_logo, name="default")

    @property
    def catalogue(self) -> Path:
        """The path to the logo configuration file."""
        return self._catalogue

    @property
    def default(self) -> Path:
        """The path to the default logo."""
        return self._default

    @default.setter
    def default(self, value: Path):
        """Set a default logo."""
        self._default = value

    def _setup(self) -> None:
        if (
            not self.catalogue.exists()
            or yaml.safe_load(self.catalogue.read_text()) is None
        ):
            if not self.catalogue.exists():
                warnings.warn(
                    f"No logo configuration file found. Creating one at {self.catalogue}.", stacklevel=2
                )
            self._config.mkdir(parents=True, exist_ok=True)
            with self.catalogue.open("w", encoding="utf-8") as f:
                yaml.dump(dict(logos={}), f)

    def __str__(self) -> str:
        """Return the default logo filepath."""
        return f"{self._default}"

    def __repr__(self) -> str:
        """Return the default logo filepath."""
        return f"{self._default}"

    def __getitem__(self, args) -> str | None:
        """
        Retrieve a logo filepath by its name.

        If it does not exist, it will be installed, with the filepath returned.
        """
        try:
            return str(self._logos[args])
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
                warnings.warn(f"Logo file {logo_name} not found at {logo_path}.", stacklevel=2)
            setattr(self, logo_name, logo_path)

    def installed(self) -> list:
        """Retrieve a list of installed logos."""
        return list(self._logos.keys())

    def set_logo(self, path: str | Path, name: str | None = None) -> str | None:
        """Copy an image at a given path to the config folder and map it to a given name in the catalogue."""
        _logo_mapping = yaml.safe_load(self.catalogue.read_text())["logos"]

        logo_path = Path(path)
        if logo_path.exists() and logo_path.is_file():
            if name is None:
                name = logo_path.stem.replace("-", "_")
            install_logo_path = self._config / logo_path.name

            if not install_logo_path.exists():
                shutil.copy(logo_path, install_logo_path)

            logger.info("Setting %s logo to %s", name, install_logo_path)
            _logo_mapping[name] = str(install_logo_path)
            self.catalogue.write_text(yaml.dump(dict(logos=_logo_mapping)))
            self.reload_config()
            if name != "default":
                return self._logos[name]
            else:
                return str(self._default)

        elif not logo_path.exists():
            warnings.warn(f"Logo file `{logo_path}` not found. Not setting logo.", stacklevel=2)
        elif not logo_path.is_file():
            warnings.warn(f"Logo path `{logo_path}` is a folder. Not setting logo.", stacklevel=2)
        return None

    def install_ouranos_logos(self, *, permitted: bool = False) -> None:
        """
        Fetch and install the Ouranos logo.

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
                    if not (self._config / file).exists():
                        logo_url = urllib.parse.urljoin(OURANOS_LOGOS_URL, file)
                        try:
                            urllib.request.urlretrieve(  # noqa: S310
                                audit_url(logo_url), self._config / file
                            )
                            self.set_logo(self._config / file)
                        except URLError as e:
                            logger.error(e)
                        except OSError as e:
                            msg = f"Error downloading or setting Ouranos logo: {e}"
                            logger.error(msg)

            if Path(self.default).stem == "figanos_logo":
                _default_ouranos_logo = (
                    self._config / "logo-ouranos-horizontal-couleur.svg"
                )
                warnings.warn(f"Setting default logo to {_default_ouranos_logo}.", stacklevel=2)
                self.set_logo(_default_ouranos_logo, name="default")
            self.reload_config()
            print(f"Ouranos logos installed at: {self._config}.")
        else:
            warnings.warn(
                "You have not indicated that you have permission to use the Ouranos logo. "
                "If you do, please set the `permitted` argument to `True`.", stacklevel=2
            )


def audit_url(url: str, context: str | None = None) -> str:
    """
    Check if the URL is well-formed.

    Raises
    ------
    URLError
        If the URL is not well-formed.
    """
    msg = ""
    result = urllib.parse.urlparse(url)
    if result.scheme == "http":
        msg = f"{context if context else ''} URL is not using secure HTTP: '{url}'".strip()
    if not all([result.scheme, result.netloc]):
        msg = f"{context if context else ''} URL is not well-formed: '{url}'".strip()

    if msg:
        logger.error(msg)
        raise URLError(msg)
    return url
