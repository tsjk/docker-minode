# MiNode

[![Testing](https://git.bitmessage.org/Bitmessage/MiNode/actions/workflows/test.yml/badge.svg)](https://git.bitmessage.org/Bitmessage/MiNode/actions?workflow=test.yml)

Python 3 implementation of the Bitmessage protocol. Designed only to route
objects inside the network.

## Requirements
- python3 (or pypy3)
- openssl

## Running
```
git clone https://git.bitmessage.org/Bitmessage/MiNode.git
```
```
cd MiNode
./start.sh
```

It is worth noting that the `start.sh` script no longer tries to do a
`git pull` in order to update to the latest version.
Is is now done by the `update.sh` script.

## Command line
```
usage: main.py [-h] [-p PORT] [--host HOST] [--debug] [--data-dir DATA_DIR]
               [--no-incoming] [--no-outgoing] [--no-ip]
               [--trusted-peer TRUSTED_PEER]
               [--connection-limit CONNECTION_LIMIT] [--i2p]
               [--i2p-tunnel-length I2P_TUNNEL_LENGTH]
               [--i2p-sam-host I2P_SAM_HOST] [--i2p-sam-port I2P_SAM_PORT]
               [--i2p-transient]

optional arguments:
  -h, --help            show this help message and exit
  -p PORT, --port PORT  Port to listen on
  --host HOST           Listening host
  --debug               Enable debug logging
  --data-dir DATA_DIR   Path to data directory
  --no-incoming         Do not listen for incoming connections
  --no-outgoing         Do not send outgoing connections
  --no-ip               Do not use IP network
  --trusted-peer TRUSTED_PEER
                        Specify a trusted peer we should connect to
  --connection-limit CONNECTION_LIMIT
                        Maximum number of connections
  --i2p                 Enable I2P support (uses SAMv3)
  --i2p-tunnel-length I2P_TUNNEL_LENGTH
                        Length of I2P tunnels
  --i2p-sam-host I2P_SAM_HOST
                        Host of I2P SAMv3 bridge
  --i2p-sam-port I2P_SAM_PORT
                        Port of I2P SAMv3 bridge
  --i2p-transient       Generate new I2P destination on start

```

## I2P support
MiNode has support for connections over I2P network.
To use it it needs an I2P router with SAMv3 activated
(both Java I2P and i2pd are supported). Keep in mind that I2P connections
are slow and full synchronization may take a while.

### Examples
Connect to both IP and I2P networks (SAM bridge on default host and port
127.0.0.1:7656) and set tunnel length to 3 (default is 2).
```
$ ./start.sh --i2p --i2p-tunnel-length 3
```

Connect only to I2P network and listen for IP connections only from local
machine.
```
$ ./start.sh --i2p --no-ip --host 127.0.0.1
```
or
```
$ ./i2p_bridge.sh
```
If you add `trustedpeer = 127.0.0.1:8444` to `keys.dat` file in PyBitmessage it
will allow you to use it anonymously over I2P with MiNode acting as a bridge.

## Contact
- lee.miller: BM-2cX1pX2goWAuZB5bLqj17x23EFjufHmygv

## Links
- [Bitmessage project website](https://bitmessage.org)
- [Protocol specification](https://pybitmessage.rtfd.io/en/v0.6/protocol.html)
