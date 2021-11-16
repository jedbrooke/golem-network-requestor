FROM alpine:latest

RUN apk add --no-cache --update bash openssh iproute2 tcpdump net-tools screen

# misc packages
RUN apk add --no-cache --update \
    python3 \
    curl \
    jq

RUN echo "UseDNS no" >> /etc/ssh/sshd_config && \
    echo "PermitRootLogin yes" >> /etc/ssh/sshd_config && \
    echo "PasswordAuthentication no" >> /etc/ssh/sshd_config


VOLUME /golem/input /golem/output /golem/work
WORKDIR /golem/work

COPY proxy_server.py /proxy_server.py
RUN ls /golem/input
