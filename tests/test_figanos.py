""""Tests for `figanos` package."""

import pkgutil
from pathlib import Path

import pytest

# import figanos


@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: https://doc.pytest.org/en/latest/explanation/fixtures.html
    """
    # import requests
    # return requests.get('https://github.com/audreyr/cookiecutter-pypackage')


def test_content(response):
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string
    pass


def test_imports():
    figanos = pkgutil.get_loader("figanos").get_filename()

    metadata = Path(figanos).resolve().parent.joinpath("__init__.py")

    with open(metadata) as f:
        contents = f.read()
        assert '__author__ = """Sarah-Claude Bourdeau-Goulet"""' in contents
        assert '__email__ = "bourdeau-goulet.sarah-claude@ouranos.ca"' in contents
        assert '__version__ = "0.1.0"' in contents
