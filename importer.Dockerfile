FROM debian:12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl unzip libunwind8 libicu72 ca-certificates && \
    curl -L -o /tmp/sqlpackage.zip https://aka.ms/sqlpackage-linux && \
    unzip /tmp/sqlpackage.zip -d /opt/sqlpackage && \
    chmod a+x /opt/sqlpackage/sqlpackage && \
    rm -rf /var/lib/apt/lists/* /tmp/sqlpackage.zip

VOLUME ["/data"]
