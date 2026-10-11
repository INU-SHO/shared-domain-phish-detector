from bs4 import BeautifulSoup, Comment, Tag


IMPORTANT_TAGS: set[str] = {
    "head", "title", "meta", "body",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "strong", "a", "img", "hr",
    "table", "tbody", "tr", "th", "td",
    "ol", "ul", "li",
    "ruby", "label",
}

_TEXTLESS_EXEMPT: set[str] = {"head", "body", "title", "meta", "img", "a"}


def get_parsed_dom(dom_path: str, max_chars: int = 500_000, max_attr_len: int = 120) -> str:
    with open(dom_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    def dump() -> str:
        return soup.decode()

    def shorten_attr(v: str) -> str:
        v = (v or "").strip()
        if not v:
            return v
        if v.startswith("data:"):
            return v[:80] + "...(truncated)"
        if len(v) <= max_attr_len:
            return v
        head = v[: int(max_attr_len * 0.6)]
        tail = v[-int(max_attr_len * 0.2):]
        return f"{head}...(truncated)...{tail}"

    # 1) remove comments / script / style / br
    for c in soup.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    for t in soup.find_all(["script", "style", "br"]):
        if isinstance(t, Tag):
            t.decompose()

    # 2) if <= max_chars: return
    if len(dump()) <= max_chars:
        return dump()

    # 3) unwrap non-important tags
    for tag in list(soup.find_all(True)):
        if not isinstance(tag, Tag):
            continue
        name = (tag.name or "").lower()
        if name and name not in IMPORTANT_TAGS:
            tag.unwrap()

    # 4) remove elements without text (with minimal exemptions)
    for tag in list(soup.find_all(True)):
        if not isinstance(tag, Tag):
            continue
        name = (tag.name or "").lower()
        if name in _TEXTLESS_EXEMPT:
            continue
        if tag.get_text(strip=True):
            continue
        tag.decompose()

    # 5) shorten href/src
    for a in soup.find_all("a"):
        if not isinstance(a, Tag):
            continue
        href = a.get("href")
        if isinstance(href, str) and href:
            a["href"] = shorten_attr(href)

    for img in soup.find_all("img"):
        if not isinstance(img, Tag):
            continue
        src = img.get("src")
        if isinstance(src, str) and src:
            img["src"] = shorten_attr(src)

    # 6) if <= max_chars: return
    if len(dump()) <= max_chars:
        return dump()

    # 7) midpoint removal until under limit (prefer body scope)
    root = soup.body or soup
    while len(dump()) > max_chars:
        elems = [e for e in root.find_all(True) if isinstance(e, Tag)]
        if not elems:
            break
        elems[len(elems) // 2].decompose()

    return dump()


def get_title_from_dom(dom_path: str) -> str:
    with open(dom_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    title_tag = soup.find("title")
    if isinstance(title_tag, Tag):
        return title_tag.get_text().strip()
    return ""
