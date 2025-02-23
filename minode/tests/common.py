"""Common staff for the tests"""

import itertools
import os
import socket
from configparser import ConfigParser


i2p_port = 7656

if os.path.isfile('/etc/i2pd/i2pd.conf'):
    i2p_conf = ConfigParser()
    with open('/etc/i2pd/i2pd.conf', encoding='ascii') as fp:
        i2p_conf.read_file(itertools.chain(['[global]'], fp))
    i2p_port = i2p_conf.getint('sam', 'port', fallback=7656)

try:
    socket.socket().bind(('127.0.0.1', i2p_port))
    i2p_port_free = True
except (OSError, socket.error):
    i2p_port_free = False
