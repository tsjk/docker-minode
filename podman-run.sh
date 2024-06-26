#!/bin/sh

### This needs to be run either with host networking, or in the network namespace of an i2pd daemon.

HOST_IP_ADDRESS=$(ip route show | grep -E '^(default|0\.0\.0\.0(/0)?) ' | awk '{ if (match($0, /metric [0-9]+/, m)) { sub(/^metric /, "", m[0]); printf("%s", m[0]); }; print "|"$0; }' | sort -t '|' -k1n,1n | grep -Po '(?<= src )[0-9]{1,3}(\.[0-9]{1,3}){3}')
[ -n "${HOST_IP_ADDRESS}" ] && \
  podman run --rm --name minode --network=host -v minode-data:/data -e TZ="Etc/UTC" -d local/minode --host "${HOST_IP_ADDRESS}" --port 8444 --no-ip --i2p --i2p-tunnel-length 3 --i2p-sam-host 127.0.0.1 --i2p-sam-port 7656
