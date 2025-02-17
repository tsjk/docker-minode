# -*- coding: utf-8 -*-
import logging
import socket

from .util import I2PThread


class I2PDialer(I2PThread):
    def __init__(
        self, state, destination, nick, sam_host='127.0.0.1', sam_port=7656
    ):

        self.sam_host = sam_host
        self.sam_port = sam_port

        self.nick = nick
        self.destination = destination

        super().__init__(state, name='I2P Dial to {}'.format(self.destination))

        self.s = socket.create_connection((self.sam_host, self.sam_port))

        self.version_reply = []
        self.success = True

    def run(self):
        logging.debug('Connecting to %s', self.destination)
        self._connect()
        if not self.state.shutting_down and self.success:
            c = self.state.connection(
                self.destination, 'i2p', self.s, 'i2p',
                False, self.destination)
            c.start()
            self.state.connections.add(c)

    def _connect(self):
        self._send(b'HELLO VERSION MIN=3.0 MAX=3.3\n')
        self.version_reply = self._receive_line().split()
        if b'RESULT=OK' not in self.version_reply:
            logging.debug('Error while connecting to %s', self.destination)
            self.success = False

        self._send(
            b'STREAM CONNECT ID=' + self.nick + b' DESTINATION='
            + self.destination + b'\n')
        reply = self._receive_line().split(b' ')
        if b'RESULT=OK' not in reply:
            logging.debug('Error while connecting to %s', self.destination)
            self.success = False
