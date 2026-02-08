#!/bin/sh
set -e

# Default cert paths
CERT_FILE="${SSL_CERTFILE:-/certs/cert.pem}"
KEY_FILE="${SSL_KEYFILE:-/certs/key.pem}"

# Build command as array
set -- mcp-guide https

# Add log configuration from environment
if [ -n "${LOG_LEVEL}" ]; then
    set -- "$@" --log-level "${LOG_LEVEL}"
fi

if [ "${LOG_JSON:-false}" = "true" ]; then
    set -- "$@" --log-json
fi

# Add SSL certificates if present
if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
    set -- "$@" --ssl-certfile "$CERT_FILE" --ssl-keyfile "$KEY_FILE"
fi

exec "$@"
