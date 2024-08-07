"""Tests for `figanos` package."""

import pathlib
from importlib.util import find_spec

import pytest

import figanos  # noqa: F401


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


def test_package_metadata():
    """Test the package metadata."""
    project = find_spec("figanos").submodule_search_locations[0]

    metadata = pathlib.Path(project).resolve().joinpath("__init__.py")

    with open(metadata) as f:
        contents = f.read()
        assert """Sarah-Claude Bourdeau-Goulet""" in contents
        assert '__email__ = "bourdeau-goulet.sarah-claude@ouranos.ca"' in contents
        assert '__version__ = "0.3.1-dev.10"' in contents
