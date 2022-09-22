FROM ubuntu:focal

RUN apt-get update

RUN apt-get install -yq --no-install-suggests --no-install-recommends \
    python3-dev python3-pip python3.9 python3.9-dev python3.9-venv

RUN python3.9 -m pip install setuptools wheel
RUN python3.9 -m pip install --upgrade pip tox virtualenv
