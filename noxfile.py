"""Nox test automation configuration.

See: https://nox.readthedocs.io/en/latest/
"""

import os
import os.path
import shutil

import nox


latest_python = "3.7"
python_versions = ["2.7", "3.6", "3.7"]


@nox.session(python=latest_python)
def lint(session):
    """Run linters.
    Returns a failure if the linters find linting errors or sufficiently
    serious code quality issues.
    """

    session.install("black", "flake8")
    session.install("-e", ".")
    session.run("flake8", "pydata_google_auth")
    session.run("flake8", "tests")
    session.run("black", "--check", ".")


@nox.session(python=latest_python)
def blacken(session):
    """Run black.
    Format code to uniform standard.
    """
    session.install("black")
    session.run("black", ".")


@nox.session(python=python_versions)
def unit(session):
    session.install("mock", "pyfakefs", "pytest", "pytest-cov")
    session.install("-e", ".")
    session.run(
        "pytest",
        os.path.join(".", "tests", "unit"),
        "--quiet",
        "--cov=pydata_google_auth",
        "--cov=tests.unit",
        "--cov-report",
        "xml:/tmp/pytest-cov.xml",
        *session.posargs
    )


@nox.session(python=latest_python)
def cover(session):
    session.install("coverage", "pytest-cov")
    session.run("coverage", "report", "--show-missing", "--fail-under=40")
    session.run("coverage", "erase")


@nox.session(python=python_versions)
def system(session):
    session.install("mock", "pyfakefs", "pytest", "pytest-cov")
    session.install("-e", ".")

    # Skip local auth tests on Travis.
    additional_args = list(session.posargs)
    if "TRAVIS_BUILD_DIR" in os.environ:
        additional_args = additional_args + ["-m", "not local_auth"]

    session.run(
        "pytest",
        os.path.join(".", "tests", "system"),
        "--quiet",
        "--cov=pydata_google_auth",
        "--cov=tests.system",
        "--cov-report",
        "xml:/tmp/pytest-cov.xml",
        *additional_args
    )


@nox.session(python=latest_python)
def docs(session):
    """Build the docs."""

    session.install("sphinx", "sphinx_rtd_theme", "ipython")
    session.install("-e", ".")

    shutil.rmtree(os.path.join("docs", "source", "_build"), ignore_errors=True)
    session.run(
        "sphinx-build",
        "-W",  # warnings as errors
        "-T",  # show full traceback on exception
        "-N",  # no colors
        "-b",
        "html",
        "-d",
        os.path.join("docs", "source", "_build", "doctrees", ""),
        os.path.join("docs", "source", ""),
        os.path.join("docs", "source", "_build", "html", ""),
    )
