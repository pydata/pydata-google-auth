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
from pydata_google_auth import _webserver


logger = logging.getLogger(__name__)

CLIENT_ID = "262006177488-3425ks60hkk80fssi9vpohv88g6q1iqd.apps.googleusercontent.com"
CLIENT_SECRET = "JSF-iczmzEgbTR-XK-2xaWAc"
GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"


def default(
    scopes,
    client_id=None,
    client_secret=None,
    credentials_cache=cache.READ_WRITE,
    use_local_webserver=False,
    auth_local_webserver=None,
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
    use_local_webserver : bool, optional
        Use a local webserver for the user authentication
        :class:`google_auth_oauthlib.flow.InstalledAppFlow`. Binds a
        webserver to an open port on ``localhost`` between 8080 and 8089,
        inclusive, to receive authentication token. If not set, defaults to
        ``False``, which requests a token via the console.
    auth_local_webserver : deprecated
        Use the ``use_local_webserver`` parameter instead.

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
    if auth_local_webserver is not None:
        use_local_webserver = auth_local_webserver

    # Try to retrieve Application Default Credentials
    credentials, default_project = get_application_default_credentials(scopes)

    if credentials and credentials.valid:
        return credentials, default_project

    credentials = get_user_credentials(
        scopes,
        client_id=client_id,
        client_secret=client_secret,
        credentials_cache=credentials_cache,
        use_local_webserver=use_local_webserver,
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
    use_local_webserver=False,
    auth_local_webserver=None,
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
    use_local_webserver : bool, optional
        Use a local webserver for the user authentication
        :class:`google_auth_oauthlib.flow.InstalledAppFlow`. Binds a
        webserver to an open port on ``localhost`` between 8080 and 8089,
        inclusive, to receive authentication token. If not set, defaults to
        ``False``, which requests a token via the console.
    auth_local_webserver : deprecated
        Use the ``use_local_webserver`` parameter instead.

    Returns
    -------
    credentials : google.oauth2.credentials.Credentials
        Credentials for the user, with the requested scopes.

    Raises
    ------
    pydata_google_auth.exceptions.PyDataCredentialsError
        If unable to get valid user credentials.
    """
    if auth_local_webserver is not None:
        use_local_webserver = auth_local_webserver

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
            "auth_uri": GOOGLE_AUTH_URI,
            "token_uri": GOOGLE_TOKEN_URI,
        }
    }

    if credentials is None:
        app_flow = flow.InstalledAppFlow.from_client_config(
            client_config, scopes=scopes
        )

        try:
            if use_local_webserver:
                credentials = _webserver.run_local_server(app_flow)
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


def save_user_credentials(
    scopes, path, client_id=None, client_secret=None, use_local_webserver=False
):
    """
    Gets user account credentials and saves them to a JSON file at ``path``.

    This function authenticates using user credentials by going through the
    OAuth 2.0 flow.

    Parameters
    ----------

    scopes : list[str]
        A list of scopes to use when authenticating to Google APIs. See the
        `list of OAuth 2.0 scopes for Google APIs
        <https://developers.google.com/identity/protocols/googlescopes>`_.
    path : str
        Path to save credentials JSON file.
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
    use_local_webserver : bool, optional
        Use a local webserver for the user authentication
        :class:`google_auth_oauthlib.flow.InstalledAppFlow`. Binds a
        webserver to an open port on ``localhost`` between 8080 and 8089,
        inclusive, to receive authentication token. If not set, defaults to
        ``False``, which requests a token via the console.

    Returns
    -------

    None

    Raises
    ------
    pydata_google_auth.exceptions.PyDataCredentialsError
        If unable to get valid user credentials.

    Examples
    --------

    Get credentials for Google Cloud Platform and save them to
    ``/home/username/keys/google-credentials.json``.

    .. code-block:: python

       pydata_google_auth.save_user_credentials(
           ["https://www.googleapis.com/auth/cloud-platform"],
           "/home/username/keys/google-credentials.json",
           use_local_webserver=True,
       )

    Set the ``GOOGLE_APPLICATION_CREDENTIALS`` environment variable to use
    these credentials with Google Application Default Credentials.

    .. code-block:: bash

       export GOOGLE_APPLICATION_CREDENTIALS='/home/username/keys/google-credentials.json'
    """
    credentials = get_user_credentials(
        scopes,
        client_id=client_id,
        client_secret=client_secret,
        credentials_cache=cache.NOOP,
        use_local_webserver=use_local_webserver,
    )
    cache._save_user_account_credentials(credentials, path)


def load_user_credentials(path):
    """
    Gets user account credentials from JSON file at ``path``.

    Parameters
    ----------
    path : str
        Path to credentials JSON file.

    Returns
    -------

    google.auth.credentials.Credentials

    Raises
    ------
    pydata_google_auth.exceptions.PyDataCredentialsError
        If unable to load user credentials.

    Examples
    --------

    Load credentials and use them to construct a BigQuery client.

    .. code-block:: python

       import pydata_google_auth
       import google.cloud.bigquery

       credentials = pydata_google_auth.load_user_credentials(
           "/home/username/keys/google-credentials.json",
       )
       client = google.cloud.bigquery.BigQueryClient(
           credentials=credentials,
           project="my-project-id"
       )
    """
    credentials = cache._load_user_credentials_from_file(path)
    if not credentials:
        raise exceptions.PyDataCredentialsError("Could not load credentials.")
    return credentials


def load_service_account_credentials(path, scopes=None):
    """
    Gets service account credentials from JSON file at ``path``.

    Parameters
    ----------
    path : str
        Path to credentials JSON file.
    scopes : list[str], optional
        A list of scopes to use when authenticating to Google APIs. See the
        `list of OAuth 2.0 scopes for Google APIs
        <https://developers.google.com/identity/protocols/googlescopes>`_.

    Returns
    -------

    google.oauth2.service_account.Credentials

    Raises
    ------
    pydata_google_auth.exceptions.PyDataCredentialsError
        If unable to load service credentials.

    Examples
    --------

    Load credentials and use them to construct a BigQuery client.

    .. code-block:: python

       import pydata_google_auth
       import google.cloud.bigquery

       credentials = pydata_google_auth.load_service_account_credentials(
           "/home/username/keys/google-service-account-credentials.json",
       )
       client = google.cloud.bigquery.BigQueryClient(
           credentials=credentials,
           project=credentials.project_id
       )
    """

    credentials = cache._load_service_account_credentials_from_file(path, scopes=scopes)
    if not credentials:
        raise exceptions.PyDataCredentialsError("Could not load credentials.")
    return credentials
