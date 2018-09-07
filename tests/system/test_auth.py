"""System tests for fetching Google API credentials."""

import google.auth
try:
    import mock
except ImportError:  # pragma: NO COVER
    from unittest import mock

from google.auth.exceptions import DefaultCredentialsError
import pytest
import requests


TEST_SCOPES = ['https://www.googleapis.com/auth/cloud-platform']


def test_default_gets_valid_credentials():
    import pydata_google_auth
    credentials, _ = pydata_google_auth.default(
        TEST_SCOPES, auth_local_webserver=True)
    assert credentials.valid
    assert credentials.has_scopes(TEST_SCOPES)


def test_default_gets_user_credentials():
    import pydata_google_auth
    # Mock google.auth.default to fail, forcing user credentials.
    with mock.patch('google.auth.default',
                    side_effect=DefaultCredentialsError()):
        credentials, _ = pydata_google_auth.default(
            TEST_SCOPES, auth_local_webserver=True)

    assert credentials.valid
    assert credentials.has_scopes(TEST_SCOPES)


def test_get_user_credentials_gets_valid_credentials():
    import pydata_google_auth
    credentials = pydata_google_auth.get_user_credentials(
        TEST_SCOPES, auth_local_webserver=True)

    assert credentials.valid
    assert credentials.has_scopes(TEST_SCOPES)


def test_get_user_credentials_from_file_gets_valid_credentials():
    import pydata_google_auth
    import pydata_google_auth.auth
    # Mock load_user_credentials_from_file to fail, forcing fresh credentials.
    with mock.patch(
            'pydata_google_auth.auth.load_user_credentials_from_file',
            return_value=None):
        credentials = pydata_google_auth.get_user_credentials(
            TEST_SCOPES, auth_local_webserver=True)

    assert credentials.valid
    assert credentials.has_scopes(TEST_SCOPES)
