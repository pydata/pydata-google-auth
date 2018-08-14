"""Shared pytest fixtures for system tests."""

import os

import pytest


@pytest.fixture(scope='session')
def project_id():
    return os.environ.get('GOOGLE_CLOUD_PROJECT')  # noqa
