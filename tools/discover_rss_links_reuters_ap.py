import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

SITES = [
    ("Reuters", "https://www.reuters.com/"),
    ("AP", "https://apnews.com/"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,sv-SE;q=0.7,sv;q=0.6",
}


def main() -> None:
    for name, url in SITES:
        print("\n===", name, url)
        try:
            r = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
            print("status=", r.status_code, "final=", r.url, "bytes=", len(r.content), "ct=", r.headers.get("content-type", ""))

            soup = BeautifulSoup(r.text, "html.parser")
            found = set()

            for tag in soup.find_all(["a", "link"]):
                href = tag.get("href")
                if not href:
                    continue
                if any(k in href.lower() for k in ["rss", "feed", "atom", ".xml"]):
                    found.add(urljoin(r.url, href))

            # regex sweep too
            for m in re.finditer(r"https?://[^\s\"'>]+", r.text):
                u = m.group(0)
                if any(k in u.lower() for k in ["rss", "feed", "atom", ".xml"]):
                    found.add(u.split("#")[0])

            found = sorted(found)
            if found:
                print("found_candidates:")
                for f in found[:50]:
                    print(" -", f)
            else:
                print("found_candidates: (none)")
        except Exception as e:
            print("ERROR", type(e).__name__, e)


if __name__ == "__main__":
    main()
