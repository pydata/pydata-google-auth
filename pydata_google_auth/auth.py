"""Private module for fetching Google BigQuery credentials."""

import json
import logging
import os
import os.path

import pydata_google_auth.exceptions


logger = logging.getLogger(__name__)


def default(
        scopes,
        client_id,
        client_secret,
        credentials_dirname,
        credentials_filename,
        project_id=None,
        auth_local_webserver=False,
        try_credentials=None):
    if try_credentials is None:
        def try_credentials(credentials, project_id):
            return credentials, project_id

    return get_credentials(
        scopes,
        client_id,
        client_secret,
        credentials_dirname,
        credentials_filename,
        project_id=project_id,
        auth_local_webserver=auth_local_webserver,
        try_credentials=try_credentials)


def get_credentials(
        scopes,
        client_id,
        client_secret,
        credentials_dirname,
        credentials_filename,
        try_credentials,
        project_id=None, reauth=False,
        auth_local_webserver=False):
    # Try to retrieve Application Default Credentials
    credentials, default_project = get_application_default_credentials(
        scopes, project_id=project_id, try_credentials=try_credentials)

    if credentials:
        return credentials, default_project

    credentials = get_user_account_credentials(
        scopes,
        client_id,
        client_secret,
        credentials_dirname,
        credentials_filename,
        project_id=project_id,
        reauth=reauth,
        auth_local_webserver=auth_local_webserver,
        try_credentials=try_credentials)
    return credentials, project_id


def get_application_default_credentials(
        scopes, try_credentials, project_id=None):
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
    import google.auth
    from google.auth.exceptions import DefaultCredentialsError

    try:
        credentials, default_project = google.auth.default(scopes=scopes)
    except (DefaultCredentialsError, IOError):
        return None, None

    # Even though we now have credentials, check that the credentials can be
    # used with BigQuery. For example, we could be running on a GCE instance
    # that does not allow the BigQuery scopes.
    billing_project = project_id or default_project
    return try_credentials(credentials, billing_project)


def get_user_account_credentials(
        scopes,
        client_id,
        client_secret,
        credentials_dirname,
        credentials_filename,
        project_id=None, reauth=False, auth_local_webserver=False,
        credentials_path=None):
    """Gets user account credentials.

    This method authenticates using user credentials, either loading saved
    credentials from a file or by going through the OAuth flow.

    Parameters
    ----------
    None

    Returns
    -------
    GoogleCredentials : credentials
        Credentials for the user with BigQuery access.
    """
    from google_auth_oauthlib.flow import InstalledAppFlow
    from oauthlib.oauth2.rfc6749.errors import OAuth2Error

    # Use the default credentials location under ~/.config and the
    # equivalent directory on windows if the user has not specified a
    # credentials path.
    if not credentials_path:
        credentials_path = get_default_credentials_path(
            credentials_dirname,
            credentials_filename)

        # Previously, pandas-gbq saved user account credentials in the
        # current working directory. If the bigquery_credentials.dat file
        # exists in the current working directory, move the credentials to
        # the new default location.
        if os.path.isfile('bigquery_credentials.dat'):
            os.rename(credentials_filename, credentials_path)

    credentials = load_user_account_credentials(
        project_id=project_id, credentials_path=credentials_path)

    client_config = {
        'installed': {
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uris': ['urn:ietf:wg:oauth:2.0:oob'],
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://accounts.google.com/o/oauth2/token',
        }
    }

    if credentials is None or reauth:
        app_flow = InstalledAppFlow.from_client_config(
            client_config, scopes=scopes)

        try:
            if auth_local_webserver:
                credentials = app_flow.run_local_server()
            else:
                credentials = app_flow.run_console()
        except OAuth2Error as ex:
            raise pydata_google_auth.exceptions.AccessDenied(
                "Unable to get valid credentials: {0}".format(ex))

        save_user_account_credentials(credentials, credentials_path)

    return credentials


def load_user_account_credentials(
        try_credentials, project_id=None, credentials_path=None):
    """
    Loads user account credentials from a local file.

    .. versionadded 0.2.0

    Parameters
    ----------
    None

    Returns
    -------
    - GoogleCredentials,
        If the credentials can loaded. The retrieved credentials should
        also have access to the project (project_id) on BigQuery.
    - OR None,
        If credentials can not be loaded from a file. Or, the retrieved
        credentials do not have access to the project (project_id)
        on BigQuery.
    """
    import google.auth.transport.requests
    from google.oauth2.credentials import Credentials

    try:
        with open(credentials_path) as credentials_file:
            credentials_json = json.load(credentials_file)
    except (IOError, ValueError):
        return None

    credentials = Credentials(
        token=credentials_json.get('access_token'),
        refresh_token=credentials_json.get('refresh_token'),
        id_token=credentials_json.get('id_token'),
        token_uri=credentials_json.get('token_uri'),
        client_id=credentials_json.get('client_id'),
        client_secret=credentials_json.get('client_secret'),
        scopes=credentials_json.get('scopes'))

    # Refresh the token before trying to use it.
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)

    return try_credentials(credentials, project_id)


def get_default_credentials_path(credentials_dirname, credentials_filename):
    """
    Gets the default path to the BigQuery credentials

    .. versionadded 0.3.0

    Returns
    -------
    Path to the BigQuery credentials
    """
    if os.name == 'nt':
        config_path = os.environ['APPDATA']
    else:
        config_path = os.path.join(os.path.expanduser('~'), '.config')

    config_path = os.path.join(config_path, credentials_dirname)

    # Create a pandas_gbq directory in an application-specific hidden
    # user folder on the operating system.
    if not os.path.exists(config_path):
        os.makedirs(config_path)

    return os.path.join(config_path, credentials_filename)


def save_user_account_credentials(credentials, credentials_path):
    """
    Saves user account credentials to a local file.

    .. versionadded 0.2.0
    """
    try:
        with open(credentials_path, 'w') as credentials_file:
            credentials_json = {
                'refresh_token': credentials.refresh_token,
                'id_token': credentials.id_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes,
            }
            json.dump(credentials_json, credentials_file)
    except IOError:
        logger.warning('Unable to save credentials.')
