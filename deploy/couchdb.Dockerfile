FROM couchdb:3.3.3

# Copy custom CouchDB configuration
COPY couchdb-config.ini /opt/couchdb/etc/local.d/brainplorp.ini

# CouchDB listens on port 5984
EXPOSE 5984

# Data directory for persistent volume
VOLUME /opt/couchdb/data

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:5984/_up || exit 1
