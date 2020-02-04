# -*- coding: utf-8 -*-

try:
    from unittest import mock
except ImportError:  # pragma: NO COVER
    import mock

import google.auth
import google.auth.credentials
import google.oauth2.credentials
import pytest

from pydata_google_auth import exceptions


TEST_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]


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


def test_load_user_credentials_raises_when_file_doesnt_exist(module_under_test):
    with pytest.raises(exceptions.PyDataCredentialsError):
        module_under_test.load_user_credentials("path/not/found.json")
