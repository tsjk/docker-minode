FROM ubuntu:focal

RUN apt-get update

RUN apt-get install -yq software-properties-common

RUN apt-add-repository ppa:purplei2p/i2pd
RUN apt-get update

RUN apt-get install -yq --no-install-suggests --no-install-recommends \
    python3-dev python3-pip python3.9 python3.9-dev python3.9-venv sudo i2pd

RUN echo 'builder ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

RUN python3.9 -m pip install setuptools wheel
RUN python3.9 -m pip install --upgrade pip tox virtualenv
