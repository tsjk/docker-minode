"""Tests for structures"""
import unittest
import struct
from binascii import unhexlify

from minode import structure


class TestStructure(unittest.TestCase):
    """Testing structures serializing and deserializing"""

    def test_varint(self):
        """Test varint serializing and deserializing"""
        s = structure.VarInt(0)
        self.assertEqual(s.to_bytes(), b'\x00')
        s = structure.VarInt.from_bytes(b'\x00')
        self.assertEqual(s.n, 0)
        s = structure.VarInt(42)
        self.assertEqual(s.to_bytes(), b'*')
        s = structure.VarInt.from_bytes(b'*')
        self.assertEqual(s.n, 42)
        s = structure.VarInt(252)
        self.assertEqual(s.to_bytes(), unhexlify('fc'))
        s = structure.VarInt.from_bytes(unhexlify('fc'))
        self.assertEqual(s.n, 252)
        s = structure.VarInt(253)
        self.assertEqual(s.to_bytes(), unhexlify('fd00fd'))
        s = structure.VarInt.from_bytes(unhexlify('fd00fd'))
        self.assertEqual(s.n, 253)
        s = structure.VarInt(100500)
        self.assertEqual(s.to_bytes(), unhexlify('fe00018894'))
        s = structure.VarInt.from_bytes(unhexlify('fe00018894'))
        self.assertEqual(s.n, 100500)
        s = structure.VarInt(65535)
        self.assertEqual(s.to_bytes(), unhexlify('fdffff'))
        s = structure.VarInt.from_bytes(unhexlify('fdffff'))
        self.assertEqual(s.n, 65535)
        s = structure.VarInt(4294967295)
        self.assertEqual(s.to_bytes(), unhexlify('feffffffff'))
        s = structure.VarInt.from_bytes(unhexlify('feffffffff'))
        self.assertEqual(s.n, 4294967295)
        s = structure.VarInt(4294967296)
        self.assertEqual(s.to_bytes(), unhexlify('ff0000000100000000'))
        s = structure.VarInt.from_bytes(unhexlify('ff0000000100000000'))
        self.assertEqual(s.n, 4294967296)
        s = structure.VarInt(18446744073709551615)
        self.assertEqual(s.to_bytes(), unhexlify('ffffffffffffffffff'))
        s = structure.VarInt.from_bytes(unhexlify('ffffffffffffffffff'))
        self.assertEqual(s.n, 18446744073709551615)

    def test_address(self):
        """Check address encoding in structure.NetAddrNoPrefix()"""
        addr = structure.NetAddrNoPrefix(1, '127.0.0.1', 8444)
        self.assertEqual(
            addr.to_bytes()[8:24],
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xFF'
            + struct.pack('>L', 2130706433))
        addr = structure.NetAddrNoPrefix(1, '191.168.1.1', 8444)
        self.assertEqual(
            addr.to_bytes()[8:24],
            unhexlify('00000000000000000000ffffbfa80101'))
        addr = structure.NetAddrNoPrefix(1, '1.1.1.1', 8444)
        self.assertEqual(
            addr.to_bytes()[8:24],
            unhexlify('00000000000000000000ffff01010101'))
        addr = structure.NetAddrNoPrefix(
            1, '0102:0304:0506:0708:090A:0B0C:0D0E:0F10', 8444)
        self.assertEqual(
            addr.to_bytes()[8:24],
            unhexlify('0102030405060708090a0b0c0d0e0f10'))
