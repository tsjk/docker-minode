FROM ubuntu:jammy

RUN apt-get update

RUN apt-get install -yq software-properties-common

RUN apt-add-repository ppa:purplei2p/i2pd && apt-get update -qq

RUN apt-get install -yq --no-install-suggests --no-install-recommends \
    python3-dev python3-pip python-is-python3 python3.11-dev python3.11-venv

RUN apt-get install -yq --no-install-suggests --no-install-recommends sudo i2pd

RUN echo 'builder ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

RUN pip install setuptools wheel
RUN pip install --upgrade pip tox virtualenv

ADD . .

CMD .buildbot/ubuntu/test.sh
