import unittest
from binascii import unhexlify

from minode import message


magic = 0xE9BEB4D9

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


class TestMessage(unittest.TestCase):
    """Test assembling and disassembling of network mesages"""

    def test_packet(self):
        """Check the packet created by message.Message()"""
        head = unhexlify(b'%x' % magic)
        self.assertEqual(
            message.Message(b'ping', b'').to_bytes()[:len(head)], head)

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
