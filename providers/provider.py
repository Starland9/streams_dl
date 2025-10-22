from models.media import Media
from models.uqvideo import UqVideo
from selenium import webdriver


class AbstractProvider:
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver

    def search_media(self, text: str) -> list[Media]:
        """
        Search for media content based on the provided text query.

        Args:
            text (str): The search query string to find matching media content.

        Returns:
            list[Media]: A list of Media objects that match the search criteria.
                        Returns an empty list if no matches are found.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.

        Note:
            This is an abstract method that should be overridden by concrete
            provider implementations to define specific search behavior.
        """
        raise NotImplementedError

    async def get_uqvideos_from_media_url(self, url: str) -> list[UqVideo]:
        """
        Extract unique videos from a media URL.

        This method should be implemented by subclasses to parse a media URL and return
        a list of unique video objects that can be downloaded or processed.

        Args:
            url (str): The media URL to extract videos from.

        Returns:
            list[UqVideo]: A list of unique video objects found at the given URL.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError
