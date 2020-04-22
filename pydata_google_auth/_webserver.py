"""Helpers for running a local webserver to receive authorization code."""

import socket
from contextlib import closing


LOCALHOST = "localhost"


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
            sock.listen(0)
        except socket.error:
            is_open = False
        else:
            is_open = True
    return is_open


def find_open_port(start=8080, stop=8090):
    for port in range(start, stop):
        if is_port_open(port):
            return port

    # No open ports found.
    return None


def run_local_server(app_flow):
    port = find_open_port()
    if not port:
        raise ConnectionError("Could not find open port.")
    return app_flow.run_local_server(host=LOCALHOST, port=port)
