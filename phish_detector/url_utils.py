from urllib.parse import urlparse

import tldextract


def extract_apex_domain(url: str) -> str:
    host = urlparse(url).netloc or urlparse("https://" + url).netloc
    host = host.split("@")[-1].split(":")[0]

    ext = tldextract.extract(host)
    if not ext.domain or not ext.suffix:
        raise ValueError(f"cannot extract apex domain: {url}")

    return f"{ext.domain}.{ext.suffix}"
