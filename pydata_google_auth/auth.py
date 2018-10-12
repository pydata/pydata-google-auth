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
from pydata_google_auth import cache


logger = logging.getLogger(__name__)

CLIENT_ID = (
    "262006177488-3425ks60hkk80fssi9vpohv88g6q1iqd" ".apps.googleusercontent.com"
)
CLIENT_SECRET = "JSF-iczmzEgbTR-XK-2xaWAc"


def default(
    scopes,
    client_id=None,
    client_secret=None,
    credentials_cache=cache.READ_WRITE,
    auth_local_webserver=False,
):
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
        credentials.refresh(request)

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
                "Unable to get valid credentials: {0}".format(exc)
            )

        credentials_cache.save(credentials)

    if credentials and not credentials.valid:
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)

    return credentials
