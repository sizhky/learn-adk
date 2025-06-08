from torch_snippets import writelines, P, makedir
import asyncio
from crawl4ai import AsyncWebCrawler

async def main(url, write_to_file=None):
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url,
        )
        if write_to_file is None:
            write_to_file = P(f'data/scraped/{url.split("//")[-1].replace("/", "_")}.md')
            makedir(write_to_file.parent)
        import ipdb; ipdb.set_trace()
        writelines([result.markdown], write_to_file, 'w')

if __name__ == '__main__':
    asyncio.run(main('https://www.infinitheism.com'))