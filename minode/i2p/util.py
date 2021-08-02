# -*- coding: utf-8 -*-
import base64
import hashlib
import threading


def receive_line(s):
    data = b''
    while b'\n' not in data:
        d = s.recv(4096)
        if not d:
            raise ConnectionResetError
        data += d
    data = data.splitlines()
    return data[0]


class I2PThread(threading.Thread):
    """
    Abstract I2P thread with _receive_line() and _send() methods,
    reused in I2PDialer, I2PListener and I2PController
    """
    def _receive_line(self):
        line = receive_line(self.s)
        # logging.debug('I2PListener <- %s', line)
        return line

    def _send(self, command):
        # logging.debug('I2PListener -> %s', command)
        self.s.sendall(command)


def pub_from_priv(priv):
    priv = base64.b64decode(priv, altchars=b'-~')
    # 256 for public key + 128 for signing key + 3 for certificate header
    # + value of bytes priv[385:387]
    pub = priv[:387 + int.from_bytes(priv[385:387], byteorder='big')]
    return base64.b64encode(pub, altchars=b'-~')


def b32_from_pub(pub):
    return base64.b32encode(
        hashlib.sha256(base64.b64decode(pub, b'-~')).digest()
    ).replace(b'=', b'').lower() + b'.b32.i2p'
