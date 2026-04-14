import os
import requests
from bs4 import BeautifulSoup
import argparse

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
        response = requests.get(current_url)
        if (response.status_code != 200):
            continue
        soup = BeautifulSoup(response.text, "html.parser")
        images = soup.find_all("img")
        for img in images:
            src = img.get("src")
            if (not src or not src.startswith("http")) or (not src.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".bmp"))):
                continue
            response_img = requests.get(src)
            with open(save_path + os.path.basename(src), "wb") as f:
                f.write(response_img.content)
        if (recursive):
            links = soup.find_all("a")
            for link in links:
                href = link.get("href")
                if (not href or not href.startswith("http")):
                    continue
                queue.append((href, depth + 1))

parser = argparse.ArgumentParser(description="Spider = image scraper")
parser.add_argument("-r", action="store_true", help="recursive download")
parser.add_argument("-l", type=int, default=5, help="max depth")
parser.add_argument("-p", type=str, default="./data/", help="folder to store images")
parser.add_argument("url", type=str, help="URL to scrape")
args = parser.parse_args()

os.makedirs(args.p, exist_ok=True)

spider(args.url, args.r, args.l, args.p)
