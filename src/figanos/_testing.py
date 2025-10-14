from collections.abc import Callable
from functools import wraps
from typing import IO


__all__ = ["pitou"]


def pitou():
    """Return a Pooch instance for the figanos testing data."""
    from figanos import __version__ as __figanos_version__

    try:
        import pooch
    except ImportError as err:
        raise ImportError(
            "The 'pooch' package is required to fetch the figanos testing data. "
            "You can install it using 'pip install pooch' or 'pip install \"figanos[docs]\"'."
        ) from err

    _pitou = pooch.Pooch(
        path=pooch.os_cache("figanos"),
        base_url="https://raw.githubusercontent.com/Ouranosinc/figanos/main/src/figanos/data/test_data/",
        registry={
            "hatchmap-ens_stats.nc": "fc52d0551747fa0a7153f1ecfebf3e697993590c6c7c4c6a6f9f32700df9d32d",
            "hatchmap-inf_5.nc": "8f22522dc153d8d347bdf97bf85e49d08a5ecbc61c64372e713a0d25638e48ac",
            "hatchmap-sup_8.nc": "a409ebbd6ce3c0ca319f676cc21677ba500983b80ff65a64ef3d467008db824a",
        },
    )

    # Add a custom fetch method to the Pooch instance
    # Needed to address: https://github.com/readthedocs/readthedocs.org/issues/11763
    _pitou.fetch_diversion = _pitou.fetch

    # Overload the fetch method to add user-agent headers
    @wraps(_pitou.fetch_diversion)
    def _fetch(*args: str, **kwargs: bool | Callable) -> str:
        def _downloader(
            url: str,
            output_file: str | IO,
            poocher: pooch.Pooch,
            check_only: bool | None = False,
        ) -> None:
            """Download the file from the URL and save it to the save_path."""
            headers = {"User-Agent": f"figanos ({__figanos_version__})"}
            downloader = pooch.HTTPDownloader(headers=headers)
            return downloader(url, output_file, poocher, check_only=check_only)

        # default to our http/s downloader with user-agent headers
        kwargs.setdefault("downloader", _downloader)
        return _pitou.fetch_diversion(*args, **kwargs)

    # Replace the fetch method with the custom fetch method
    _pitou.fetch = _fetch

    return _pitou
