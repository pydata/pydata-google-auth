"""Private module for fetching Google API credentials."""

import logging

import google.auth
import google.auth.exceptions
import google.oauth2.credentials
from google_auth_oauthlib import flow
import oauthlib.oauth2.rfc6749.errors
import google.auth.transport.requests

from pydata_google_auth import exceptions
from pydata_google_auth import cache


logger = logging.getLogger(__name__)

CLIENT_ID = "262006177488-3425ks60hkk80fssi9vpohv88g6q1iqd.apps.googleusercontent.com"
CLIENT_SECRET = "JSF-iczmzEgbTR-XK-2xaWAc"


def default(
    scopes,
    client_id=None,
    client_secret=None,
    credentials_cache=cache.READ_WRITE,
    auth_local_webserver=False,
):
    """
    Get credentials and default project for accessing Google APIs.

    This method first attempts to get credentials via the
    :func:`google.auth.default` function. If it is unable to get valid
    credentials, it then attempts to get user account credentials via the
    :func:`pydata_google_auth.get_user_credentials` function.

    Parameters
    ----------
    scopes : list[str]
        A list of scopes to use when authenticating to Google APIs. See the
        `list of OAuth 2.0 scopes for Google APIs
        <https://developers.google.com/identity/protocols/googlescopes>`_.
    client_id : str, optional
        The client secrets to use when prompting for user credentials.
        Defaults to a client ID associated with pydata-google-auth.

        If you are a tool or library author, you must override the default
        value with a client ID associated with your project. Per the `Google
        APIs terms of service <https://developers.google.com/terms/>`_, you
        must not mask your API client's identity when using Google APIs.
    client_secret : str, optional
        The client secrets to use when prompting for user credentials.
        Defaults to a client secret associated with pydata-google-auth.

        If you are a tool or library author, you must override the default
        value with a client secret associated with your project. Per the
        `Google APIs terms of service
        <https://developers.google.com/terms/>`_, you must not mask your API
        client's identity when using Google APIs.
    credentials_cache : pydata_google_auth.cache.CredentialsCache, optional
        An object responsible for loading and saving user credentials.

        By default, pydata-google-auth reads and writes credentials in
        ``$HOME/.config/pydata/pydata_google_credentials.json`` or
        ``$APPDATA/.config/pydata/pydata_google_credentials.json`` on
        Windows.
    auth_local_webserver : bool, optional
        Use a local webserver for the user authentication
        :class:`google_auth_oauthlib.flow.InstalledAppFlow`. Defaults to
        ``False``, which requests a token via the console.

    Returns
    -------
    credentials, project_id : tuple[google.auth.credentials.Credentials, str or None]
        credentials : OAuth 2.0 credentials for accessing Google APIs

        project_id : A default Google developer project ID, if one could be determined
        from the credentials. For example, this returns the project ID
        associated with a service account when using a service account key
        file. It returns None when using user-based credentials.

    Raises
    ------
    pydata_google_auth.exceptions.PyDataCredentialsError
        If unable to get valid credentials.
    """
    # Try to retrieve Application Default Credentials
    credentials, default_project = get_application_default_credentials(scopes)

    if credentials and credentials.valid:
        return credentials, default_project

    credentials = get_user_credentials(
        scopes,
        client_id=client_id,
        client_secret=client_secret,
        credentials_cache=credentials_cache,
        auth_local_webserver=auth_local_webserver,
    )

    if not credentials or not credentials.valid:
        raise exceptions.PyDataCredentialsError("Could not get any valid credentials.")

    return credentials, None


def get_application_default_credentials(scopes):
    """
    This method tries to retrieve the "default application credentials".
    This could be useful for running code on Google Cloud Platform.

    Parameters
    ----------
    project_id (str, optional): Override the default project ID.

    Returns
    -------
    - GoogleCredentials,
        If the default application credentials can be retrieved
        from the environment. The retrieved credentials should also
        have access to the project (project_id) on BigQuery.
    - OR None,
        If default application credentials can not be retrieved
        from the environment. Or, the retrieved credentials do not
        have access to the project (project_id) on BigQuery.
    """

    try:
        credentials, project = google.auth.default(scopes=scopes)
    except (google.auth.exceptions.DefaultCredentialsError, IOError) as exc:
        logger.debug("Error getting default credentials: {}".format(str(exc)))
        return None, None

    if credentials and not credentials.valid:
        request = google.auth.transport.requests.Request()
        try:
            credentials.refresh(request)
        except google.auth.exceptions.RefreshError:
            # Sometimes (such as on Travis) google-auth returns GCE
            # credentials, but fetching the token for those credentials doesn't
            # actually work. See:
            # https://github.com/googleapis/google-auth-library-python/issues/287
            return None, None

    return credentials, project


def get_user_credentials(
    scopes,
    client_id=None,
    client_secret=None,
    credentials_cache=cache.READ_WRITE,
    auth_local_webserver=False,
):
    """
    Gets user account credentials.

    This function authenticates using user credentials, either loading saved
    credentials from the cache or by going through the OAuth 2.0 flow.

    The default read-write cache attempts to read credentials from a file on
    disk. If these credentials are not found or are invalid, it begins an
    OAuth 2.0 flow to get credentials. You'll open a browser window asking
    for you to authenticate to your Google account using the product name
    ``PyData Google Auth``. The permissions it requests correspond to the
    scopes you've provided.

    Additional information on the user credentails authentication mechanism
    can be found `here
    <https://developers.google.com/identity/protocols/OAuth2#clientside/>`__.

    Parameters
    ----------
    scopes : list[str]
        A list of scopes to use when authenticating to Google APIs. See the
        `list of OAuth 2.0 scopes for Google APIs
        <https://developers.google.com/identity/protocols/googlescopes>`_.
    client_id : str, optional
        The client secrets to use when prompting for user credentials.
        Defaults to a client ID associated with pydata-google-auth.

        If you are a tool or library author, you must override the default
        value with a client ID associated with your project. Per the `Google
        APIs terms of service <https://developers.google.com/terms/>`_, you
        must not mask your API client's identity when using Google APIs.
    client_secret : str, optional
        The client secrets to use when prompting for user credentials.
        Defaults to a client secret associated with pydata-google-auth.

        If you are a tool or library author, you must override the default
        value with a client secret associated with your project. Per the
        `Google APIs terms of service
        <https://developers.google.com/terms/>`_, you must not mask your API
        client's identity when using Google APIs.
    credentials_cache : pydata_google_auth.cache.CredentialsCache, optional
        An object responsible for loading and saving user credentials.

        By default, pydata-google-auth reads and writes credentials in
        ``$HOME/.config/pydata/pydata_google_credentials.json`` or
        ``$APPDATA/.config/pydata/pydata_google_credentials.json`` on
        Windows.
    auth_local_webserver : bool, optional
        Use a local webserver for the user authentication
        :class:`google_auth_oauthlib.flow.InstalledAppFlow`. Defaults to
        ``False``, which requests a token via the console.

    Returns
    -------
    credentials : google.oauth2.credentials.Credentials
        Credentials for the user, with the requested scopes.

    Raises
    ------
    pydata_google_auth.exceptions.PyDataCredentialsError
        If unable to get valid user credentials.
    """
    # Use None as default for client_id and client_secret so that the values
    # aren't included in the docs. A string of bytes isn't useful for the
    # documentation and might encourage the values to be used outside of this
    # library.
    if client_id is None:
        client_id = CLIENT_ID
    if client_secret is None:
        client_secret = CLIENT_SECRET

    credentials = credentials_cache.load()

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://accounts.google.com/o/oauth2/token",
        }
    }

    if credentials is None:
        app_flow = flow.InstalledAppFlow.from_client_config(
            client_config, scopes=scopes
        )

        try:
            if auth_local_webserver:
                credentials = app_flow.run_local_server()
            else:
                credentials = app_flow.run_console()
        except oauthlib.oauth2.rfc6749.errors.OAuth2Error as exc:
            raise exceptions.PyDataCredentialsError(
                "Unable to get valid credentials: {}".format(exc)
            )

        credentials_cache.save(credentials)

    if credentials and not credentials.valid:
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)

    return credentials
