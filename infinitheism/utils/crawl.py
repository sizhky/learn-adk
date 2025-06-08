from torch_snippets import writelines, P, makedir, exists
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import aiohttp
import json
from pathlib import Path

visited_file = Path('data/scraped/visited.json')

queue_file = Path('data/scraped/queue.json')
crawled = 0

def load_queue():
    if queue_file.exists():
        with open(queue_file, 'r') as f:
            return list(json.load(f))
    return []

def save_queue(queue):
    with open(queue_file, 'w') as f:
        json.dump(queue, f)

def load_visited():
    if visited_file.exists():
        with open(visited_file, 'r') as f:
            return set(json.load(f))
    return set()

def save_visited():
    with open(visited_file, 'w') as f:
        json.dump(list(visited), f)

visited = load_visited()

import re

async def extract_links(markdown, base_url):
    links = set()
    for match in re.findall(r'\[.*?\]\((.*?)\)', markdown):
        href = urljoin(base_url, match)
        if "infinitheism.com" in urlparse(href).netloc:
            links.add(href.split('#')[0])
    return links

async def fetch_content(session, url):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.text()
    except Exception:
        return None

async def crawl_and_scrape(url, crawler, session, write_to_file_fn):
    try:
        global crawled
        if url in visited:
            return []
        if "infinitheism.com" not in urlparse(url).netloc:
            return []
        visited.add(url)

        print(f"[CRAWLING] {url}")

        result = await crawler.arun(url=url)
        if not result.success:
            print(f"[ERROR] {url} => {result.error_message}")
            return []

        write_to_file_fn(url, result.markdown)
        links = await extract_links(result.markdown, url)
        save_visited()
        crawled += 1
        if crawled > 50000:
            raise Exception("Crawled too many pages, stopping to avoid infinite loop.")
        return list(links)
    except Exception as e:
        print(f"[SCRAPE EXCEPTION] {url} => {str(e)}")
        return []

async def main(root_url):
    run_conf = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler() as crawler, aiohttp.ClientSession() as session:
        to_crawl = load_queue() or [root_url]
        try:
            while to_crawl:
                next_batch = []
                for url in to_crawl:
                    if any(extn in url for extn in ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.mp4', '.mp3', '.zip', '.tar', '.gz', 'category', 'cart', 'checkout', 'enroll', 'author']):
                        continue
                    if exists(url2path(url)):
                        print(f"[SKIPPING] {url} already exists.")
                        continue
                    new_links = await crawl_and_scrape(url, crawler, session, write_to_file)
                    next_batch.extend(new_links)
                to_crawl = [link for link in next_batch if link not in visited]
                save_queue(to_crawl)
        except Exception as e:
            print(f"[EXCEPTION] {str(e)}")

def url2path(url):
    return P(('data/scraped/content/' + f'{urlparse(url).netloc}{urlparse(url).path}'.replace('/', '__').strip("__") + '.md'))

def write_to_file(url, markdown):
    write_to = url2path(url)
    makedir(write_to.parent)
    writelines([markdown], write_to, 'w')

if __name__ == '__main__':
    asyncio.run(main('https://www.infinitheism.com'))