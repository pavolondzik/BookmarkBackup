from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


def normalize_url(url: str) -> str:
    """
    Canonical form for duplicate detection.

    Rules:
    - scheme and host lowercased
    - default ports removed (http:80, https:443)
    - www. stripped from host
    - fragment removed
    - trailing slash removed from path (except root '/')
    - query params sorted alphabetically
    """
    parsed = urlparse(url.strip())
    if not parsed.scheme or not parsed.netloc:
        return url.strip()

    scheme = parsed.scheme.lower()
    host = parsed.hostname or ""
    if host.startswith("www."):
        host = host[4:]

    port = parsed.port
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{host}:{port}"
    else:
        netloc = host

    path = parsed.path or ""
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)))

    return urlunparse((scheme, netloc, path, "", query, ""))
