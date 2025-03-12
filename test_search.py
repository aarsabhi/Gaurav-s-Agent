from tavily import TavilyClient
import json
from datetime import datetime

# Initialize Tavily client
tavily = TavilyClient(api_key="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")

def test_tavily_search():
    try:
        # Add time-based context to the query
        current_year = datetime.now().year
        query = f"Top 10 current news in India {current_year} breaking news latest developments"
        
        # Perform the search with Tavily
        search_result = tavily.search(
            query=query,
            search_depth="advanced",
            max_results=10,
            sort_by="date",
            search_type="news",  # Specifically search for news
            include_domains=[
                "timesofindia.indiatimes.com",
                "ndtv.com",
                "indianexpress.com",
                "hindustantimes.com",
                "news18.com",
                "thehindu.com",
                "reuters.com",
                "bloomberg.com"
            ]
        )
        
        # Print results
        print("\nSearch Results for:", query)
        print("-" * 80)
        for idx, result in enumerate(search_result.get('results', []), 1):
            print(f"\n{idx}. {result.get('title', 'No Title')}")
            print(f"Source: {result.get('url', 'No URL')}")
            print(f"Published: {result.get('published_date', 'No Date')}")
            print("\nSummary:")
            print(result.get('content', 'No Content')[:300], "...")
            print("-" * 80)

    except Exception as e:
        print(f"Error during search: {str(e)}")

if __name__ == "__main__":
    test_tavily_search() 