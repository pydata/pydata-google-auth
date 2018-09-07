# -*- coding: utf-8 -*-

import json
import os.path

try:
    from unittest import mock
except ImportError:  # pragma: NO COVER
    import mock

import google.auth
import google.auth.credentials


TEST_SCOPES = ['https://www.googleapis.com/auth/cloud-platform']


def test_default_returns_google_auth_credentials(monkeypatch):
    from pydata_google_auth import auth

    def mock_default_credentials(scopes=None, request=None):
        return (
            mock.create_autospec(google.auth.credentials.Credentials),
            'default-project',
        )

    monkeypatch.setattr(google.auth, 'default', mock_default_credentials)

    credentials, project = auth.default(TEST_SCOPES)
    assert project == 'default-project'
    assert credentials is not None


def test_default_loads_user_credentials(monkeypatch):
    from pydata_google_auth import auth

    def mock_default_credentials(scopes=None, request=None):
        return (None, None)

    monkeypatch.setattr(google.auth, 'default', mock_default_credentials)
    mock_user_credentials = mock.create_autospec(
        google.auth.credentials.Credentials)

    def mock_load_credentials(project_id=None, credentials_path=None):
        return mock_user_credentials

    monkeypatch.setattr(
        auth,
        'load_user_credentials_from_file',
        mock_load_credentials)

    credentials, project = auth.default(TEST_SCOPES)
    assert project is None
    assert credentials is mock_user_credentials
