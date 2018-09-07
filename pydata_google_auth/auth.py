"""Private module for fetching Google API credentials."""

import json
import logging
import os
import os.path

import google.auth
import google.auth.exceptions
import google.oauth2.credentials
from google_auth_oauthlib import flow
import oauthlib.oauth2.rfc6749.errors
import google.auth.transport.requests

from pydata_google_auth import exceptions


logger = logging.getLogger(__name__)

CLIENT_ID = (
    '262006177488-3425ks60hkk80fssi9vpohv88g6q1iqd'
    '.apps.googleusercontent.com'
)
CLIENT_SECRET = 'JSF-iczmzEgbTR-XK-2xaWAc'
CREDENTIALS_DIRNAME = 'pydata'
CREDENTIALS_FILENAME = 'google_credentials.json'


def default(
        scopes,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        credentials_dirname=CREDENTIALS_DIRNAME,
        credentials_filename=CREDENTIALS_FILENAME,
        reauth=False,
        auth_local_webserver=False):
    # Try to retrieve Application Default Credentials
    credentials, default_project = get_application_default_credentials(scopes)

    if credentials:
        return credentials, default_project

    credentials = get_user_account_credentials(
        scopes,
        client_id=client_id,
        client_secret=client_secret,
        credentials_dirname=credentials_dirname,
        credentials_filename=credentials_filename,
        reauth=reauth,
        auth_local_webserver=auth_local_webserver)

    if not credentials:
        raise exceptions.PyDataCredentialsError(
            'Could not get any valid credentials.')
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
        return google.auth.default(scopes=scopes)
    except (google.auth.exceptions.DefaultCredentialsError, IOError) as exc:
        logger.debug('Error getting default credentials: {}'.format(str(exc)))
        return None, None


def get_user_account_credentials(
        scopes,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        credentials_dirname=CREDENTIALS_DIRNAME,
        credentials_filename=CREDENTIALS_FILENAME,
        reauth=False,
        auth_local_webserver=False):
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
    # Use the default credentials location under ~/.config and the
    # equivalent directory on windows if the user has not specified a
    # credentials path.
    credentials_path = get_default_credentials_path(
        credentials_dirname,
        credentials_filename)

    credentials = None
    if not reauth:
        credentials = load_user_account_credentials(credentials_path)

    client_config = {
        'installed': {
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uris': ['urn:ietf:wg:oauth:2.0:oob'],
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://accounts.google.com/o/oauth2/token',
        }
    }

    if credentials is None:
        app_flow = flow.InstalledAppFlow.from_client_config(
            client_config, scopes=scopes)

        try:
            if auth_local_webserver:
                credentials = app_flow.run_local_server()
            else:
                credentials = app_flow.run_console()
        except oauthlib.oauth2.rfc6749.errors.OAuth2Error as exc:
            raise exceptions.PyDataCredentialsError(
                "Unable to get valid credentials: {0}".format(exc))

        save_user_account_credentials(credentials, credentials_path)

    return credentials


def load_user_account_credentials(credentials_path):
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
    try:
        with open(credentials_path) as credentials_file:
            credentials_json = json.load(credentials_file)
    except (IOError, ValueError) as exc:
        logger.debug('Error loading credentials from {}: {}'.format(
            credentials_path, str(exc)))
        return None

    credentials = google.oauth2.credentials.Credentials(
        token=credentials_json.get('access_token'),
        refresh_token=credentials_json.get('refresh_token'),
        id_token=credentials_json.get('id_token'),
        token_uri=credentials_json.get('token_uri'),
        client_id=credentials_json.get('client_id'),
        client_secret=credentials_json.get('client_secret'),
        scopes=credentials_json.get('scopes'))

    return credentials


def get_default_credentials_path(credentials_dirname, credentials_filename):
    """
    Gets the default path to the Google user credentials

    .. versionadded 0.3.0

    Returns
    -------
    Path to the Google user credentials
    """
    if os.name == 'nt':
        config_path = os.environ['APPDATA']
    else:
        config_path = os.path.join(os.path.expanduser('~'), '.config')

    config_path = os.path.join(config_path, credentials_dirname)

    # Create a pydata directory in an application-specific hidden
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
