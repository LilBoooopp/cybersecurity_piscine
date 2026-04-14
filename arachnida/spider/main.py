import os
import requests
from bs4 import BeautifulSoup
import argparse
import hashlib

def spider(url, recursive, max_depth, save_path):
    queue = [(url, 0)]
    visited = set()

    while queue:
        item = queue.pop(0)
        current_url = item[0]
        if current_url in visited:
            continue
        visited.add(current_url)
        depth = item[1]
        if depth > max_depth:
            continue
        try:
            response = requests.get(current_url, timeout=5)
            if (response.status_code != 200):
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            images = soup.find_all("img")
            for img in images:
                src = img.get("src")
                if (not src or not src.startswith("http")) or (not src.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".bmp"))):
                    continue
                try:
                    response_img = requests.get(src, timeout=5)
                    url_hash = hashlib.md5(src.encode()).hexdigest()[:8]
                    ext = os.path.splitext(os.path.basename(src))[1]
                    filename = f"{url_hash}{ext}"
                    with open(save_path + filename, "wb") as f:
                        f.write(response_img.content)
                    print(f"Downloaded: {filename}")
                except Exception as e:
                    print(f"Failed to download image {src}: {e}")
            if (recursive):
                links = soup.find_all("a")
                for link in links:
                    href = link.get("href")
                    if (not href or not href.startswith("http")):
                        continue
                    queue.append((href, depth + 1))
        except Exception as e:
            print(f"Failed to fetch {current_url}: {e}")
            continue

parser = argparse.ArgumentParser(description="Spider = image scraper")
parser.add_argument("-r", action="store_true", help="recursive download")
parser.add_argument("-l", type=int, default=5, help="max depth")
parser.add_argument("-p", type=str, default="./data/", help="folder to store images")
parser.add_argument("url", type=str, help="URL to scrape")
args = parser.parse_args()

os.makedirs(args.p, exist_ok=True)

spider(args.url, args.r, args.l, args.p)
