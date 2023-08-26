"""Tests for network connections"""
import logging
import os
import random
import unittest
import tempfile
import time
from contextlib import contextmanager

from minode import connection, main, shared
from minode.manager import Manager


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
            while c.status not in ('disconnecting', 'disconnected', 'failed'):
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
