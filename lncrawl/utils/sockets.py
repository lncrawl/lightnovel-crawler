"""Socket helpers."""
import socket


def free_port(host="127.0.0.1") -> int:
    """Find and return an available TCP port on the given host."""
    free_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    free_socket.bind((host, 0))
    free_socket.listen(5)
    port: int = free_socket.getsockname()[1]
    free_socket.close()
    return port
