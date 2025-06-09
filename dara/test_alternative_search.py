#!/usr/bin/env python3
"""
Alternative DuckDuckGo search implementation for testing.
"""

import asyncio
import httpx
import json
from typing import Dict, Any, List
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

class SimpleDuckDuckGoSearch:
    """Simple DuckDuckGo search without MCP for comparison."""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
    async def search(self, query: str, count: int = 10) -> Dict[str, Any]:
        """Perform simple DuckDuckGo search."""
        try:
            async with httpx.AsyncClient(timeout=10.0, headers=self.headers) as client:
                # Using DuckDuckGo instant answers API
                encoded_query = quote_plus(query)
                url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
                
                response = await client.get(url)
                response.raise_for_status()
                
                data = response.json()
                
                # Extract results
                results = []
                
                # Abstract/summary
                if data.get('Abstract'):
                    results.append({
                        'title': data.get('AbstractText', '')[:100],
                        'description': data.get('Abstract', ''),
                        'url': data.get('AbstractURL', ''),
                        'source': 'Abstract'
                    })
                
                # Related topics
                for topic in data.get('RelatedTopics', [])[:count-1]:
                    if isinstance(topic, dict) and topic.get('Text'):
                        results.append({
                            'title': topic.get('Text', '')[:50],
                            'description': topic.get('Text', ''),
                            'url': topic.get('FirstURL', ''),
                            'source': 'Related'
                        })
                
                # Infobox data
                if data.get('Infobox'):
                    infobox = data['Infobox']
                    content_items = []
                    for item in infobox.get('content', []):
                        if item.get('label') and item.get('value'):
                            content_items.append(f"{item['label']}: {item['value']}")
                    
                    if content_items:
                        results.append({
                            'title': f"Info: {query}",
                            'description': "; ".join(content_items),
                            'url': data.get('AbstractURL', ''),
                            'source': 'Infobox'
                        })
                
                return {
                    "success": True,
                    "query": query,
                    "results": results[:count],
                    "total_results": len(results)
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": [],
                "total_results": 0
            }

async def test_alternative_search():
    """Test the alternative search method."""
    search = SimpleDuckDuckGoSearch()
    
    print("Testing alternative DuckDuckGo search...")
    
    queries = [
        "Apple Inc revenue 2023",
        "Microsoft financial report",
        "Tesla annual revenue"
    ]
    
    for query in queries:
        print(f"\nTesting query: {query}")
        result = await search.search(query, count=3)
        print(f"Success: {result['success']}")
        print(f"Total results: {result['total_results']}")
        
        if result['results']:
            for i, res in enumerate(result['results'], 1):
                print(f"  {i}. {res['title']}")
                print(f"     {res['description'][:100]}...")
                print(f"     URL: {res['url']}")
                print(f"     Source: {res['source']}")
        else:
            print("  No results found")

if __name__ == "__main__":
    print("Starting alternative search test...")
    asyncio.run(test_alternative_search())
    print("Test completed.")
