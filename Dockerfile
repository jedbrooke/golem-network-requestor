FROM alpine:latest

# REQUIRED ssh utils
RUN apk add --no-cache --update bash openssh iproute2 tcpdump net-tools screen

# REQUIRED python to run the proxy server
RUN apk add --no-cache --update \
    python3 

# REQUIRED code to run the proxy server
COPY proxy_server.py /proxy_server.py
COPY util.py /util.py

# REQUIRED ssh server setup
RUN echo "UseDNS no" >> /etc/ssh/sshd_config && \
    echo "PermitRootLogin yes" >> /etc/ssh/sshd_config && \
    echo "PasswordAuthentication no" >> /etc/ssh/sshd_config

# OPTIONAL set up golem work volumes
VOLUME /golem/input /golem/output /golem/work
WORKDIR /golem/work

# OPTIONAL tools used in demo
RUN apk add --no-cache --update \
    curl \
    jq


