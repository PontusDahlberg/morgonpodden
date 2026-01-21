import requests

URLS = [
    ("Svd", "https://www.svd.se/rss.xml"),
    ("Reuters", "https://feeds.reuters.com/reuters/worldNews"),
    ("AP", "https://feeds.apnews.com/rss/topnews"),
    ("NyTeknik", "https://www.nyteknik.se/rss/senaste"),
    ("ComputerSweden", "https://computersweden.idg.se/rss/allanyheter"),
    ("Breakit", "https://www.breakit.se/feed"),
    ("ClimateCentral", "https://www.climatecentral.org/rss.xml"),
    ("CleanTechnica", "https://cleantechnica.com/feed/"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.7",
    "Accept-Language": "sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7",
}


def main() -> None:
    for name, url in URLS:
        try:
            r = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
            ct = r.headers.get("content-type", "")
            print(
                f"{name:14} status={r.status_code} bytes={len(r.content)} "
                f"ct={ct} final={r.url}"
            )
            head = (r.text[:160].replace("\n", " ") if r.text else "")
            print("  head:", head)
        except Exception as e:
            print(f"{name:14} ERROR {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
