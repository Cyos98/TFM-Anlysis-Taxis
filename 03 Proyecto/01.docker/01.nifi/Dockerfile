FROM apache/nifi:2.10.0

USER root

ADD --checksum=sha256:1981b31d3993c58702783c1cddf10a34e48c1f413d70ff1cb6def0a143484647 \
    https://repo.maven.apache.org/maven2/org/postgresql/postgresql/42.7.11/postgresql-42.7.11.jar \
    /opt/nifi/drivers/postgresql-42.7.11.jar

ADD --checksum=sha256:5e72cc7dd028ed79fb96e18c65b08c4ceddaebb3fd6c14dfc786d4ca380e7abb \
    https://repo.maven.apache.org/maven2/org/apache/nifi/nifi-hadoop-libraries-nar/2.10.0/nifi-hadoop-libraries-nar-2.10.0.nar \
    /opt/nifi/nifi-current/lib/nifi-hadoop-libraries-nar-2.10.0.nar

ADD --checksum=sha256:b65cfd66ff70c32b8caa6e79d3bbb627295bb1e7bad684689d222134314e9ad3 \
    https://repo.maven.apache.org/maven2/org/apache/nifi/nifi-parquet-nar/2.10.0/nifi-parquet-nar-2.10.0.nar \
    /opt/nifi/nifi-current/lib/nifi-parquet-nar-2.10.0.nar

RUN chown -R nifi:nifi \
    /opt/nifi/drivers \
    /opt/nifi/nifi-current/lib/nifi-hadoop-libraries-nar-2.10.0.nar \
    /opt/nifi/nifi-current/lib/nifi-parquet-nar-2.10.0.nar

USER nifi
