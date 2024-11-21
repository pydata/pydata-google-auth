# -*- coding: utf-8 -*-

try:
    from unittest import mock
except ImportError:  # pragma: NO COVER
    import mock

import google.auth
import google.auth.credentials
import google.oauth2.credentials
import pytest

from google.oauth2 import service_account
from pydata_google_auth import exceptions
import pydata_google_auth.cache


TEST_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]


class FakeCredentials(object):
    @property
    def valid(self):
        return True


@pytest.fixture
def module_under_test():
    from pydata_google_auth import auth

    return auth


def test_default_returns_google_auth_credentials(monkeypatch, module_under_test):
    def mock_default_credentials(scopes=None, request=None):
        return (
            mock.create_autospec(google.auth.credentials.Credentials),
            "default-project",
        )

    monkeypatch.setattr(google.auth, "default", mock_default_credentials)

    credentials, project = module_under_test.default(TEST_SCOPES)
    assert project == "default-project"
    assert credentials is not None


def test_default_loads_user_credentials(monkeypatch, module_under_test):
    from pydata_google_auth import cache

    def mock_default_credentials(scopes=None, request=None):
        return (None, None)

    monkeypatch.setattr(google.auth, "default", mock_default_credentials)

    mock_cache = mock.create_autospec(cache.CredentialsCache)
    mock_user_credentials = mock.create_autospec(google.oauth2.credentials.Credentials)
    mock_cache.load.return_value = mock_user_credentials

    credentials, project = module_under_test.default(
        TEST_SCOPES, credentials_cache=mock_cache
    )
    assert project is None
    assert credentials is mock_user_credentials


def test_get_user_credentials_tries_colab_first(monkeypatch, module_under_test):
    colab_auth_module = mock.Mock()
    try_colab_auth_import = mock.Mock(return_value=colab_auth_module)
    monkeypatch.setattr(
        module_under_test, "try_colab_auth_import", try_colab_auth_import
    )
    default_credentials = mock.create_autospec(google.auth.credentials.Credentials)
    default_call_times = 0

    # Can't use a Mock because we want to check authenticate_user.
    def mock_default(scopes=None, request=None):
        nonlocal default_call_times
        default_call_times += 1

        # Make sure colab auth is called first.
        colab_auth_module.authenticate_user.assert_called_once_with()

        return (
            default_credentials,
            "colab-project",  # In reality, often None.
        )

    monkeypatch.setattr(google.auth, "default", mock_default)

    credentials = module_under_test.get_user_credentials(TEST_SCOPES)

    assert credentials is default_credentials
    assert default_call_times == 1


def test_get_user_credentials_skips_colab_if_no_colab(monkeypatch, module_under_test):
    try_colab_auth_import = mock.Mock(return_value=None)
    monkeypatch.setattr(
        module_under_test, "try_colab_auth_import", try_colab_auth_import
    )
    credentials_cache = mock.create_autospec(pydata_google_auth.cache.CredentialsCache)
    loaded_credentials = mock.Mock()
    credentials_cache.load.return_value = loaded_credentials

    credentials = module_under_test.get_user_credentials(
        TEST_SCOPES,
        credentials_cache=credentials_cache,
    )

    assert credentials is loaded_credentials


def test_load_service_account_credentials(monkeypatch, tmp_path, module_under_test):
    creds_path = str(tmp_path / "creds.json")
    with open(creds_path, "w") as stream:
        stream.write("{}")

    fake_creds = FakeCredentials()
    mock_service = mock.create_autospec(service_account.Credentials)
    mock_service.from_service_account_info.return_value = fake_creds
    monkeypatch.setattr(service_account, "Credentials", mock_service)

    creds = module_under_test.load_service_account_credentials(creds_path)
    assert creds is fake_creds


def test_load_user_credentials_raises_when_file_doesnt_exist(module_under_test):
    with pytest.raises(exceptions.PyDataCredentialsError):
        module_under_test.load_user_credentials("path/not/found.json")


def test_load_service_account_credentials_raises_when_file_doesnt_exist(
    module_under_test,
):
    with pytest.raises(exceptions.PyDataCredentialsError):
        module_under_test.load_service_account_credentials("path/not/found.json")
