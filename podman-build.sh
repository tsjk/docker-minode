#!/bin/sh
podman build --format docker --pull --layers --force-rm --tag local/minode:latest .
