#!/usr/bin/env python

"""The setup script."""

from setuptools import find_packages, setup

with open("README.rst") as readme_file:
    readme = readme_file.read()

requirements = [
    "cartopy",
    "click>=8.0",
    "dask",
    "geopandas",
    "geoviews",
    "h5py",
    "holoviews",
    "jupyter",
    "matplotlib",
    "netCDF4",
    "notebook",
    "numpy",
    "pandas",
    "xarray",
    "xclim>=0.38",
    "pyyaml",
    "zarr",
    "seaborn",
]

test_requirements = ["pytest>=3"]

docs_requirements = [
    dependency for dependency in open("requirements_docs.txt").readlines()
]

dev_requirements = [
    dependency for dependency in open("requirements_dev.txt").readlines()
]

setup(
    author="Sarah-Claude Bourdeau-Goulet",
    author_email="bourdeau-goulet.sarah-claude@ouranos.ca",
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    description="Outils pour produire des graphiques informatifs sur les impacts des changements climatiques.",
    entry_points={
        "console_scripts": [
            "figanos=figanos.cli:main",
        ],
    },
    install_requires=requirements,
    license="Apache Software License 2.0",
    long_description=readme,
    long_description_content_type="text/x-rst",
    include_package_data=True,
    keywords="figanos",
    name="figanos",
    packages=find_packages(include=["figanos", "figanos.*"]),
    test_suite="tests",
    tests_require=test_requirements,
    extras_require={
        "docs": docs_requirements,
        "dev": dev_requirements,
    },
    project_urls={
        "Source": "https://github.com/Ouranosinc/figanos",
        "Issue tracker": "https://github.com/Ouranosinc/figanos/issues",
        "About Ouranos": "https://www.ouranos.ca/en/",
    },
    version="0.2.0",
    zip_safe=False,
)
