#!/usr/bin/env python3
"""
Test script for the FlemmixProvider.
Usage: python test_flemmix.py [search_query]
"""

import sys
import undetected_chromedriver as uc

from providers.flemmix import FlemmixProvider

def main():
    search_query = sys.argv[1] if len(sys.argv) > 1 else "Futurama"
    
    print(f"Testing FlemmixProvider with search query: '{search_query}'")
    print("=" * 60)
    
    # Setup Chrome driver
    chrome_options = uc.ChromeOptions()
    # chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    driver = uc.Chrome(options=chrome_options)
    
    try:
        # Create provider
        provider = FlemmixProvider(driver)
        
        # Test search
        print(f"\n1. Searching for '{search_query}'...")
        results = provider.search_media(search_query)
        print(f"   Found {len(results)} results")
        
        for i, media in enumerate(results[:5], 1):
            print(f"\n   {i}. {media.title}")
            print(f"      URL: {media.url}")
            if media.image_url:
                print(f"      Image: {media.image_url[:60]}...")
        
        if results and results[0].url:
            print(f"\n2. Testing video extraction from first result...")
            print(f"   Media: {results[0].title}")
            print(f"   URL: {results[0].url}")
            
            # Note: This is a synchronous test, so we'll just test the episode extraction
            episode_links = provider._get_episode_links(results[0].url)
            print(f"   Found {len(episode_links)} episode link(s)")
            for i, link in enumerate(episode_links[:3], 1):
                print(f"      {i}. {link}")
        
        print("\n" + "=" * 60)
        print("Test completed successfully!")
        
    except Exception as e:
        print(f"\nError during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()
        print("Driver closed.")

if __name__ == "__main__":
    main()
