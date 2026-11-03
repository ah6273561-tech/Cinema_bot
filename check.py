import requests, json, os, time
from urllib.parse import urljoin
from bs4 import BeautifulSoup

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
FILE = "seen.json"

URL = "https://egy.voxcinemas.com/movies/whatson"
SKIP = ["/movies/whatson", "/movies/comingsoon"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

html = None
for attempt in range(3):
    try:
        html = requests.get(URL, timeout=(10, 40), headers=HEADERS).text
        break
    except requests.exceptions.RequestException as e:
        print(f"محاولة {attempt + 1} فشلت: {e}")
        time.sleep(5)

if html is None:
    print("الموقع مش راضي يفتح، هنحاول في التشغيل الجاي")
    raise SystemExit

soup = BeautifulSoup(html, "html.parser")

movies = {}
for a in soup.select('a[href^="/movies/"]'):
    href = a["href"].split("?")[0].split("#")[0].rstrip("/")
    if any(href.endswith(s) for s in SKIP):
        continue
    name = a.get("title") or a.get_text(" ", strip=True)
    if name:
        movies[urljoin(URL, href)] = name

print("لقيت", len(movies), "فيلم")

if not movies:
    print("مفيش أفلام اتقرأت")
    raise SystemExit

seen = set(json.load(open(FILE))) if os.path.exists(FILE) else None

if seen is not None:
    for link in movies.keys() - seen:
        requests.get(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            params={
                "chat_id": CHAT_ID,
                "text": f"فيلم جديد نزل في فوكس:\n{movies[link]}\n{link}",
            },
        )

json.dump(sorted((seen or set()) | set(movies)), open(FILE, "w"), ensure_ascii=False)
