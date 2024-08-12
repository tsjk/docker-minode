# -*- coding: utf-8 -*-
"""The main thread, managing connections, nodes and objects"""
import base64
import csv
import logging
import os
import pickle
import queue
import random
import threading
import time

from . import proofofwork, shared, structure
from .connection import Bootstrapper, Connection
from .i2p import I2PDialer


class Manager(threading.Thread):
    """The manager thread"""
    def __init__(self):
        super().__init__(name='Manager')
        self.q = queue.Queue()
        self.bootstrap_pool = []
        self.last_cleaned_objects = time.time()
        self.last_cleaned_connections = time.time()
        self.last_pickled_objects = time.time()
        self.last_pickled_nodes = time.time()
        # Publish destination 5-15 minutes after start
        self.last_published_i2p_destination = \
            time.time() - 50 * 60 + random.uniform(-1, 1) * 300  # nosec B311

    def fill_bootstrap_pool(self):
        """Populate the bootstrap pool by core nodes and checked ones"""
        self.bootstrap_pool = list(shared.core_nodes.union(shared.node_pool))
        random.shuffle(self.bootstrap_pool)

    def run(self):
        self.load_data()
        self.clean_objects()
        self.fill_bootstrap_pool()
        while True:
            time.sleep(0.8)
            now = time.time()
            if shared.shutting_down:
                logging.debug('Shutting down Manager')
                break
            if now - self.last_cleaned_objects > 90:
                self.clean_objects()
                self.last_cleaned_objects = now
            if now - self.last_cleaned_connections > 2:
                self.manage_connections()
                self.last_cleaned_connections = now
            if now - self.last_pickled_objects > 100:
                self.pickle_objects()
                self.last_pickled_objects = now
            if now - self.last_pickled_nodes > 60:
                self.pickle_nodes()
                self.last_pickled_nodes = now
            if now - self.last_published_i2p_destination > 3600:
                self.publish_i2p_destination()
                self.last_published_i2p_destination = now

    @staticmethod
    def clean_objects():
        for vector in set(shared.objects):
            # FIXME: no need to check is_valid() here
            if shared.objects[vector].is_expired():
                logging.debug(
                    'Deleted expired object: %s',
                    base64.b16encode(vector).decode())
                with shared.objects_lock:
                    del shared.objects[vector]

    def manage_connections(self):
        """Open new connections if needed, remove closed ones"""
        hosts = set()

        def connect(target, connection_class=Connection):
            """
            Open a connection of *connection_class*
            to the *target* (host, port)
            """
            c = connection_class(*target)
            c.start()
            with shared.connections_lock:
                shared.connections.add(c)

        def bootstrap():
            """Bootstrap from DNS seed-nodes and known nodes"""
            try:
                target = self.bootstrap_pool.pop()
            except IndexError:
                logging.warning(
                    'Ran out of bootstrap nodes, refilling')
                self.fill_bootstrap_pool()
                return
            logging.info('Starting a bootstrapper for %s:%s', *target)
            connect(target, Bootstrapper)

        outgoing_connections = 0
        for c in shared.connections.copy():
            if not c.is_alive() or c.status == 'disconnected':
                with shared.connections_lock:
                    shared.connections.remove(c)
            else:
                hosts.add(structure.NetAddrNoPrefix.network_group(c.host))
                if not c.server:
                    outgoing_connections += 1

        for d in shared.i2p_dialers.copy():
            hosts.add(d.destination)
            if not d.is_alive():
                shared.i2p_dialers.remove(d)

        to_connect = set()
        if shared.trusted_peer:
            to_connect.add(shared.trusted_peer)

        if (
            outgoing_connections < shared.outgoing_connections
            and shared.send_outgoing_connections and not shared.trusted_peer
        ):

            if shared.ip_enabled:
                if len(shared.unchecked_node_pool) > 16:
                    to_connect.update(random.sample(
                        tuple(shared.unchecked_node_pool), 16))
                else:
                    to_connect.update(shared.unchecked_node_pool)
                    if outgoing_connections < shared.outgoing_connections / 2:
                        bootstrap()
                shared.unchecked_node_pool.difference_update(to_connect)
                if len(shared.node_pool) > 8:
                    to_connect.update(random.sample(
                        tuple(shared.node_pool), 8))
                else:
                    to_connect.update(shared.node_pool)

            if shared.i2p_enabled:
                if len(shared.i2p_unchecked_node_pool) > 16:
                    to_connect.update(random.sample(
                        tuple(shared.i2p_unchecked_node_pool), 16))
                else:
                    to_connect.update(shared.i2p_unchecked_node_pool)
                shared.i2p_unchecked_node_pool.difference_update(to_connect)
                if len(shared.i2p_node_pool) > 8:
                    to_connect.update(random.sample(
                        tuple(shared.i2p_node_pool), 8))
                else:
                    to_connect.update(shared.i2p_node_pool)

        for host, port in to_connect:
            group = structure.NetAddrNoPrefix.network_group(host)
            if group in hosts:
                continue
            if port == 'i2p' and shared.i2p_enabled:
                if shared.i2p_session_nick and host != shared.i2p_dest_pub:
                    try:
                        d = I2PDialer(
                            shared,
                            host, shared.i2p_session_nick,
                            shared.i2p_sam_host, shared.i2p_sam_port)
                        d.start()
                        hosts.add(d.destination)
                        shared.i2p_dialers.add(d)
                    except Exception:
                        logging.warning(
                            'Exception while trying to establish'
                            ' an I2P connection', exc_info=True)
                else:
                    continue
            else:
                connect((host, port))
                hosts.add(group)
        shared.hosts = hosts

    @staticmethod
    def load_data():
        """Loads initial nodes and data, stored in files between sessions"""
        try:
            with open(
                os.path.join(shared.data_directory, 'objects.pickle'), 'br'
            ) as src:
                shared.objects = pickle.load(src)
        except FileNotFoundError:
            pass  # first start
        except Exception:
            logging.warning(
                'Error while loading objects from disk.', exc_info=True)

        try:
            with open(
                os.path.join(shared.data_directory, 'nodes.pickle'), 'br'
            ) as src:
                shared.node_pool = pickle.load(src)
        except FileNotFoundError:
            pass
        except Exception:
            logging.warning(
                'Error while loading nodes from disk.', exc_info=True)

        try:
            with open(
                os.path.join(shared.data_directory, 'i2p_nodes.pickle'), 'br'
            ) as src:
                shared.i2p_node_pool = pickle.load(src)
        except FileNotFoundError:
            pass
        except Exception:
            logging.warning(
                'Error while loading nodes from disk.', exc_info=True)

        with open(
            os.path.join(shared.source_directory, 'core_nodes.csv'),
            'r', newline='', encoding='ascii'
        ) as src:
            reader = csv.reader(src)
            shared.core_nodes = {(row[0], int(row[1])) for row in reader}
            shared.node_pool.update(shared.core_nodes)

        with open(
            os.path.join(shared.source_directory, 'i2p_core_nodes.csv'),
            'r', newline='', encoding='ascii'
        ) as f:
            reader = csv.reader(f)
            shared.i2p_core_nodes = {
                (row[0].encode(), 'i2p') for row in reader}
            shared.i2p_node_pool.update(shared.i2p_core_nodes)

    @staticmethod
    def pickle_objects():
        try:
            with open(
                os.path.join(shared.data_directory, 'objects.pickle'), 'bw'
            ) as dst:
                with shared.objects_lock:
                    pickle.dump(shared.objects, dst, protocol=3)
                logging.debug('Saved objects')
        except Exception:
            logging.warning('Error while saving objects', exc_info=True)

    @staticmethod
    def pickle_nodes():
        if len(shared.node_pool) > 10000:
            shared.node_pool = set(random.sample(
                tuple(shared.node_pool), 10000))
        if len(shared.unchecked_node_pool) > 1000:
            shared.unchecked_node_pool = set(random.sample(
                tuple(shared.unchecked_node_pool), 1000))

        if len(shared.i2p_node_pool) > 1000:
            shared.i2p_node_pool = set(random.sample(
                tuple(shared.i2p_node_pool), 1000))
        if len(shared.i2p_unchecked_node_pool) > 100:
            shared.i2p_unchecked_node_pool = set(random.sample(
                tuple(shared.i2p_unchecked_node_pool), 100))

        try:
            with open(
                os.path.join(shared.data_directory, 'nodes.pickle'), 'bw'
            ) as dst:
                pickle.dump(shared.node_pool, dst, protocol=3)
            with open(
                os.path.join(shared.data_directory, 'i2p_nodes.pickle'), 'bw'
            ) as dst:
                pickle.dump(shared.i2p_node_pool, dst, protocol=3)
                logging.debug('Saved nodes')
        except Exception:
            logging.warning('Error while saving nodes', exc_info=True)

    @staticmethod
    def publish_i2p_destination():
        if shared.i2p_session_nick and not shared.i2p_transient:
            logging.info('Publishing our I2P destination')
            dest_pub_raw = base64.b64decode(
                shared.i2p_dest_pub, altchars=b'-~')
            obj = structure.Object(
                b'\x00' * 8, int(time.time() + 2 * 3600),
                shared.i2p_dest_obj_type, shared.i2p_dest_obj_version,
                shared.stream, dest_pub_raw)
            proofofwork.do_pow_and_publish(obj)
