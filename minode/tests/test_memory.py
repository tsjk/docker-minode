"""Tests for memory usage"""

import gc
import time

from minode import shared

from .test_network import TestProcessProto, run_listener


class TestListener(TestProcessProto):
    """A separate test case for Listener with a process with --trusted-peer"""
    _process_cmd = ['minode', '--trusted-peer', '127.0.0.1']

    def setUp(self):
        shared.shutting_down = False

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shared.shutting_down = False

    def test_listener(self):
        """Start Listener and disconnect a client"""
        with run_listener() as listener:
            if not listener:
                self.fail('Failed to start listener')

            shared.connection_limit = 2
            connected = False
            started = time.time()
            while not connected:
                time.sleep(0.2)
                if time.time() - started > 90:
                    self.fail('Failed to establish the connection')
                for c in shared.connections:
                    if c.status == 'fully_established':
                        connected = True

            if not self._stop_process(10):
                self.fail('Failed to stop the client process')

            for c in shared.connections.copy():
                if not c.is_alive() or c.status == 'disconnected':
                    shared.connections.remove(c)
                    c = None
                    break
            else:
                self.fail('The connection is alive')

            gc.collect()
            for obj in gc.get_objects():
                if (
                    isinstance(obj, shared.connection)
                    and obj not in shared.connections
                ):
                    self.fail('Connection %s remains in memory' % obj)
