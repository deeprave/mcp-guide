#!/bin/sh
set -e

# The CLI owns MG_* configuration and gives explicit options precedence.
if [ -z "${MG_SSL_CERTFILE:-}" ] && [ -f /home/mcp/certs/cert.pem ]; then
    export MG_SSL_CERTFILE=/home/mcp/certs/cert.pem
fi
if [ -z "${MG_SSL_KEYFILE:-}" ] && [ -f /home/mcp/certs/key.pem ]; then
    export MG_SSL_KEYFILE=/home/mcp/certs/key.pem
fi

# Supply the image's transport only when the caller supplied options or no arguments.
case "${1:-}" in
    ""|-*) set -- https://0.0.0.0:8443 "$@" ;;
esac

exec mcp-guide "$@"
