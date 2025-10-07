from models.media import Media
from models.uqvideo import UqVideo
from selenium import webdriver


class AbstractProvider:
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver

    def search_media(self, text: str) -> list[Media]:
        raise NotImplementedError

    async def get_uqvideos_from_media_url(self, url: str) -> list[UqVideo]:
        raise NotImplementedError
