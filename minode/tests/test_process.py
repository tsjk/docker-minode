"""Blind tests, starting the minode process"""
import unittest
import signal
import socket
import subprocess
import sys
import tempfile
import time

import psutil

from minode.structure import NetAddrNoPrefix

try:
    socket.socket().bind(('127.0.0.1', 7656))
    i2p_port_free = True
except (OSError, socket.error):
    i2p_port_free = False


class TestProcessProto(unittest.TestCase):
    """Test process attributes, common flow"""
    _process_cmd = ['minode']
    _connection_limit = 4 if sys.platform.startswith('win') else 10
    _listen = False
    _listening_port = None

    home = None

    @classmethod
    def setUpClass(cls):
        if not cls.home:
            cls.home = tempfile.gettempdir()
        cmd = cls._process_cmd + [
            '--data-dir', cls.home,
            '--connection-limit', str(cls._connection_limit)
        ]
        if not cls._listen:
            cmd += ['--no-incoming']
        elif cls._listening_port:
            cmd += ['-p', str(cls._listening_port)]
        cls.process = psutil.Popen(cmd, stderr=subprocess.STDOUT)  # nosec

    @classmethod
    def _stop_process(cls, timeout=5):
        cls.process.send_signal(signal.SIGTERM)
        try:
            cls.process.wait(timeout)
        except psutil.TimeoutExpired:
            return False
        return True

    @classmethod
    def tearDownClass(cls):
        """Ensures that process stopped and removes files"""
        try:
            if not cls._stop_process(10):
                try:
                    cls.process.kill()
                except psutil.NoSuchProcess:
                    pass
        except psutil.NoSuchProcess:
            pass

    def connections(self):
        """All process' established connections"""
        return [
            c for c in self.process.connections()
            if c.status == 'ESTABLISHED']


class TestProcessShutdown(TestProcessProto):
    """Separate test case for SIGTERM"""
    _wait_time = 30
    # longer wait time because it's not a benchmark

    def test_shutdown(self):
        """Send to minode SIGTERM and ensure it stopped"""
        self.assertTrue(
            self._stop_process(self._wait_time),
            '%s has not stopped in %i sec' % (
                ' '.join(self._process_cmd), self._wait_time))


class TestProcess(TestProcessProto):
    """The test case for minode process"""
    _wait_time = 120
    _check_limit = False

    def test_connections(self):
        """Check minode process connections"""
        _started = time.time()

        def continue_check_limit(extra_time):
            for _ in range(extra_time * 2):
                self.assertLessEqual(
                    len(self.connections()),
                    # shared.outgoing_connections, one listening
                    # TODO: find the cause of one extra
                    (min(self._connection_limit, 8) if not self._listen
                     else self._connection_limit) + 1,
                    'Opened more connections than required'
                    ' by --connection-limit')
                time.sleep(1)

        for _ in range(self._wait_time * 2):
            if len(self.connections()) > self._connection_limit / 2:
                _time_to_connect = round(time.time() - _started)
                break
            if '--i2p' not in self._process_cmd:
                groups = []
                for c in self.connections():
                    group = NetAddrNoPrefix.network_group(c.raddr[0])
                    self.assertNotIn(group, groups)
                    groups.append(group)
            time.sleep(0.5)
        else:
            self.fail(
                'Failed establish at least %i connections in %s sec'
                % (int(self._connection_limit / 2), self._wait_time))

        if self._check_limit:
            continue_check_limit(_time_to_connect)

        for c in self.process.connections():
            if c.status == 'LISTEN':
                if self._listen is False:
                    self.fail('Listening while started with --no-incoming')
                    return
                self.assertEqual(c.laddr[1], self._listening_port or 8444)
                break
        else:
            if self._listen:
                self.fail('No listening connection found')


@unittest.skipIf(i2p_port_free, 'No running i2pd detected')
class TestProcessI2P(TestProcess):
    """Test minode process with --i2p and no IP"""
    _process_cmd = ['minode', '--i2p', '--no-ip']
    _connection_limit = 4
    _listen = True
    _listening_port = 8448

    def test_connections(self):
        """Ensure all connections are I2P"""
        super().test_connections()
        for c in self.connections():
            self.assertEqual(c.raddr[0], '127.0.0.1')
            self.assertEqual(c.raddr[1], 7656)


@unittest.skipUnless(i2p_port_free, 'Detected running i2pd')
class TestProcessNoI2P(TestProcessShutdown):
    """Test minode process shutdown with --i2p and no IP"""
    _process_cmd = ['minode', '--i2p', '--no-ip']
