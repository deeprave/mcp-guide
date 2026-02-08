#!/bin/sh
set -e

# Build command as array
set -- mcp-guide http

# Add log configuration from environment
if [ -n "${LOG_LEVEL}" ]; then
    set -- "$@" --log-level "${LOG_LEVEL}"
fi

if [ "${LOG_JSON:-false}" = "true" ]; then
    set -- "$@" --log-json
fi

exec "$@"
