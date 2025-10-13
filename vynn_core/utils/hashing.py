import hashlib
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

def url_hash(url: str) -> str:
    # Remove UTM params
    parsed = urlparse(url)
    query = [(k, v) for k, v in parse_qsl(parsed.query) if not k.lower().startswith("utm_")]
    clean_url = urlunparse(parsed._replace(query=urlencode(query)))
    return hashlib.sha256(clean_url.encode("utf-8")).hexdigest()
