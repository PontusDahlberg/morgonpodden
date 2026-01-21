import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

SITES = [
    ("SvD", "https://www.svd.se/"),
    ("NyTeknik", "https://www.nyteknik.se/"),
    ("ComputerSweden", "https://computersweden.se/"),
    ("Breakit", "https://www.breakit.se/"),
    ("ClimateCentral", "https://www.climatecentral.org/"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7",
}


def extract_candidate_urls(html: str) -> list[str]:
    # crude regex for any URLs that look like feeds
    found = set()
    for m in re.finditer(r"https?://[^\s\"'>]+", html):
        u = m.group(0)
        if any(k in u.lower() for k in ["rss", "feed", "atom", ".xml"]):
            found.add(u.split("#")[0])
    return sorted(found)


def main() -> None:
    for name, url in SITES:
        print("\n===", name, url)
        try:
            r = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
            print("status=", r.status_code, "final=", r.url, "bytes=", len(r.content), "ct=", r.headers.get("content-type", ""))
            soup = BeautifulSoup(r.text, "html.parser")

            # <link rel="alternate" type="application/rss+xml" ...>
            links = []
            for link in soup.find_all("link"):
                rel = (link.get("rel") or [])
                rel = [x.lower() for x in rel]
                typ = (link.get("type") or "").lower()
                href = link.get("href")
                if not href:
                    continue
                if "alternate" in rel and any(x in typ for x in ["rss", "atom", "xml"]):
                    links.append(urljoin(r.url, href))

            # Also scan for anchors with rss/feed in href
            for a in soup.find_all("a"):
                href = a.get("href")
                if not href:
                    continue
                if any(k in href.lower() for k in ["rss", "feed", "atom", ".xml"]):
                    links.append(urljoin(r.url, href))

            links = sorted(set(links))
            if links:
                print("discovered_links:")
                for l in links[:30]:
                    print(" -", l)
            else:
                print("discovered_links: (none in link/a tags)")

            candidates = extract_candidate_urls(r.text)
            if candidates:
                print("regex_candidates:")
                for c in candidates[:30]:
                    print(" -", c)
        except Exception as e:
            print("ERROR", type(e).__name__, e)


if __name__ == "__main__":
    main()
