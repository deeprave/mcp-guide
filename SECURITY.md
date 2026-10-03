# Security Policy

## Deployment and Trust Boundaries

Guide exposes project configuration, permission settings and documents through
MCP. Tools can mutate server-side state. Treat access to an unprotected server
as trusted access, not as a read-only document service.

Stdio is intended for trusted local clients. HTTP and HTTPS default to
localhost; listening on other interfaces requires an explicit transport URL,
such as `https://0.0.0.0:8443`.

HTTPS encrypts traffic but does not authenticate callers. Authentication is
optional: without `--auth-provider`, operations remain available without
authentication. Configure a provider or restrict access at the network or
reverse-proxy boundary before exposing the server to untrusted callers.

For remote deployments, use direct HTTPS or HTTP behind a TLS-terminating
reverse proxy. Administrators and providers own TLS, proxy and header-trust
policy; Guide does not enforce those deployment policies.

## Authentication and Isolation

A configured provider supplies request authorisation. Guide requires `user`
or `admin` access for protected operations; `admin` grants unrestricted access.
Missing authentication or insufficient access must not permit protected
mutations. Provider validation failures must not fall back to trusted access.

Authentication is not tenant isolation. Project names, paths and checksums are
not ownership or access-control boundaries. Do not assume separate callers
have isolated projects, documents or configuration.

## Reporting a Vulnerability

Do not include credentials, private documents or sensitive deployment details
in public reports. If no private reporting channel is available, open a
repository issue requesting one without disclosing sensitive details.
