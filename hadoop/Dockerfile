FROM debian:bookworm-slim
ARG HADOOP_VERSION=3.4.1
ENV DEBIAN_FRONTEND=noninteractive \
    JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
    HADOOP_HOME=/opt/hadoop \
    HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop \
    PATH=/opt/hadoop/bin:/opt/hadoop/sbin:$PATH
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jdk-headless python3 python3-pip python3-psycopg2 openssh-server \
    openssh-client curl ca-certificates procps tini && \
    rm -rf /var/lib/apt/lists/* && \
    curl -fSL --retry 3 "https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz" -o /tmp/hadoop.tgz && \
    mkdir -p /opt && tar -xzf /tmp/hadoop.tgz -C /opt && \
    mv "/opt/hadoop-${HADOOP_VERSION}" /opt/hadoop && rm /tmp/hadoop.tgz && \
    useradd -m -s /bin/bash hadoop && mkdir -p /run/sshd /data/output /shared-ssh && \
    chown -R hadoop:hadoop /data/output && \
    printf 'PermitRootLogin no\nPasswordAuthentication no\nPubkeyAuthentication yes\n' > /etc/ssh/sshd_config.d/90-datamart.conf && \
    printf 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64\n' >> /opt/hadoop/etc/hadoop/hadoop-env.sh && \
    printf 'export HADOOP_OPTS="-Djava.library.path=$HADOOP_HOME/lib/native"\n' >> /opt/hadoop/etc/hadoop/hadoop-env.sh
COPY mapreduce/ /opt/proyecto/mapreduce/
COPY scripts/ /opt/proyecto/scripts/
COPY hadoop/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh /opt/proyecto/scripts/ejecutar_pipeline.sh && \
    chown -R hadoop:hadoop /opt/proyecto
EXPOSE 22
ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]
