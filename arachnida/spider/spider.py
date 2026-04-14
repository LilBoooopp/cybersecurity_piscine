import os
import requests
from bs4 import BeautifulSoup
import argparse
import hashlib
from urllib.parse import urlparse
import ipaddress
import socket

def is_safe_url(url):
    try:
        parsed = urlparse(url)

        # block non-http
        if parsed.scheme not in ("http", "https"):
            return False

        # block localhost
        if parsed.hostname in ("localhost", "127.0.0.1", "::1"):
            return False

        # resolve hostname to ip and check if private
        ip = ipaddress.ip_address(socket.gethostbyname(parsed.hostname))
        if ip.is_private:
            return False
        
        return True
    except Exception:
        return False

def spider(url, recursive, max_depth, save_path):
    queue = [(url, 0)]
    visited = set()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

    while queue:
        item = queue.pop(0)
        current_url = item[0]
        if current_url in visited or not is_safe_url(current_url):
            continue
        visited.add(current_url)
        depth = item[1]
        if depth > max_depth:
            continue
        try:
            response = requests.get(current_url, headers=headers, timeout=5)
            if (response.status_code != 200):
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            images = soup.find_all("img")
            for img in images:
                src = img.get("src")
                if (not src or not src.startswith("http")) or (not src.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".bmp"))):
                    continue
                try:
                    response_img = requests.get(src, headers=headers, timeout=5)
                    url_hash = hashlib.md5(src.encode()).hexdigest()[:8]
                    ext = os.path.splitext(os.path.basename(src))[1]
                    filename = f"{url_hash}{ext}"
                    with open(os.path.join(save_path, filename), "wb") as f:
                        f.write(response_img.content)
                    yield filename
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spider = image scraper")
    parser.add_argument("-r", action="store_true", help="recursive download")
    parser.add_argument("-l", type=int, default=5, help="max depth")
    parser.add_argument("-p", type=str, default="./data/", help="folder to store images")
    parser.add_argument("url", type=str, help="URL to scrape")
    args = parser.parse_args()
    
    os.makedirs(args.p, exist_ok=True)
    
    for filename in spider(args.url, args.r, args.l, args.p):
        print(f"Downloaded: {filename}")
