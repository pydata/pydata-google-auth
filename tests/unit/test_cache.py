"""Test module for pydata_google_auth.cache"""

import json
import os
import os.path

import pytest

import google.oauth2.credentials
from six.moves import reload_module


@pytest.fixture
def module_under_test():
    from pydata_google_auth import cache

    return cache


def test_import_unwriteable_fs(module_under_test, monkeypatch):
    """Test import with an unwritable filesystem.

    See: https://github.com/pydata/pydata-google-auth/issues/10
    """

    def raise_unwriteable(path):
        raise PermissionError()

    monkeypatch.setattr(os.path, "exists", lambda _: False)
    monkeypatch.setattr(os, "makedirs", raise_unwriteable)

    reload_module(module_under_test)

    assert module_under_test.NOOP is not None


def test__save_user_account_credentials_wo_directory(module_under_test, fs):
    """Directories should be created if they don't exist."""

    credentials = google.oauth2.credentials.Credentials(
        token="access_token",
        refresh_token="refresh_token",
        id_token="id_token",
        token_uri="token_uri",
        client_id="client_id",
        client_secret="client_secret",
        scopes=["scopes"],
    )
    path = "/home/username/.config/pydata/pydata_google_credentials.json"
    assert not os.path.exists("/home/username/.config/pydata/")

    module_under_test._save_user_account_credentials(credentials, path)

    with open(path) as fp:
        serialized_data = json.load(fp)
    assert serialized_data["refresh_token"] == "refresh_token"


def test_ReadWriteCredentialsCache_sets_path(module_under_test):
    """ReadWriteCredentialsCache ctor should respect dirname and filename.

    See: https://github.com/pydata/pydata-google-auth/issues/16
    """
    cache = module_under_test.ReadWriteCredentialsCache(
        dirname="dirtest", filename="filetest.json"
    )
    path = os.path.normpath(cache._path)
    parts = path.split(os.sep)
    assert parts[-2] == "dirtest"
    assert parts[-1] == "filetest.json"


def test_WriteOnlyCredentialsCache_sets_path(module_under_test):
    """ReadWriteCredentialsCache ctor should respect dirname and filename.

    See: https://github.com/pydata/pydata-google-auth/issues/16
    """
    cache = module_under_test.WriteOnlyCredentialsCache(
        dirname="dirtest", filename="filetest.json"
    )
    path = os.path.normpath(cache._path)
    parts = path.split(os.sep)
    assert parts[-2] == "dirtest"
    assert parts[-1] == "filetest.json"
