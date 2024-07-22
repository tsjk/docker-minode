"""Common staff for the tests"""

import socket


try:
    socket.socket().bind(('127.0.0.1', 7656))
    i2p_port_free = True
except (OSError, socket.error):
    i2p_port_free = False
