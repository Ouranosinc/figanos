from pathlib import Path


__all__ = ["data"]


def data(*args) -> Path:
    """Return the path to the data directory."""
    return Path(__file__).parent / "data" / Path(*args)
