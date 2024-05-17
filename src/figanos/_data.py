from pathlib import Path


def data(*args) -> Path:
    return Path(__file__).parent / "data" / Path(*args)
