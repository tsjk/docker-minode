#!/bin/sh

DOCKERFILE=.buildbot/ubuntu/Dockerfile

docker build -t minode/tox -f $DOCKERFILE .

if [ $? -gt 0 ]; then
    docker build --no-cache -t minode/tox -f $DOCKERFILE .
fi

docker run --rm -it minode/tox
