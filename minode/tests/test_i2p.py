"""Tests for I2P subpackage"""
import os
import tempfile
import threading
import time
import unittest

from minode import main, shared

from .common import i2p_port, i2p_port_free

shared.i2p_sam_port = i2p_port


@unittest.skipIf(i2p_port_free, 'No running i2pd detected')
class TestI2P(unittest.TestCase):
    """A test case running I2P parts"""
    _wait_time = 90
    _files = ['i2p_dest_priv.key', 'i2p_dest.pub']
    _threads = {'I2P Controller', 'I2P Listener'}

    @classmethod
    def cleanup(cls):
        """Remove used files"""
        for f in cls._files:
            try:
                os.remove(os.path.join(shared.data_directory, f))
            except FileNotFoundError:
                pass

    @classmethod
    def setUpClass(cls):
        shared.data_directory = tempfile.gettempdir()
        cls.cleanup()

    @classmethod
    def tearDownClass(cls):
        shared.shutting_down = True
        time.sleep(10)
        shared.shutting_down = False
        for thread in threading.enumerate():
            if thread is not threading.current_thread():
                cls.fail('Thread "%s" failed to stop in 10 sec' % thread.name)
        cls.cleanup()

    def test_i2p_listener(self):
        """Start I2P listener as in main and check the environment"""
        t = threading.Thread(target=main.start_i2p_listener, name='Start')
        t.start()
        for _ in range(self._wait_time):
            for f in self._files:
                if not os.path.isfile(os.path.join(shared.data_directory, f)):
                    break
            else:
                break
            time.sleep(1)
        else:
            self.fail('I2PController has probably failed to start')

        for thread in threading.enumerate():
            if thread is not threading.current_thread():
                self._threads.remove(thread.name)

        self.assertFalse(self._threads)
