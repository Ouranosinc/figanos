"""Tests for `figanos` package."""

import pathlib
import pkgutil

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
    project = pkgutil.get_loader("figanos").get_filename()

    metadata = pathlib.Path(project).resolve().parent.joinpath("__init__.py")

    with open(metadata) as f:
        contents = f.read()
        assert """Sarah-Claude Bourdeau-Goulet""" in contents
        assert '__email__ = "bourdeau-goulet.sarah-claude@ouranos.ca"' in contents
        assert '__version__ = "0.3.1-dev.0"' in contents
