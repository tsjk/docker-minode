FROM --platform=${TARGETPLATFORM:-${BUILDPLATFORM}} python:3.9-alpine

ARG TARGETPLATFORM
ARG COMMIT

ENV PIP_ROOT_USER_ACTION=ignore

COPY ./minode-patches/* /tmp/minode-patches/

RUN    apk upgrade --no-cache\
    && apk add --no-cache build-base git linux-headers patch\
    && mkdir /app\
    && (    cd /app\
         && git clone https://github.com/tsjk/docker-minode.git .\
         && git checkout ${COMMIT}\
         && if [ $(ls -1 /tmp/minode-patches/*.patch 2> /dev/null | wc -l) -gt 0 ]; then\
              for p in /tmp/minode-patches/*.patch; do patch -p1 < "${p}" || exit 1; done; fi\
         && pip install -r requirements.txt )\
    && rm -rf /tmp/minode-patches

WORKDIR /app

VOLUME ["/data"]

EXPOSE 8444

ENTRYPOINT ["python", "-m", "minode.main", "--data-dir", "/data"]
