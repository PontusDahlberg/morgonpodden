import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

URL = "https://www.nwt.se/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def main() -> None:
    r = requests.get(URL, headers=HEADERS, timeout=20, allow_redirects=True)
    print("status=", r.status_code, "final=", r.url, "bytes=", len(r.content), "ct=", r.headers.get("content-type", ""))

    soup = BeautifulSoup(r.text, "html.parser")
    found = set()

    for tag in soup.find_all(["a", "link"]):
        href = tag.get("href")
        if not href:
            continue
        if any(k in href.lower() for k in ["rss", "feed", "atom", ".xml"]):
            found.add(urljoin(r.url, href))

    for m in re.finditer(r"https?://[^\s\"'>]+", r.text):
        u = m.group(0)
        if any(k in u.lower() for k in ["rss", "feed", "atom", ".xml"]):
            found.add(u.split("#")[0])

    found = sorted(found)
    print("candidates:", len(found))
    for u in found[:50]:
        print(" -", u)


if __name__ == "__main__":
    main()
