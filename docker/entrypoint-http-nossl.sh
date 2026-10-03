#!/bin/sh
set -e

# Supply the image's transport only when the caller supplied options or no arguments.
case "${1:-}" in
    ""|-*) set -- http://0.0.0.0:8080 "$@" ;;
esac

exec mcp-guide "$@"
