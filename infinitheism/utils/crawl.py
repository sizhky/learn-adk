import asyncio
import json
import re
from pathlib import Path
from urllib.parse import urlparse, urljoin
from typing import List, Set, Optional

import aiohttp
import typer
from crawl4ai import AsyncWebCrawler
from torch_snippets import writelines, P, makedir, exists

app = typer.Typer()

class WebCrawler:
    """A modular web crawler that can crawl any domain and save to any output directory."""
    
    def __init__(
        self, 
        domain: str, 
        output_dir: Path,
        crawl_limit: int = 50000,
        exclude_patterns: Optional[List[str]] = None
    ):
        self.domain = domain
        self.output_dir = Path(output_dir)
        self.data_dir = self.output_dir / "scraped"
        self.visited_file = self.data_dir / "visited.json"
        self.queue_file = self.data_dir / "queue.json"
        self.content_dir = self.data_dir / "content"
        self.crawl_limit = crawl_limit
        self.exclude_patterns = exclude_patterns or [
            '.jpg', '.jpeg', '.png', '.gif', '.pdf', '.mp4', '.mp3', 
            '.zip', '.tar', '.gz', 'category', 'cart', 'checkout', 
            'enroll', 'author', 'page'
        ]
        
        self.visited: Set[str] = set()
        self.crawled = 0
        
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.content_dir.mkdir(parents=True, exist_ok=True)

    # --- Persistence Utilities ---
    def load_json(self, path: Path, default):
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        return default

    def save_json(self, path: Path, data):
        with open(path, "w") as f:
            json.dump(data, f)

    def load_queue(self) -> List[str]:
        return self.load_json(self.queue_file, [])

    def save_queue(self, queue: List[str]):
        self.save_json(self.queue_file, queue)

    def load_visited(self) -> Set[str]:
        return set(self.load_json(self.visited_file, []))

    def save_visited(self):
        self.save_json(self.visited_file, list(self.visited))

    # --- Path Utilities ---
    def url2path(self, url: str) -> Path:
        return P(self.content_dir / (f'{urlparse(url).netloc}{urlparse(url).path}'.replace('/', '__').strip("__") + '.md'))

    def write_to_file(self, url: str, markdown: str):
        path = self.url2path(url)
        makedir(path.parent)
        writelines([markdown], path, 'w')

    # --- Link Extraction ---
    async def extract_links(self, markdown: str, base_url: str) -> Set[str]:
        links = set()
        # Extract Markdown links
        for match in re.findall(r'\[.*?\]\((.*?)\)', markdown):
            href = urljoin(base_url, match)
            if self.domain in urlparse(href).netloc:
                links.add(href.split('#')[0])
        # Extract plain https:// links
        for match in re.findall(r'https://[^\s\)\]]+', markdown):
            href = urljoin(base_url, match)
            if self.domain in urlparse(href).netloc:
                links.add(href.split('#')[0])
        return links

    # --- Crawler Logic ---
    async def crawl_and_scrape(self, url: str, crawler, session) -> List[str]:
        try:
            if self.domain not in urlparse(url).netloc:
                return []
            if url in self.visited:
                return []
            self.visited.add(url)
            self.save_visited()
            print(f"[CRAWLING] {url}")
            result = await crawler.arun(url=url)
            if not result.success:
                print(f"[ERROR] {url} => {result.error_message}")
                return []
            self.write_to_file(url, result.markdown)
            links = await self.extract_links(result.markdown, url)
            # Filter out excluded URLs before returning them for the queue
            filtered_links = []
            for link in links:
                if not any(ext in link for ext in self.exclude_patterns):
                    filtered_links.append(link)
            self.crawled += 1
            if self.crawled > self.crawl_limit:
                raise Exception("Crawled too many pages, stopping to avoid infinite loop.")
            return filtered_links
        except Exception as e:
            print(f"[SCRAPE EXCEPTION] {url} => {str(e)}")
            return []

    # --- Main Crawling Method ---
    async def crawl(self, seed_url: str):
        """Main crawling method that orchestrates the entire crawling process."""
        self.visited = self.load_visited()
        
        async with AsyncWebCrawler() as crawler, aiohttp.ClientSession() as session:
            to_crawl = self.load_queue() or [seed_url]
            try:
                while to_crawl:
                    next_batch = []
                    for url in to_crawl:
                        if url in self.visited:
                            continue
                        # Check exclusion patterns for URLs already in queue (for backward compatibility)
                        if any(ext in url for ext in self.exclude_patterns):
                            print(f"[EXCLUDED] {url} due to file type or path.")
                            continue
                        if exists(self.url2path(url)):
                            print(f"[SKIPPING] {url} already exists.")
                            continue
                        new_links = await self.crawl_and_scrape(url, crawler, session)
                        next_batch.extend(new_links)
                    to_crawl = [link for link in next_batch if link not in self.visited]
                    to_crawl = list(set(to_crawl))  # Deduplicate to avoid redundant scraping
                    self.save_queue(to_crawl)
            except Exception as e:
                print(f"[EXCEPTION] {str(e)}")

# --- Typer CLI Interface ---
@app.command()
def crawl_website(
    website: str = typer.Argument(..., help="Website URL to crawl (e.g., https://example.com)"),
    output_dir: str = typer.Argument(..., help="Output directory to save crawled content"),
    crawl_limit: int = typer.Option(50000, "--limit", "-l", help="Maximum number of pages to crawl"),
    exclude: List[str] = typer.Option(
        [
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.ico', '.svg',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.mp4', '.m4v', '.mov', '.avi', '.wmv', '.flv', '.webm', '.mkv',
            '.mp3', '.wav', '.aac', '.ogg', '.flac', '.m4a', '.wma', '.opus',
            '.zip', '.tar', '.gz', '.rar', '.7z',
            'category', 'cart', 'checkout', 'enroll', 'author', 'page'
        ],
        "--exclude", "-e", help="Patterns to exclude from crawling"
    )
):
    """
    Crawl a website and save all content to the specified output directory.
    
    Example:
        python crawl.py https://example.com ./output
    """
    # Extract domain from URL
    parsed_url = urlparse(website)
    domain = parsed_url.netloc
    
    if not domain:
        typer.echo(f"Error: Invalid URL '{website}'. Please provide a valid URL.", err=True)
        raise typer.Exit(1)
    
    # Create crawler instance
    crawler = WebCrawler(
        domain=domain,
        output_dir=Path(output_dir),
        crawl_limit=crawl_limit,
        exclude_patterns=exclude
    )
    
    typer.echo(f"Starting crawl of {website}")
    typer.echo(f"Domain: {domain}")
    typer.echo(f"Output directory: {output_dir}")
    typer.echo(f"Crawl limit: {crawl_limit}")
    
    # Run the crawler
    asyncio.run(crawler.crawl(website))
    
    typer.echo("Crawling completed!")

def crawl_website_async(website: str, output_dir: str, crawl_limit: int = 50000, exclude_patterns: Optional[List[str]] = None):
    """
    Async function to crawl a website programmatically.
    
    Args:
        website: Website URL to crawl
        output_dir: Output directory to save content
        crawl_limit: Maximum number of pages to crawl
        exclude_patterns: Patterns to exclude from crawling
    """
    parsed_url = urlparse(website)
    domain = parsed_url.netloc
    
    if not domain:
        raise ValueError(f"Invalid URL '{website}'. Please provide a valid URL.")
    
    crawler = WebCrawler(
        domain=domain,
        output_dir=Path(output_dir),
        crawl_limit=crawl_limit,
        exclude_patterns=exclude_patterns
    )
    
    return crawler.crawl(website)

if __name__ == '__main__':
    # Check if running with old-style arguments for backward compatibility
    import sys
    if len(sys.argv) == 1:
        # Run with original hardcoded domain for backward compatibility
        original_domain = "infinitheism.com"
        original_output = "data"
        print(f"Running in compatibility mode: crawling {original_domain}")
        crawler = WebCrawler(
            domain=original_domain,
            output_dir=Path(original_output)
        )
        asyncio.run(crawler.crawl(f'https://{original_domain}'))
    else:
        # Run Typer CLI
        app()