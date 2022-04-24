FROM ubuntu:bionic AS bionic

RUN apt-get update

RUN apt-get install -yq --no-install-suggests --no-install-recommends \
    python3-dev python3-pip python3.8 python3.8-dev python3.8-venv

RUN python3.8 -m pip install setuptools wheel
RUN python3.8 -m pip install --upgrade pip tox virtualenv
