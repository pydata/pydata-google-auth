"""System tests for fetching Google API credentials."""

import google.auth

try:
    import mock
except ImportError:  # pragma: NO COVER
    from unittest import mock

from google.auth.exceptions import DefaultCredentialsError
import pytest
import requests


TEST_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]


def test_default_gets_valid_credentials():
    import pydata_google_auth

    credentials, _ = pydata_google_auth.default(TEST_SCOPES, auth_local_webserver=True)
    assert credentials.valid
    assert credentials.has_scopes(TEST_SCOPES)


def test_default_gets_user_credentials():
    import pydata_google_auth

    # Mock google.auth.default to fail, forcing user credentials.
    with mock.patch("google.auth.default", side_effect=DefaultCredentialsError()):
        credentials, _ = pydata_google_auth.default(
            TEST_SCOPES, auth_local_webserver=True
        )

    assert credentials.valid
    assert credentials.has_scopes(TEST_SCOPES)


def test_get_user_credentials_gets_valid_credentials():
    import pydata_google_auth

    credentials = pydata_google_auth.get_user_credentials(
        TEST_SCOPES, auth_local_webserver=True
    )

    assert credentials.valid
    assert credentials.has_scopes(TEST_SCOPES)


def test_get_user_credentials_noop_gets_valid_credentials():
    import pydata_google_auth
    import pydata_google_auth.cache

    credentials = pydata_google_auth.get_user_credentials(
        TEST_SCOPES,
        credentials_cache=pydata_google_auth.cache.NOOP,
        auth_local_webserver=True,
    )

    assert credentials.valid
    assert credentials.has_scopes(TEST_SCOPES)


def test_get_user_credentials_reauth_gets_valid_credentials():
    import pydata_google_auth
    import pydata_google_auth.cache

    credentials = pydata_google_auth.get_user_credentials(
        TEST_SCOPES,
        credentials_cache=pydata_google_auth.cache.REAUTH,
        auth_local_webserver=True,
    )

    assert credentials.valid
    assert credentials.has_scopes(TEST_SCOPES)
