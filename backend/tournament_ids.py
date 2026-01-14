import requests
from bs4 import BeautifulSoup
import re
import time

ARCHIVE_URL = "https://www.atptour.com/en/scores/results-archive?year=2024"
BASE_URL = "https://www.atptour.com"

resp = requests.get(ARCHIVE_URL)
soup = BeautifulSoup(resp.text, "html.parser")

tournament_ids = set()

# find all anchors that have a tournament link containing an ID
for a in soup.find_all("a", href=True):
    href = a["href"]
    # pattern for tournament pages
    m = re.search(r"/tournaments/[^/]+/(\d+)", href)
    if m:
        tournament_ids.add(m.group(1))
    # pattern for results pages
    m2 = re.search(r"/scores/\d+/\d+/results", href)
    if m2:
        # might also capture 2nd number as ID
        parts = href.split("/")
        if parts[-2].isdigit():
            tournament_ids.add(parts[-2])

# output
print("Tournament IDs (2025):")
print(len(tournament_ids))
for tid in tournament_ids:
    print(tid)
