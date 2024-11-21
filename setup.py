#!/usr/bin/env python
# -*- coding: utf-8 -*-

import versioneer
from setuptools import find_packages, setup

NAME = "pydata-google-auth"


# versioning
cmdclass = versioneer.get_cmdclass()


def readme():
    with open("README.rst") as f:
        return f.read()


INSTALL_REQUIRES = [
    "setuptools",
    "google-auth >=1.25.0, <3.0dev",
    "google-auth-oauthlib >=0.4.0",
]

setup(
    name=NAME,
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="PyData helpers for authenticating to Google APIs",
    long_description=readme(),
    license="BSD License",
    author="The PyData Development Team",
    author_email="pydata@googlegroups.com",
    url="https://github.com/pydata/pydata-google-auth",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: BSD License",
    ],
    keywords="data",
    install_requires=INSTALL_REQUIRES,
    packages=find_packages(exclude=["contrib", "docs", "tests*"]),
    test_suite="tests",
    python_requires=">=3.9",
)
