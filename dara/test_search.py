#!/usr/bin/env python3
"""
Test script to verify DuckDuckGo MCP client integration.
"""

import asyncio
from agent import search_tool, search_financial_data

async def test_search():
    """Test the DuckDuckGo search functionality."""
    print("Testing DuckDuckGo MCP client integration...")
    
    # Test 1: Direct search tool
    print("\n1. Testing direct search tool:")
    result = await search_tool.search("Apple Inc revenue 2023", count=5)
    print(f"Success: {result['success']}")
    print(f"Query: {result['query']}")
    print(f"Results preview: {result['results'][:200]}...")
    
    # Test 2: Financial search function
    print("\n2. Testing financial search function:")
    financial_result = await search_financial_data("Microsoft", count=3)
    print(f"Financial search result: {financial_result[:300]}...")

if __name__ == "__main__":
    asyncio.run(test_search())
