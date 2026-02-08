#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Generate SSL certificates for mcp-guide HTTPS transport.

OPTIONS:
    -s, --self          Generate self-signed certificates using mkcert
    -c, --certbot       Generate Let's Encrypt certificates using certbot
    -h, --help          Show this help message

EXAMPLES:
    $0 --self           # Generate self-signed certs with mkcert
    $0 --certbot        # Generate Let's Encrypt certs with certbot

REQUIREMENTS:
    --self:    mkcert must be installed (https://github.com/FiloSottile/mkcert)
    --certbot: certbot must be installed and domain must be publicly accessible

OUTPUT:
    Certificates are generated in: $SCRIPT_DIR/
    - cert.pem (certificate)
    - key.pem (private key)
EOF
    exit 0
}

check_mkcert() {
    if ! command -v mkcert &> /dev/null; then
        echo "Error: mkcert is not installed"
        echo "Install from: https://github.com/FiloSottile/mkcert"
        exit 1
    fi
}

generate_self_signed() {
    check_mkcert

    echo "Generating self-signed certificates with mkcert..."
    cd "$SCRIPT_DIR"

    mkcert -cert-file cert.pem -key-file key.pem localhost 127.0.0.1 ::1

    echo "✅ Self-signed certificates generated:"
    echo "   - $SCRIPT_DIR/cert.pem"
    echo "   - $SCRIPT_DIR/key.pem"
}

generate_certbot() {
    if ! command -v certbot &> /dev/null; then
        echo "Error: certbot is not installed"
        exit 1
    fi

    echo "Error: certbot integration not yet implemented"
    echo "Use --self for self-signed certificates"
    exit 1
}

case "${1:-}" in
    -s|--self)
        generate_self_signed
        ;;
    -c|--certbot)
        generate_certbot
        ;;
    -h|--help|"")
        usage
        ;;
    *)
        echo "Error: Unknown option: $1"
        usage
        ;;
esac
