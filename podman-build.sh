#!/bin/sh
if [ -n "${1}" ]; then
  echo "${1}" | grep -qE '^[0-9a-f]{40}$' || exit 2
  __COMMIT="${1}"; shift 1
else
  __COMMIT=$(git rev-parse HEAD)
fi
podman build --format docker --pull --layers --force-rm --build-arg COMMIT=${__COMMIT} --tag local/minode:${__COMMIT} . && \
  podman tag local/minode:${__COMMIT} local/minode:latest
