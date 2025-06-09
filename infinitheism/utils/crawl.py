import asyncio
import json
import re
from pathlib import Path
from urllib.parse import urlparse, urljoin

import aiohttp
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from torch_snippets import writelines, P, makedir, exists

# --- Config & Globals ---
DOMAIN = "infinitheism.com"
DATA_DIR = Path("data/scraped")
VISITED_FILE = DATA_DIR / "visited.json"
QUEUE_FILE = DATA_DIR / "queue.json"
CONTENT_DIR = DATA_DIR / "content"
CRAWL_LIMIT = 50000
EXCLUDE = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.mp4', '.mp3', '.zip', '.tar', '.gz', 'category', 'cart', 'checkout', 'enroll', 'author', 'page']

visited = set()
crawled = 0

# --- Persistence Utilities ---
def load_json(path, default):
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f)

def load_queue():
    return load_json(QUEUE_FILE, [])

def save_queue(queue):
    save_json(QUEUE_FILE, queue)

def load_visited():
    return set(load_json(VISITED_FILE, []))

def save_visited():
    save_json(VISITED_FILE, list(visited))

# --- Path Utilities ---
def url2path(url):
    return P(CONTENT_DIR / (f'{urlparse(url).netloc}{urlparse(url).path}'.replace('/', '__').strip("__") + '.md'))

def write_to_file(url, markdown):
    path = url2path(url)
    makedir(path.parent)
    writelines([markdown], path, 'w')

# --- Link Extraction ---
async def extract_links(markdown, base_url):
    links = set()
    for match in re.findall(r'\[.*?\]\((.*?)\)', markdown):
        href = urljoin(base_url, match)
        if DOMAIN in urlparse(href).netloc:
            links.add(href.split('#')[0])
    return links

# --- Crawler Logic ---
async def crawl_and_scrape(url, crawler, session):
    global crawled
    try:
        if url in visited or DOMAIN not in urlparse(url).netloc:
            return []
        visited.add(url)
        print(f"[CRAWLING] {url}")
        result = await crawler.arun(url=url)
        if not result.success:
            print(f"[ERROR] {url} => {result.error_message}")
            return []
        write_to_file(url, result.markdown)
        links = await extract_links(result.markdown, url)
        save_visited()
        crawled += 1
        if crawled > CRAWL_LIMIT:
            raise Exception("Crawled too many pages, stopping to avoid infinite loop.")
        return list(links)
    except Exception as e:
        print(f"[SCRAPE EXCEPTION] {url} => {str(e)}")
        return []

# --- Entry Point ---
async def main(seed_url):
    run_conf = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    global visited
    visited = load_visited()
    async with AsyncWebCrawler() as crawler, aiohttp.ClientSession() as session:
        to_crawl = load_queue() or [seed_url]
        try:
            while to_crawl:
                next_batch = []
                for url in to_crawl:
                    if any(ext in url for ext in EXCLUDE):
                        print(f"[EXCLUDED] {url} due to file type or path.")
                        continue
                    if exists(url2path(url)):
                        print(f"[SKIPPING] {url} already exists.")
                        continue
                    new_links = await crawl_and_scrape(url, crawler, session)
                    next_batch.extend(new_links)
                to_crawl = [link for link in next_batch if link not in visited]
                save_queue(to_crawl)
        except Exception as e:
            print(f"[EXCEPTION] {str(e)}")

if __name__ == '__main__':
    asyncio.run(main(f'https://{DOMAIN}'))