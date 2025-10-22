#!/usr/bin/env python3
"""
Example usage of the FlemmixProvider
"""

import asyncio
import undetected_chromedriver as uc
from providers.flemmix import FlemmixProvider

async def main():
    # Setup Chrome driver
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    driver = uc.Chrome(options=chrome_options)
    
    try:
        # Create provider
        provider = FlemmixProvider(driver)
        
        # Example 1: Search for media
        print("Searching for 'Futurama' on Flemmix...")
        results = provider.search_media("Futurama")
        
        if results:
            print(f"\nFound {len(results)} results:")
            first_result = results[0]
            print(f"  - {first_result.title}")
            print(f"    URL: {first_result.url}")
            
            # Example 2: Get video links from the first result
            if first_result.url:
                print(f"\nExtracting videos from: {first_result.title}")
                videos = await provider.get_uqvideos_from_media_url(first_result.url)
                
                if videos:
                    print(f"Found {len(videos)} video(s):")
                    for video in videos[:3]:  # Show first 3
                        print(f"  - {video.title or 'Unknown'}")
                        print(f"    Resolution: {video.resolution}")
                        print(f"    URL: {video.url}")
                else:
                    print("No videos found")
        else:
            print("No search results found")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    asyncio.run(main())
