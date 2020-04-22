# -*- coding: utf-8 -*-

import socket

try:
    from unittest import mock
except ImportError:  # pragma: NO COVER
    import mock

import google_auth_oauthlib.flow
import pytest

from pydata_google_auth import exceptions


@pytest.fixture
def module_under_test():
    from pydata_google_auth import _webserver

    return _webserver


def test_find_open_port_finds_start_port(monkeypatch, module_under_test):
    monkeypatch.setattr(socket, "socket", mock.create_autospec(socket.socket))
    port = module_under_test.find_open_port(9999)
    assert port == 9999


def test_find_open_port_finds_stop_port(monkeypatch, module_under_test):
    socket_instance = mock.create_autospec(socket.socket, instance=True)

    def mock_socket(family, type_):
        return socket_instance

    monkeypatch.setattr(socket, "socket", mock_socket)
    socket_instance.listen.side_effect = [socket.error] * 99 + [None]
    port = module_under_test.find_open_port(9000, stop=9100)
    assert port == 9099


def test_find_open_port_returns_none(monkeypatch, module_under_test):
    socket_instance = mock.create_autospec(socket.socket, instance=True)

    def mock_socket(family, type_):
        return socket_instance

    monkeypatch.setattr(socket, "socket", mock_socket)
    socket_instance.listen.side_effect = socket.error
    port = module_under_test.find_open_port(9000)
    assert port is None
    socket_instance.listen.assert_has_calls(mock.call(1) for _ in range(100))


def test_run_local_server_calls_flow(monkeypatch, module_under_test):
    mock_flow = mock.create_autospec(
        google_auth_oauthlib.flow.InstalledAppFlow, instance=True
    )
    module_under_test.run_local_server(mock_flow)
    mock_flow.run_local_server.assert_called_once()


def test_run_local_server_raises_connectionerror(monkeypatch, module_under_test):
    def mock_find_open_port():
        return None

    monkeypatch.setattr(module_under_test, "find_open_port", mock_find_open_port)
    mock_flow = mock.create_autospec(
        google_auth_oauthlib.flow.InstalledAppFlow, instance=True
    )

    with pytest.raises(exceptions.PyDataConnectionError):
        module_under_test.run_local_server(mock_flow)

    mock_flow.run_local_server.assert_not_called()
