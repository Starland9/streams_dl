import re
import time
import urllib.parse
from contextlib import suppress
from typing import List, Set

import requests

from fastapi.concurrency import run_in_threadpool
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from uqload_dl import UQLoad

from models.media import Media
from models.uqvideo import UqVideo
from providers.provider import AbstractProvider
from cache import cache_video_links


class FlemmixProvider(AbstractProvider):
    """
    Provider for Flemmix (formerly Wiflix) streaming site.
    Base URL: https://flemmix.wiki/
    """
    
    DEFAULT_WAIT = 10
    BASE_URL = "https://flemmix.wiki"
    
    # Regex patterns for extracting UQload links
    _UQLOAD_SOURCE_RE = re.compile(
        r"sources?\s*:\s*\[(?P<block>[^\]]+)\]", re.IGNORECASE | re.DOTALL
    )
    _UQLOAD_URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
    _UQLOAD_FILE_CODE_RE = re.compile(
        r"file_code=([a-zA-Z0-9]+)", re.IGNORECASE
    )
    _UQLOAD_EMBED_RE = re.compile(
        r"https?://(?:www\.)?uqload\.[a-z]+/embed-[^\"']+", re.IGNORECASE
    )

    def __init__(self, driver: webdriver.Chrome):
        super().__init__(driver)
        self._http = requests.Session()
        self._user_agent: str = ""

    def _wait_for(self, xpath: str, timeout: int | None = None):
        """Wait for elements to be present on the page."""
        timeout = timeout or self.DEFAULT_WAIT
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located((By.XPATH, xpath))
            )
        except TimeoutException:
            return []

    @staticmethod
    def _normalize_url(url: str | None) -> str | None:
        """Normalize relative URLs to absolute URLs."""
        if not url:
            return None
        return urllib.parse.urljoin(FlemmixProvider.BASE_URL, url)

    def _get_user_agent(self) -> str:
        """Get the user agent from the browser."""
        if self._user_agent:
            return self._user_agent

        try:
            self._user_agent = self.driver.execute_script(
                "return navigator.userAgent;"
            )
        except Exception:
            self._user_agent = (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            )
        return self._user_agent

    def _sync_session_cookies(self, target_url: str) -> None:
        """Sync cookies from Selenium to requests session."""
        parsed = urllib.parse.urlparse(target_url)
        domain = parsed.netloc
        if not domain:
            return

        with suppress(Exception):
            self._http.cookies.clear(domain=domain)

        try:
            selenium_cookies = self.driver.get_cookies()
        except Exception:
            return

        for cookie in selenium_cookies:
            name = cookie.get("name")
            value = cookie.get("value")
            if not name or value is None:
                continue

            cookie_domain = cookie.get("domain") or domain
            normalized_domain = cookie_domain.lstrip(".")
            if (
                normalized_domain
                and normalized_domain not in domain
                and domain not in normalized_domain
            ):
                continue

            self._http.cookies.set(
                name,
                value,
                domain=cookie_domain,
                path=cookie.get("path", "/"),
            )

    def search_media(self, text: str) -> List[Media]:
        """
        Search for media on Flemmix.
        
        Args:
            text: Search query string
            
        Returns:
            List of Media objects (max 50)
        """
        uri = urllib.parse.quote(text)
        
        # Try common search URL patterns
        search_patterns = [
            f"{self.BASE_URL}/search/{uri}",
            f"{self.BASE_URL}/recherche/{uri}",
            f"{self.BASE_URL}/?s={uri}",
        ]
        
        medias: List[Media] = []
        
        for search_url in search_patterns:
            try:
                self.driver.get(search_url)
                time.sleep(0.5)
                
                # Try multiple XPath patterns for finding media items
                media_xpaths = [
                    "//div[contains(@class, 'movie-item') or contains(@class, 'serie-item')]",
                    "//div[contains(@class, 'result-item')]",
                    "//div[contains(@class, 'item') and .//a and .//img]",
                    "//article[contains(@class, 'post') or contains(@class, 'item')]",
                ]
                
                elements = []
                for xpath in media_xpaths:
                    elements = self._wait_for(xpath, timeout=5)
                    if elements:
                        break
                
                if not elements:
                    continue
                
                # Extract media information
                for elem in elements[:50]:
                    try:
                        # Try to find title
                        title = None
                        title_xpaths = [
                            ".//h2//a",
                            ".//h3//a",
                            ".//div[contains(@class, 'title')]//a",
                            ".//a[contains(@class, 'title')]",
                            ".//a[@title]"
                        ]
                        
                        for title_xpath in title_xpaths:
                            try:
                                title_elem = elem.find_element(By.XPATH, title_xpath)
                                title = title_elem.text.strip() or title_elem.get_attribute("title")
                                if title:
                                    break
                            except Exception:
                                continue
                        
                        if not title:
                            continue
                        
                        # Try to find URL
                        url = None
                        url_xpaths = [
                            ".//a[contains(@href, '/') and not(contains(@href, 'javascript'))]",
                            ".//a[@href]"
                        ]
                        
                        for url_xpath in url_xpaths:
                            try:
                                link_elem = elem.find_element(By.XPATH, url_xpath)
                                url = self._normalize_url(link_elem.get_attribute("href"))
                                if url and "javascript" not in url:
                                    break
                            except Exception:
                                continue
                        
                        # Try to find image
                        image_url = None
                        try:
                            img_elem = elem.find_element(By.XPATH, ".//img")
                            image_url = (
                                img_elem.get_attribute("data-src")
                                or img_elem.get_attribute("src")
                                or img_elem.get_attribute("data-lazy-src")
                            )
                        except Exception:
                            pass
                        
                        medias.append(Media(title=title, url=url, image_url=image_url))
                        
                    except Exception as e:
                        continue
                
                # If we found results, break
                if medias:
                    break
                    
            except Exception as e:
                print(f"Error trying search URL {search_url}: {e}")
                continue
        
        return medias[:50]

    def _get_episode_links(self, media_url: str) -> List[str]:
        """Extract episode links from a media page."""
        self.driver.get(media_url)
        time.sleep(0.5)
        
        episode_links: List[str] = []
        
        # Try multiple patterns for episode links
        episode_xpaths = [
            "//div[contains(@class, 'episode')]//a",
            "//a[contains(@class, 'episode')]",
            "//div[contains(@class, 'saison') or contains(@class, 'season')]//a",
            "//a[contains(@href, 'episode') or contains(@href, 'ep-')]",
        ]
        
        for xpath in episode_xpaths:
            elements = self._wait_for(xpath, timeout=5)
            if elements:
                for elem in elements:
                    try:
                        href = elem.get_attribute("href")
                        if href:
                            normalized = self._normalize_url(href)
                            if normalized and normalized not in episode_links:
                                episode_links.append(normalized)
                    except Exception:
                        continue
            
            if episode_links:
                break
        
        # If no episodes found, treat the page itself as a single video
        if not episode_links:
            episode_links = [media_url]
        
        return episode_links

    def _extract_uqload_from_page(self, page_url: str) -> Set[str]:
        """Extract UQload links from a page."""
        candidates: Set[str] = set()
        
        try:
            self.driver.get(page_url)
            time.sleep(0.5)
        except Exception:
            return candidates
        
        # Try to find and click buttons that reveal video players
        button_xpaths = [
            "//button[contains(@class, 'play') or contains(text(), 'Lecture')]",
            "//a[contains(@class, 'play-button')]",
            "//div[contains(@onclick, 'uqload')]",
        ]
        
        for xpath in button_xpaths:
            buttons = self._wait_for(xpath, timeout=3)
            for button in buttons:
                with suppress(Exception):
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});", button
                    )
                    self.driver.execute_script("arguments[0].click();", button)
                    time.sleep(0.3)
        
        # Look for iframes with uqload
        iframes = self._wait_for("//iframe[contains(@src, 'uqload')]", timeout=5)
        for iframe in iframes:
            try:
                src = iframe.get_attribute("src")
                if src and "uqload" in src:
                    candidates.add(src)
                    
                # Try to access iframe content
                iframe_links = self._collect_uqload_from_iframe(iframe)
                candidates.update(iframe_links)
            except Exception:
                continue
        
        # Search in page source for uqload links
        try:
            page_source = self.driver.page_source
            parsed_links = self._parse_uqload_links_from_html(page_source)
            candidates.update(parsed_links)
        except Exception:
            pass
        
        return candidates

    def _collect_uqload_from_iframe(self, iframe) -> Set[str]:
        """Extract UQload links from within an iframe."""
        links: Set[str] = set()
        try:
            with suppress(Exception):
                self.driver.execute_script(
                    "arguments[0].removeAttribute('sandbox');", iframe
                )
            self.driver.switch_to.frame(iframe)
            time.sleep(0.2)
            
            html = self.driver.execute_script(
                "return document.documentElement ? document.documentElement.outerHTML : '';"
            )
            if html:
                links.update(self._parse_uqload_links_from_html(html))
        except Exception:
            pass
        finally:
            with suppress(Exception):
                self.driver.switch_to.default_content()
        return links

    def _parse_uqload_links_from_html(self, html: str) -> Set[str]:
        """Parse UQload links from HTML content."""
        if not html:
            return set()

        links: Set[str] = set()

        # Look for sources array
        source_match = self._UQLOAD_SOURCE_RE.search(html)
        if source_match:
            block = source_match.group("block")
            for match in self._UQLOAD_URL_RE.findall(block):
                if "uqload" in match:
                    links.add(match.strip("'\""))

        # Look for embed URLs
        for match in self._UQLOAD_EMBED_RE.findall(html):
            links.add(match.strip("'\""))

        # Look for file codes
        file_code_match = self._UQLOAD_FILE_CODE_RE.search(html)
        if file_code_match:
            code = file_code_match.group(1)
            links.add(f"https://uqload.cx/embed-{code}.html")
            links.add(f"https://uqload.net/embed-{code}.html")

        return links

    @staticmethod
    def _normalize_uqload_candidate(link: str) -> str | None:
        """Normalize a UQload URL candidate."""
        if not link:
            return None

        cleaned = link.strip().strip("'\"")
        if "uqload" not in cleaned:
            return None

        if "/embed-" in cleaned:
            return cleaned.split("?")[0]

        # Try to extract the file code
        match = FlemmixProvider._UQLOAD_FILE_CODE_RE.search(cleaned)
        if match:
            code = match.group(1)
            return f"https://uqload.cx/embed-{code}.html"

        match = re.search(r"/(?:v/)?([a-zA-Z0-9]{8,})", cleaned)
        if match:
            code = match.group(1)
            return f"https://uqload.cx/embed-{code}.html"

        return cleaned

    @cache_video_links
    async def get_uqvideos_from_media_url(self, url: str) -> List[UqVideo]:
        """
        Get UQload videos from a media URL.
        
        Args:
            url: Media page URL
            
        Returns:
            List of UqVideo objects
        """
        uqvideos: List[UqVideo] = []
        seen_links: Set[str] = set()

        # Get episode links
        episode_links = self._get_episode_links(url)
        
        for episode_link in episode_links:
            # Extract UQload candidates from each episode
            candidates = self._extract_uqload_from_page(episode_link)
            
            for candidate in candidates:
                normalized = self._normalize_uqload_candidate(candidate)
                if not normalized or normalized in seen_links:
                    continue
                seen_links.add(normalized)

                try:
                    uqload = UQLoad(url=normalized)
                    video_info = await run_in_threadpool(uqload.get_video_info)
                    uqvideos.append(
                        UqVideo(dict=video_info, html_url=normalized)
                    )
                except Exception as exc:
                    print(f"Error fetching video info for {normalized}: {exc}")

        return uqvideos
