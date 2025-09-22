from src.utils.network_utils import get_local_ip
from unittest.mock import patch
import builtins

original_open = builtins.open

@patch('socket.socket')
def test_get_local_ip(mock_socket):
    mock_socket.return_value.connect.return_value = None
    mock_socket.return_value.getsockname.return_value = ["127.0.0.1"]
    assert get_local_ip() == "127.0.0.1"

@patch('socket.socket')
def test_get_local_ip_exception(mock_socket):
    mock_socket.return_value.connect.side_effect = Exception("Connection error")
    mock_socket.return_value.getsockname.return_value = ["127.0.0.1"]
    mock_close = mock_socket.return_value.close

    ip = get_local_ip()
    assert ip == "127.0.0.1"
    mock_close.assert_called_once()

@patch('socket.socket')
def test_get_local_ip_finally_close(mock_socket):
    mock_socket.return_value.connect.return_value = None
    mock_socket.return_value.getsockname.return_value = ["127.0.0.1"]
    mock_close = mock_socket.return_value.close

    ip = get_local_ip()
    assert ip == "127.0.0.1"
    mock_close.assert_called_once()