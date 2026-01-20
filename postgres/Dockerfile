# PostgreSQL 15 - Blacklist Intelligence Platform
FROM postgres:15-alpine

LABEL maintainer="NextRade <dev@jclee.me>"
LABEL description="PostgreSQL 15 for Blacklist Intelligence Platform"

ARG BUILD_DATE
ARG VCS_REF

LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.title="blacklist-postgres"

ENV POSTGRES_DB=blacklist
ENV POSTGRES_USER=postgres
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

COPY initdb/ /docker-entrypoint-initdb.d/

HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
    CMD pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB} || exit 1

EXPOSE 5432
