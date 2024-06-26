FROM --platform=${TARGETPLATFORM:-${BUILDPLATFORM}} python:3.9-alpine

ARG TARGETPLATFORM

ENV PIP_ROOT_USER_ACTION=ignore

COPY . /app

RUN    apk upgrade --no-cache\
    && apk add --no-cache build-base linux-headers\
    && ( cd /app && pip install -r requirements.txt )

WORKDIR app

VOLUME ["/data"]

EXPOSE 8444

ENTRYPOINT ["python", "-m", "minode.main", "--data-dir", "/data"]
