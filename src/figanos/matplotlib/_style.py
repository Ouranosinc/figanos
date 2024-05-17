from pathlib import Path


def get_mpl_styles() -> dict[str, Path]:
    """Get the available matplotlib styles and their paths as a dictionary."""
    files = sorted(Path(__file__).parent.joinpath("style").glob("*.mplstyle"))
    styles = {style.stem: style for style in files}
    return styles
