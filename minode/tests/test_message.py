"""Tests for messages"""
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
sample_data = unhexlify(
    'fd01f4' + (
        '0000000060f420b30000000'
        '1000000000000000100000000000000000000ffff7f00000120fc'
        ) * 500
)

# protocol.CreatePacket(b'ping', b'test')
sample_ping_msg = unhexlify(
    'e9beb4d970696e67000000000000000000000004ee26b0dd74657374')


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
        msg = message.Message(b'addr', sample_data)
        addr_packet = message.Addr.from_message(msg)
        self.assertEqual(len(addr_packet.addresses), 500)
        address = addr_packet.addresses.pop()
        self.assertEqual(address.stream, 1)
        self.assertEqual(address.services, 1)
        self.assertEqual(address.port, 8444)
        self.assertEqual(address.host, '127.0.0.1')
