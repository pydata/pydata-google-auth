# -*- coding: utf-8 -*-

try:
    from unittest import mock
except ImportError:  # pragma: NO COVER
    import mock

import builtins
import urllib.parse
import warnings

import google.auth
import google.auth.credentials
import google.oauth2.credentials
from google_auth_oauthlib import flow as oauthlib_flow
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


@pytest.mark.parametrize(
    "use_local_webserver, extra_kwargs",
    [
        pytest.param(True, {}, id="local_webserver"),
        pytest.param(False, {}, id="default_webapp"),
        pytest.param(
            False,
            {
                "client_id": "custom-client-id",
                "client_secret": "custom-client-secret",
                "redirect_uri": "https://org.example.com/oauth",
            },
            id="custom_redirect_uri",
        ),
    ],
)
def test_get_user_credentials_enables_pkce(
    monkeypatch, module_under_test, use_local_webserver, extra_kwargs
):
    monkeypatch.setattr(module_under_test, "try_colab_auth_import", lambda: None)
    credentials_cache = mock.create_autospec(pydata_google_auth.cache.CredentialsCache)
    credentials_cache.load.return_value = None

    captured_flow = None
    fake_creds = FakeCredentials()

    def capture_flow(app_flow, **kwargs):
        nonlocal captured_flow
        captured_flow = app_flow
        return fake_creds

    monkeypatch.setattr(module_under_test._webserver, "run_local_server", capture_flow)
    monkeypatch.setattr(module_under_test, "_run_webapp", capture_flow)

    with mock.patch.object(
        module_under_test.flow.InstalledAppFlow,
        "from_client_config",
        wraps=oauthlib_flow.InstalledAppFlow.from_client_config,
    ) as from_client_config:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            credentials = module_under_test.get_user_credentials(
                TEST_SCOPES,
                credentials_cache=credentials_cache,
                use_local_webserver=use_local_webserver,
                **extra_kwargs,
            )

    assert credentials is fake_creds
    assert from_client_config.call_count == 1
    assert from_client_config.call_args.kwargs["autogenerate_code_verifier"] is True
    assert captured_flow.autogenerate_code_verifier is True


def test__run_webapp_sends_pkce_challenge_and_verifier(
    monkeypatch, capsys, module_under_test
):
    monkeypatch.setattr(builtins, "input", lambda _: "fake-auth-code")
    fake_creds = FakeCredentials()
    fetch_token_kwargs = {}

    client_config = {
        "installed": {
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
            "redirect_uris": [module_under_test.WEBAPP_REDIRECT_URI],
            "auth_uri": module_under_test.GOOGLE_AUTH_URI,
            "token_uri": module_under_test.GOOGLE_TOKEN_URI,
        }
    }
    app_flow = oauthlib_flow.InstalledAppFlow.from_client_config(
        client_config, scopes=TEST_SCOPES, autogenerate_code_verifier=True
    )

    def fake_fetch_token(token_url, **token_kwargs):
        fetch_token_kwargs.update(token_kwargs)
        return {"access_token": "fake-token"}

    monkeypatch.setattr(app_flow.oauth2session, "fetch_token", fake_fetch_token)
    monkeypatch.setattr(
        oauthlib_flow.Flow,
        "credentials",
        property(lambda self: fake_creds),
    )

    credentials = module_under_test._run_webapp(
        app_flow,
        redirect_uri=module_under_test.WEBAPP_REDIRECT_URI,
        **module_under_test.AUTH_URI_KWARGS,
    )

    assert credentials is fake_creds
    assert app_flow.code_verifier is not None
    assert len(app_flow.code_verifier) == 128
    assert fetch_token_kwargs["code"] == "fake-auth-code"
    assert fetch_token_kwargs["code_verifier"] == app_flow.code_verifier

    printed = capsys.readouterr().out
    auth_url = printed.strip().split(": ", 1)[1]
    query = urllib.parse.parse_qs(urllib.parse.urlparse(auth_url).query)
    assert query["code_challenge_method"] == ["S256"]
    assert "code_challenge" in query


@pytest.mark.parametrize(
    "has_cached_credentials, use_local_webserver, extra_kwargs, expect_warning",
    [
        pytest.param(False, False, {}, True, id="uncached_default_webapp"),
        pytest.param(True, False, {}, False, id="cached_default_webapp"),
        pytest.param(
            False,
            False,
            {
                "client_id": "custom-client-id",
                "client_secret": "custom-client-secret",
                "redirect_uri": "https://org.example.com/oauth",
            },
            False,
            id="custom_redirect_uri",
        ),
        pytest.param(False, True, {}, False, id="local_webserver"),
    ],
)
def test_get_user_credentials_webapp_deprecation_warning(
    monkeypatch,
    module_under_test,
    has_cached_credentials,
    use_local_webserver,
    extra_kwargs,
    expect_warning,
):
    monkeypatch.setattr(module_under_test, "try_colab_auth_import", lambda: None)
    credentials_cache = mock.create_autospec(pydata_google_auth.cache.CredentialsCache)
    fake_creds = FakeCredentials()
    credentials_cache.load.return_value = fake_creds if has_cached_credentials else None
    monkeypatch.setattr(
        module_under_test._webserver,
        "run_local_server",
        mock.Mock(return_value=fake_creds),
    )
    monkeypatch.setattr(
        module_under_test, "_run_webapp", mock.Mock(return_value=fake_creds)
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        module_under_test.get_user_credentials(
            TEST_SCOPES,
            credentials_cache=credentials_cache,
            use_local_webserver=use_local_webserver,
            **extra_kwargs,
        )

    deprecation_warnings = [
        w for w in caught if issubclass(w.category, DeprecationWarning)
    ]
    if expect_warning:
        assert len(deprecation_warnings) == 1
        assert "default copy-paste authentication flow" in str(
            deprecation_warnings[0].message
        )
    else:
        assert deprecation_warnings == []


@pytest.mark.parametrize(
    "initial_uri, arg_uri, expected_uri",
    [
        pytest.param(
            "https://org.example.com/oauth",
            None,
            "https://org.example.com/oauth",
            id="existing_flow_uri",
        ),
        pytest.param(
            None,
            "https://override.example.com/oauth",
            "https://override.example.com/oauth",
            id="explicit_redirect_uri",
        ),
    ],
)
def test__run_webapp_sets_redirect_uri(
    monkeypatch, module_under_test, initial_uri, arg_uri, expected_uri
):
    monkeypatch.setattr(builtins, "input", lambda _: "fake-auth-code")
    fake_creds = FakeCredentials()
    mock_flow = mock.Mock(redirect_uri=initial_uri)
    mock_flow.authorization_url.return_value = ("https://example.com/auth", "state")
    mock_flow.credentials = fake_creds

    credentials = module_under_test._run_webapp(mock_flow, redirect_uri=arg_uri)

    assert credentials is fake_creds
    assert mock_flow.redirect_uri == expected_uri
    mock_flow.fetch_token.assert_called_once_with(code="fake-auth-code")


def test__run_webapp_raises_without_redirect_uri(module_under_test):
    mock_flow = mock.Mock(redirect_uri=None)
    with pytest.raises(exceptions.PyDataCredentialsError, match="redirect_uri"):
        module_under_test._run_webapp(mock_flow)
