"""Helpers for running a local webserver to receive authorization code."""

import socket
from contextlib import closing

from pydata_google_auth import exceptions


LOCALHOST = "localhost"
DEFAULT_PORTS_TO_TRY = 100


def is_port_open(port):
    """Check if a port is open on localhost.

    Based on StackOverflow answer: https://stackoverflow.com/a/43238489/101923

    Parameters
    ----------
    port : int
        A port to check on localhost.

    Returns
    -------
    is_open : bool
        True if a socket can be opened at the requested port.
    """
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        try:
            sock.bind((LOCALHOST, port))
            sock.listen(1)
        except socket.error:
            is_open = False
        else:
            is_open = True
    return is_open


def find_open_port(start=8080, stop=None):
    """Find an open port between ``start`` and ``stop``.

    Parameters
    ----------
    start : Optional[int]
        Beginning of range of ports to try. Defaults to 8080.
    stop : Optional[int]
        End of range of ports to try (not including exactly equals ``stop``).
        This function tries 100 possible ports if no ``stop`` is specified.

    Returns
    -------
    Optional[int]
        ``None`` if no open port is found, otherwise an integer indicating an
        open port.
    """
    if not stop:
        stop = start + DEFAULT_PORTS_TO_TRY

    for port in range(start, stop):
        if is_port_open(port):
            return port

    # No open ports found.
    return None


def run_local_server(app_flow, **kwargs):
    """Run local webserver installed app flow on some open port.

    Parameters
    ----------
    app_flow : google_auth_oauthlib.flow.InstalledAppFlow
        Installed application flow to fetch user credentials.

    Returns
    -------
    google.auth.credentials.Credentials
        User credentials from installed application flow.

    Raises
    ------
    pydata_google_auth.exceptions.PyDataConnectionError
        If no open port can be found in the range from 8080 to 8089,
        inclusive.
    """
    port = find_open_port()
    if not port:
        raise exceptions.PyDataConnectionError("Could not find open port.")
    return app_flow.run_local_server(host=LOCALHOST, port=port, **kwargs)
