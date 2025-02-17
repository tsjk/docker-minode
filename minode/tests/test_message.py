"""Tests for messages"""
import struct
import time
import unittest
from binascii import unhexlify

from minode import message
from minode.shared import magic_bytes


# 500 identical peers:
# import ipaddress
# from hyperbit import net, packet
# [packet.Address(
#     1626611891, 1, 1, net.ipv6(ipaddress.ip_address('127.0.0.1')).packed,
#     8444
# ) for _ in range(1000)]
sample_addr_data = unhexlify(
    'fd01f4' + (
        '0000000060f420b30000000'
        '1000000000000000100000000000000000000ffff7f00000120fc'
        ) * 500
)

# protocol.CreatePacket(b'ping', b'test')
sample_ping_msg = unhexlify(
    'e9beb4d970696e67000000000000000000000004ee26b0dd74657374')

# from pybitmessage import pathmagic
# pathmagic.setup()
# import protocol
# msg = protocol.assembleVersionMessage('127.0.0.1', 8444, [1, 2, 3])
sample_version_msg = unhexlify(
    'e9beb4d976657273696f6e00000000000000006b1b06b182000000030000000000000003'
    '0000000064fdd3e1000000000000000100000000000000000000ffff7f00000120fc0000'
    '00000000000300000000000000000000ffff7f00000120fc00c0b6c3eefb2adf162f5079'
    '4269746d6573736167653a302e362e332e322f03010203'
)

#
sample_error_data = \
    b'\x02\x00\x006Too many connections from your IP. Closing connection.'


class TestMessage(unittest.TestCase):
    """Test assembling and disassembling of network mesages"""

    def test_packet(self):
        """Check packet creation and parsing by message.Message"""
        msg = message.Message(b'ping', b'test').to_bytes()
        self.assertEqual(msg[:len(magic_bytes)], magic_bytes)
        with self.assertRaises(ValueError):
            # wrong magic
            message.Message.from_bytes(msg[1:])
        with self.assertRaises(ValueError):
            # wrong length
            message.Message.from_bytes(msg[:-1])
        with self.assertRaises(ValueError):
            # wrong checksum
            message.Message.from_bytes(msg[:-1] + b'\x00')
        msg = message.Message.from_bytes(sample_ping_msg)
        self.assertEqual(msg.command, b'ping')
        self.assertEqual(msg.payload, b'test')

    def test_addr(self):
        """Test addr messages"""
        msg = message.Message(b'addr', sample_addr_data)
        addr_packet = message.Addr.from_message(msg)
        self.assertEqual(len(addr_packet.addresses), 500)
        address = addr_packet.addresses.pop()
        self.assertEqual(address.stream, 1)
        self.assertEqual(address.services, 1)
        self.assertEqual(address.port, 8444)
        self.assertEqual(address.host, '127.0.0.1')

    def test_version(self):
        """Test version message"""
        msg = message.Message.from_bytes(sample_version_msg)
        self.assertEqual(msg.command, b'version')
        with self.assertRaises(ValueError):
            # large time offset
            version_packet = message.Version.from_message(msg)
        msg.payload = (
            msg.payload[:12] + struct.pack('>Q', int(time.time()))
            + msg.payload[20:])

        version_packet = message.Version.from_message(msg)
        self.assertEqual(version_packet.host, '127.0.0.1')
        self.assertEqual(version_packet.port, 8444)
        self.assertEqual(version_packet.protocol_version, 3)
        self.assertEqual(version_packet.services, 3)
        self.assertEqual(version_packet.user_agent, b'/PyBitmessage:0.6.3.2/')
        self.assertEqual(version_packet.streams, [1, 2, 3])

        msg = version_packet.to_bytes()
        # omit header and timestamp
        self.assertEqual(msg[24:36], sample_version_msg[24:36])
        self.assertEqual(msg[44:], sample_version_msg[44:])

    def test_error(self):
        """Test error message"""
        msg = message.Error.from_message(
            message.Message(b'error', sample_error_data))
        self.assertEqual(msg.fatal, 2)
        self.assertEqual(msg.ban_time, 0)
        self.assertEqual(msg.vector, b'')

        msg = message.Error(
            b'Too many connections from your IP. Closing connection.', 2)
        self.assertEqual(msg.to_bytes()[24:], sample_error_data)
