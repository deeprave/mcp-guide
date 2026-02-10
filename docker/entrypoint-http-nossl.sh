#!/bin/sh
set -e

# Build command as array
set -- mcp-guide http

# Add log configuration from environment
if [ -n "${LOG_LEVEL}" ]; then
    set -- "$@" --log-level "${LOG_LEVEL}"
fi

if [ "$(printf '%s' "${LOG_JSON:-false}" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
    set -- "$@" --log-json
fi

exec "$@"
