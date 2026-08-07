# HolmesGPT server + docker CLI so the docker/core toolset can talk to the
# host daemon through the mounted socket.
FROM us-central1-docker.pkg.dev/genuine-flight-317411/devel/holmes:latest

USER root
RUN curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-27.3.1.tgz \
    | tar -xz --strip-components=1 -C /usr/local/bin docker/docker \
    && docker --version
