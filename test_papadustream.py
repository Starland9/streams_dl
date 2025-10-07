from fastapi import FastAPI, Body, BackgroundTasks
import undetected_chromedriver as uc
import os

from providers.papadustream import PapaduStreamProvider

DOWNLOADS_DIR = "downloads"

# --- Selenium Driver Setup ---
chrome_options = uc.ChromeOptions()
# chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
# driver = webdriver.Chrome(
#     service=ChromeService(ChromeDriverManager().install()), options=chrome_options
# )
driver = uc.Chrome(options=chrome_options)

# test provider
provider = PapaduStreamProvider(driver)
results = provider.search_media("futurama")
print(f"Found {len(results)} medias")
for media in results:
    print(f"- {media.title} ({media.url})")
    # get episodes
    if not media.url:
        continue
    episode_links = provider._get_episode_links(media.url)
    print(f"  Found {len(episode_links)} episodes")
    for ep_link in episode_links:
        print(f"  - Episode link: {ep_link}")
        provider._get_uq_from_episode(ep_link)


driver.quit()
