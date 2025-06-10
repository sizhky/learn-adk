#!/usr/bin/env python3
"""
Example script showing how to use the web crawler module programmatically.
"""

import asyncio
from pathlib import Path
from crawl import WebCrawler, crawl_website_async


async def example_basic_usage():
    """Example 1: Basic usage with WebCrawler class"""
    print("Example 1: Basic usage with WebCrawler class")
    
    crawler = WebCrawler(
        domain="httpbin.org",
        output_dir=Path("./example_output_1"),
        crawl_limit=3,  # Small limit for demo
        exclude_patterns=['.json', '.xml']  # Custom exclusions
    )
    
    await crawler.crawl("https://httpbin.org")
    print("✓ Crawling completed!")


async def example_convenience_function():
    """Example 2: Using the convenience function"""
    print("\nExample 2: Using the convenience function")
    
    await crawl_website_async(
        website="https://httpbin.org/html",
        output_dir="./example_output_2",
        crawl_limit=2,
        exclude_patterns=['.json', '.xml', 'forms']
    )
    print("✓ Crawling completed!")


async def example_multiple_sites():
    """Example 3: Crawling multiple sites"""
    print("\nExample 3: Crawling multiple sites")
    
    sites = [
        ("https://httpbin.org", "./output/httpbin"),
        ("https://httpbin.org/html", "./output/httpbin_html"),
    ]
    
    for site_url, output_dir in sites:
        print(f"Crawling {site_url}...")
        await crawl_website_async(
            website=site_url,
            output_dir=output_dir,
            crawl_limit=2
        )
        print(f"✓ Completed {site_url}")


async def main():
    """Run all examples"""
    print("Web Crawler Module Examples")
    print("=" * 40)
    
    # Run examples
    await example_basic_usage()
    await example_convenience_function()
    await example_multiple_sites()
    
    print("\n" + "=" * 40)
    print("All examples completed!")
    print("\nCheck the output directories:")
    print("- ./example_output_1/")
    print("- ./example_output_2/")
    print("- ./output/")


if __name__ == "__main__":
    asyncio.run(main())
