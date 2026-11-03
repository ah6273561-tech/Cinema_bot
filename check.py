import requests, json, os, time
from urllib.parse import urljoin
from bs4 import BeautifulSoup

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
FILE = "seen.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

SITES = [
    {
        "name": "Scene",
        "url": "https://cfc.scenecinemas.com/home",
        "selector": 'a[href*="/movie-details/"]',
        "skip": [],
    },
    {
        "name": "VOX",
        "url": "https://egy.voxcinemas.com/movies/whatson",
        "selector": 'a[href^="/movies/"]',
        "skip": ["/movies/whatson", "/movies/comingsoon"],
    },
]


def fetch(url):
    for attempt in range(3):
        try:
            return requests.get(url, timeout=(10, 40), headers=HEADERS).text
        except requests.exceptions.RequestException as e:
            print(f"محاولة {attempt + 1} فشلت: {e}")
            time.sleep(5)
    return None


movies = {}  # الرابط الكامل -> (اسم الفيلم, اسم السينما)

for site in SITES:
    html = fetch(site["url"])
    if html is None:
        print(site["name"], "مش راضي يفتح، هنكمل بالباقي")
        continue
    soup = BeautifulSoup(html, "html.parser")
    count = 0
    for a in soup.select(site["selector"]):
        href = a["href"].split("?")[0].split("#")[0].rstrip("/")
        if any(href.endswith(s) for s in site["skip"]):
            continue
        name = a.get("title") or a.get_text(" ", strip=True)
        if name:
            movies[urljoin(site["url"], href)] = (name, site["name"])
            count += 1
    print(site["name"], "- لقيت", count, "فيلم")

if not movies:
    print("مفيش أفلام اتقرأت")
    raise SystemExit

seen = set(json.load(open(FILE))) if os.path.exists(FILE) else None

if seen is not None:
    for link in movies.keys() - seen:
        name, cinema = movies[link]
        requests.get(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            params={
                "chat_id": CHAT_ID,
                "text": f"فيلم جديد نزل ({cinema}):\n{name}\n{link}",
            },
        )

json.dump(sorted((seen or set()) | set(movies)), open(FILE, "w"), ensure_ascii=False)
