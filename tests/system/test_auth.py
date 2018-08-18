"""System tests for fetching Google BigQuery credentials."""

import google.auth
try:
    import mock
except ImportError:  # pragma: NO COVER
    from unittest import mock
import pytest
import requests

from pydata_google_auth import auth


TEST_CLIENT_ID = (
    '262006177488-3425ks60hkk80fssi9vpohv88g6q1iqd.apps.googleusercontent.com'
)
TEST_CLIENT_SECRET = 'JSF-iczmzEgbTR-XK-2xaWAc'
TEST_SCOPES = ['https://www.googleapis.com/auth/userinfo.email']


def _check_if_can_get_correct_default_credentials():
    # Checks if "Application Default Credentials" can be fetched
    # from the environment the tests are running in.
    # See https://github.com/pandas-dev/pandas/issues/13577
    from google.auth.exceptions import DefaultCredentialsError

    try:
        credentials, project = google.auth.default(TEST_SCOPES)
    except (DefaultCredentialsError, IOError):
        return False

    return _try_credentials(credentials, project) is None


def test_should_be_able_to_get_valid_credentials():
    credentials, _ = auth.default(
        TEST_SCOPES,
        TEST_CLIENT_ID,
        TEST_CLIENT_SECRET,
        'pydata_google_auth',
        'test_credentials.dat')
    assert credentials.valid


def test_get_application_default_credentials_does_not_throw_error():
    if _check_if_can_get_correct_default_credentials():
        # Can get real credentials, so mock it out to fail.
        from google.auth.exceptions import DefaultCredentialsError
        with mock.patch('google.auth.default',
                        side_effect=DefaultCredentialsError()):
            credentials, _ = auth.get_application_default_credentials()
    else:
        credentials, _ = auth.get_application_default_credentials()
    assert credentials is None


def test_get_application_default_credentials_returns_credentials():
    if not _check_if_can_get_correct_default_credentials():
        pytest.skip("Cannot get default_credentials "
                    "from the environment!")
    from google.auth.credentials import Credentials
    credentials, default_project = auth.get_application_default_credentials()

    assert isinstance(credentials, Credentials)
    assert default_project is not None


@pytest.mark.local_auth
def test_get_user_account_credentials_bad_file_returns_credentials():
    from google.auth.credentials import Credentials
    with mock.patch('__main__.open', side_effect=IOError()):
        credentials = auth.get_user_account_credentials(
            TEST_SCOPES,
            TEST_CLIENT_ID,
            TEST_CLIENT_SECRET,
            'pydata_google_auth',
            'test_credentials.dat')
    assert isinstance(credentials, Credentials)


@pytest.mark.local_auth
def test_get_user_account_credentials_returns_credentials(project_id):
    from google.auth.credentials import Credentials
    credentials = auth.get_user_account_credentials(
        project_id=project_id,
        auth_local_webserver=True)
    assert isinstance(credentials, Credentials)


@pytest.mark.local_auth
def test_get_user_account_credentials_reauth_returns_credentials(project_id):
    from google.auth.credentials import Credentials
    credentials = auth.get_user_account_credentials(
        project_id=project_id,
        auth_local_webserver=True,
        reauth=True)
    assert isinstance(credentials, Credentials)
