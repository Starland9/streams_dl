import urllib.parse
from fastapi.concurrency import run_in_threadpool
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from models.media import Media
from models.uqvideo import UqVideo
from uqload_dl import UQLoad

from providers.provider import AbstractProvider


class FrenchStreamProvider(AbstractProvider):
    def __init__(self, driver: webdriver.Chrome):
        super().__init__(driver)

    def search_media(self, text: str) -> list[Media]:
        """
        Searches for media on french-streaming.tv and returns a list of Media objects.
        """
        uri = urllib.parse.quote(text)
        self.driver.get(f"https://www.french-streaming.tv/search/{uri}")

        series = self.driver.find_elements(
            "xpath", "//div[contains(@class, 'short serie')]"
        )
        films = self.driver.find_elements(
            "xpath", "//div[contains(@class, 'short-in nl')]"
        )

        all_results = series + films
        if len(all_results) > 50:
            all_results = all_results[:50]

        return [Media.from_web_element(sf) for sf in all_results]

    async def get_uqvideos_from_media_url(self, url: str) -> list[UqVideo]:
        """
        Gets all UqVideo objects from a media page URL.
        """
        self.driver.get(url)
        try:
            uqloadButton = self.driver.find_element(
                "xpath", "//a[contains(@data-href, 'uqload') and contains(@id, 'singh1')]"
            )
            uqloadButton.click()
            video_links_elements = self.driver.find_elements(
                "xpath", "//a[contains(@data-href, 'uqload')]"
            )
            links = [link.get_attribute("data-href")
                     for link in video_links_elements]
        except Exception:
            links_elements = self.driver.find_elements(
                "xpath", "//div[contains(@data-url-default, 'uqload')]"
            )
            links = [link.get_attribute("data-url-default")
                     for link in links_elements]

        uqvideos = []
        for link in links:
            if not link:
                continue
            try:
                uqload = UQLoad(url=link)
                # Run the blocking, problematic function in a separate thread
                video_info = await run_in_threadpool(uqload.get_video_info)
                uqvideos.append(UqVideo(dict=video_info, html_url=link))
            except Exception as e:
                print(f"Error getting video info for {link}: {e}")
                pass
        return uqvideos
