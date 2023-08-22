"""Tests for network connections"""
import logging
import os
import random
import unittest
import tempfile
import time

from minode import connection, main, shared
from minode.manager import Manager


logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s')


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

    def test_connection(self):
        """Check a normal connection - should receive objects"""
        Manager.load_data()
        self.assertGreaterEqual(len(shared.core_nodes), 3)

        main.bootstrap_from_dns()
        self.assertGreaterEqual(len(shared.unchecked_node_pool), 3)

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
