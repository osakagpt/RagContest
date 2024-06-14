FROM postgres:latest

RUN apt-get update && \
    apt-get install -y git make gcc postgresql-server-dev-16


RUN cd /tmp && \
    git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git && \
    cd pgvector && \
    make && \
    make install && \
    cd ../ && \
    rm -rf pgvector

# Ensure the container is configured to use the pgvector extension
COPY init-db.sh /docker-entrypoint-initdb.d/
RUN chmod +x /docker-entrypoint-initdb.d/init-db.sh