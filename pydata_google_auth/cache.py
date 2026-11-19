"""Caching implementations for reading and writing user credentials."""

import errno
import json
import logging
import os
import os.path
import stat
import tempfile

import google.oauth2.credentials
from google.oauth2 import service_account


logger = logging.getLogger(__name__)


_DIRNAME = "pydata"
_FILENAME = "pydata_google_credentials.json"


def _get_default_credentials_path(credentials_dirname, credentials_filename):
    """
    Gets the default path to the Google user credentials

    Returns
    -------
    str
        Path to the Google user credentials
    """
    config_path = os.getenv("XDG_CONFIG_HOME")

    if not config_path and os.name == "nt":
        config_path = os.getenv("APPDATA")
    if not config_path:
        config_path = os.path.join(os.path.expanduser("~"), ".config")

    config_path = os.path.join(config_path, credentials_dirname)
    return os.path.join(config_path, credentials_filename)


def _load_user_credentials_from_info(credentials_json):
    credentials = google.oauth2.credentials.Credentials(
        token=credentials_json.get("access_token"),
        refresh_token=credentials_json.get("refresh_token"),
        id_token=credentials_json.get("id_token"),
        token_uri=credentials_json.get("token_uri"),
        client_id=credentials_json.get("client_id"),
        client_secret=credentials_json.get("client_secret"),
        scopes=credentials_json.get("scopes"),
    )

    if credentials and not credentials.valid:
        request = google.auth.transport.requests.Request()
        try:
            credentials.refresh(request)
        except google.auth.exceptions.RefreshError:
            # Credentials could be expired or revoked. Try to reauthorize.
            return None

    return credentials


def _load_user_credentials_from_file(credentials_path):
    """
    Loads user account credentials from a local file.

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
        logger.debug(
            "Error loading credentials from {}: {}".format(credentials_path, str(exc))
        )
        return None

    return _load_user_credentials_from_info(credentials_json)


def _replace_with_private_file(path, contents):
    """
    Replaces the file at path with a new file that only the current user can
    read or write (mode 0600).

    Returns
    -------
    bool
        ``True`` if the file was replaced. Otherwise ``False``, and the file
        is unchanged.
    """
    path = os.fsdecode(path)
    directory, filename = os.path.split(path)
    try:
        fd, temp_path = tempfile.mkstemp(
            dir=directory or os.curdir, prefix=filename + ".", suffix=".tmp"
        )
    except OSError:
        return False

    replaced = False
    try:
        with os.fdopen(fd, "w") as temp_file:
            temp_file.write(contents)
        try:
            os.replace(temp_path, path)
            replaced = True
        except OSError:
            pass
    finally:
        if not replaced:
            try:
                os.remove(temp_path)
            except OSError:
                pass
    return replaced


def _is_owned_by_current_user(path_stat):
    # os.stat doesn't report file owners on Windows, so skip the check there.
    return not hasattr(os, "geteuid") or path_stat.st_uid == os.geteuid()


def _write_private_file(path, contents):
    """
    Writes contents to the file at path, so that only the current user can
    read or write the file (mode 0600).
    """
    try:
        path_stat = os.lstat(path)
    except OSError:
        path_stat = None

    # Replace the file instead of rewriting it, so that a user who has the old
    # file open can't read the new credentials. Write in place where a
    # replacement would break a link, change the owner or overwrite a
    # read-only file.
    if (
        path_stat is None
        or (
            stat.S_ISREG(path_stat.st_mode)
            and path_stat.st_nlink == 1
            and _is_owned_by_current_user(path_stat)
            and os.access(path, os.W_OK)
        )
    ) and _replace_with_private_file(path, contents):
        return

    # Don't truncate the file before it's known to be safe to write to.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT, 0o600)
    with os.fdopen(fd, "w") as private_file:
        fd_stat = os.fstat(fd)
        is_regular_file = stat.S_ISREG(fd_stat.st_mode)
        if (
            (is_regular_file or stat.S_ISFIFO(fd_stat.st_mode))
            and hasattr(os, "geteuid")
            and os.geteuid() not in (0, fd_stat.st_uid)
        ):
            raise PermissionError(
                errno.EACCES, "Credentials file belongs to another user", path
            )

        if is_regular_file:
            if hasattr(os, "fchmod"):
                try:
                    os.fchmod(fd, 0o600)
                except OSError:
                    logger.warning("Unable to restrict access to credentials file.")
            os.ftruncate(fd, 0)
        private_file.write(contents)


def _remove_other_users_access(path):
    """
    Removes other users' access from an existing credentials file.
    """
    if os.name == "nt":
        # File modes don't restrict other users on Windows.
        return
    try:
        path_stat = os.stat(path)
        mode = stat.S_IMODE(path_stat.st_mode)
        if stat.S_ISREG(path_stat.st_mode) and mode & 0o077:
            os.chmod(path, mode & 0o700)
    except OSError:
        pass


def _save_user_account_credentials(credentials, credentials_path):
    """
    Saves user account credentials to a local file.

    Only the current user can read or write the file (mode 0600), or access
    a directory that is created for it (mode 0700).
    """

    # Create the direcory if it doesn't exist.
    # https://stackoverflow.com/a/12517490/101923
    # A bare filename is saved in the current directory.
    config_dir = os.path.dirname(credentials_path) or os.curdir
    if not os.path.exists(config_dir):
        try:
            os.makedirs(config_dir, mode=0o700)
        except OSError as exc:  # Guard against race condition.
            if exc.errno != errno.EEXIST:
                logger.warning("Unable to create credentials directory.")
                return

    try:
        credentials_json = {
            "refresh_token": credentials.refresh_token,
            "id_token": credentials.id_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
            # Required for Application Default Credentials to detect the
            # credentials type. See:
            # https://github.com/pydata/pydata-google-auth/issues/22
            "type": "authorized_user",
        }
        _write_private_file(credentials_path, json.dumps(credentials_json))
    except IOError:
        logger.warning("Unable to save credentials.")


def _load_service_account_credentials_from_file(credentials_path, **kwargs):
    try:
        with open(credentials_path) as credentials_file:
            credentials_json = json.load(credentials_file)
    except (IOError, ValueError) as exc:
        logger.debug(
            "Error loading credentials from {}: {}".format(credentials_path, str(exc))
        )
        return None

    return _load_service_account_credentials_from_info(credentials_json, **kwargs)


def _load_service_account_credentials_from_info(credentials_json, **kwargs):
    credentials = service_account.Credentials.from_service_account_info(
        credentials_json, **kwargs
    )
    if not credentials.valid:
        request = google.auth.transport.requests.Request()
        try:
            credentials.refresh(request)
        except google.auth.exceptions.RefreshError as exc:
            # Credentials could be expired or revoked.
            logger.debug("Error refreshing credentials: {}".format(str(exc)))
            return None

    return credentials


class CredentialsCache(object):
    """
    Shared base class for crentials classes.

    This class also functions as a noop implementation of a credentials class.
    """

    def load(self):
        """
        Load credentials from disk.

        Does nothing in this base class.

        Returns
        -------
        google.oauth2.credentials.Credentials, optional
            Returns user account credentials loaded from disk or ``None`` if no
            credentials could be found.
        """
        pass

    def save(self, credentials):
        """
        Write credentials to disk.

        Does nothing in this base class.

        Parameters
        ----------
        credentials : google.oauth2.credentials.Credentials
            User credentials to save to disk.
        """
        pass


class ReadWriteCredentialsCache(CredentialsCache):
    """
    A :class:`~pydata_google_auth.cache.CredentialsCache` which writes to
    disk and reads cached credentials from disk.

    Parameters
    ----------
    dirname : str, optional
        Name of directory to write credentials to. This directory is created
        within ``XDG_CONFIG_HOME`` when set. Otherwise, it is created within
        ``APPDATA`` on Windows or the ``.config`` subdirectory of ``HOME``.
    filename : str, optional
        Name of the credentials file within the credentials directory.
    """

    def __init__(self, dirname=_DIRNAME, filename=_FILENAME):
        super(ReadWriteCredentialsCache, self).__init__()
        self._path = _get_default_credentials_path(dirname, filename)

    def load(self):
        """
        Load credentials from disk.

        Returns
        -------
        google.oauth2.credentials.Credentials, optional
            Returns user account credentials loaded from disk or ``None`` if no
            credentials could be found.
        """
        _remove_other_users_access(self._path)
        return _load_user_credentials_from_file(self._path)

    def save(self, credentials):
        """
        Write credentials to disk.

        Parameters
        ----------
        credentials : google.oauth2.credentials.Credentials
            User credentials to save to disk.
        """
        _save_user_account_credentials(credentials, self._path)


class WriteOnlyCredentialsCache(CredentialsCache):
    """
    A :class:`~pydata_google_auth.cache.CredentialsCache` which writes to
    disk, but doesn't read from disk.

    Use this class to reauthorize against Google APIs and cache your
    credentials for later.

    Parameters
    ----------
    dirname : str, optional
        Name of directory to write credentials to. This directory is created
        within ``XDG_CONFIG_HOME`` when set. Otherwise, it is created within
        ``APPDATA`` on Windows or the ``.config`` subdirectory of ``HOME``.
    filename : str, optional
        Name of the credentials file within the credentials directory.
    """

    def __init__(self, dirname=_DIRNAME, filename=_FILENAME):
        super(WriteOnlyCredentialsCache, self).__init__()
        self._path = _get_default_credentials_path(dirname, filename)

    def save(self, credentials):
        """
        Write credentials to disk.

        Parameters
        ----------
        credentials : google.oauth2.credentials.Credentials
            User credentials to save to disk.
        """
        _save_user_account_credentials(credentials, self._path)


NOOP = CredentialsCache()
"""
Noop impmentation of credentials cache.

This cache always reauthorizes and never save credentials to disk.
Recommended for shared machines.
"""

READ_WRITE = ReadWriteCredentialsCache()
"""
Write credentials to disk and read cached credentials from disk.
"""

REAUTH = WriteOnlyCredentialsCache()
"""
Write credentials to disk. Never read cached credentials from disk.

Use this to reauthenticate and refresh the cached credentials.
"""
