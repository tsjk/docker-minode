"""Tests for network connections"""
import logging
import os
import random
import unittest
import tempfile
import time
from contextlib import contextmanager

from minode import connection, main, shared
from minode.listener import Listener
from minode.manager import Manager

from .test_process import TestProcessProto


logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s')


@contextmanager
def time_offset(offset):
    """
    Replace time.time() by a mock returning a constant value
    with given offset from current time.
    """
    started = time.time()
    time_call = time.time
    try:
        time.time = lambda: started + offset
        yield time_call
    finally:
        time.time = time_call


@contextmanager
def run_listener(host='localhost', port=8444):
    """
    Run the Listener with zero connection limit and
    reset variables in shared after its stop.
    """
    connection_limit = shared.connection_limit
    shared.connection_limit = 0
    try:
        listener = Listener(host, port)
        listener.start()
        yield listener
    except OSError:
        yield
    finally:
        shared.connection_limit = connection_limit
        shared.connections.clear()
        shared.shutting_down = True
        time.sleep(1)


class TestNetwork(unittest.TestCase):
    """Test case starting connections"""

    @classmethod
    def setUpClass(cls):
        shared.data_directory = tempfile.gettempdir()

    def setUp(self):
        shared.core_nodes.clear()
        shared.unchecked_node_pool.clear()
        shared.objects = {}
        try:
            os.remove(os.path.join(shared.data_directory, 'objects.pickle'))
        except FileNotFoundError:
            pass

    def _make_initial_nodes(self):
        Manager.load_data()
        self.assertGreaterEqual(len(shared.core_nodes), 3)

        main.bootstrap_from_dns()
        self.assertGreaterEqual(len(shared.unchecked_node_pool), 3)

    def test_connection(self):
        """Check a normal connection - should receive objects"""
        self._make_initial_nodes()

        started = time.time()
        nodes = list(shared.core_nodes.union(shared.unchecked_node_pool))
        random.shuffle(nodes)

        for node in nodes:
            # unknown = node not in shared.node_pool
            # self.assertTrue(unknown)
            unknown = True
            shared.node_pool.discard(node)

            c = connection.Connection(*node)
            c.start()
            connection_started = time.time()
            while c.status not in ('disconnected', 'failed'):
                # The addr of established connection is added to nodes pool
                if unknown and c.status == 'fully_established':
                    unknown = False
                    self.assertIn(node, shared.node_pool)
                if shared.objects or time.time() - connection_started > 90:
                    c.status = 'disconnecting'
                if time.time() - started > 300:
                    c.status = 'disconnecting'
                    self.fail('Failed to receive an object in %s sec' % 300)
                time.sleep(0.2)
            if shared.objects:  # got some objects
                break
        else:
            self.fail('Failed to establish a proper connection')

    def test_time_offset(self):
        """Assert the network bans for large time offset"""
        def try_connect(nodes, timeout, call):
            started = call()
            for node in nodes:
                c = connection.Connection(*node)
                c.start()
                while call() < started + timeout:
                    if c.status == 'fully_established':
                        return 'Established a connection'
                    if c.status in ('disconnected', 'failed'):
                        break
                    time.sleep(0.2)
                else:
                    return 'Spent too much time trying to connect'

        def time_offset_connections(nodes, offset):
            """Spoof time.time and open connections with given time offset"""
            with time_offset(offset) as time_call:
                result = try_connect(nodes, 200, time_call)
                if result:
                    self.fail(result)

        self._make_initial_nodes()
        nodes = random.sample(
            tuple(shared.core_nodes.union(shared.unchecked_node_pool)), 5)

        time_offset_connections(nodes, 4000)
        time_offset_connections(nodes, -4000)


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
        """Start Listener and try to connect"""
        with run_listener() as listener:
            if not listener:
                self.fail('Failed to start listener')

            c = connection.Connection('127.0.0.1', 8444)
            shared.connections.add(c)

            for _ in range(30):
                if len(shared.connections) > 1:
                    self.fail('The listener ignored connection limit')
                time.sleep(0.5)

            shared.connection_limit = 2
            c.start()
            started = time.time()
            while c.status not in ('disconnected', 'failed'):
                if c.status == 'fully_established':
                    self.fail('Connected to itself')
                if time.time() - started > 90:
                    c.status = 'disconnecting'
                time.sleep(0.2)

            server = None
            started = time.time()
            while not server:
                time.sleep(0.2)
                if time.time() - started > 90:
                    self.fail('Failed to establish the connection')
                for c in shared.connections:
                    if c.status == 'fully_established':
                        server = c
            self.assertTrue(server.server)

            while not self.process.connections():
                time.sleep(0.2)
                if time.time() - started > 90:
                    self.fail('Failed to connect to listener')

            client = self.process.connections()[0]
            self.assertEqual(client.raddr[0], '127.0.0.1')
            self.assertEqual(client.raddr[1], 8444)
            self.assertEqual(server.host, client.laddr[0])
            # self.assertEqual(server.port, client.laddr[1])
            server.status = 'disconnecting'

        self.assertFalse(listener.is_alive())

    def test_listener_timeoffset(self):
        """Run listener with a large time offset - shouldn't connect"""
        with time_offset(4000):
            with run_listener() as listener:
                if not listener:
                    self.fail('Failed to start listener')
                shared.connection_limit = 2
                for _ in range(30):
                    for c in shared.connections:
                        if c.status == 'fully_established':
                            self.fail('Established a connection')
                    time.sleep(0.5)
