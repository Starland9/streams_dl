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


class PapaduStreamProvider(AbstractProvider):
    DEFAULT_WAIT = 10
    _UQLOAD_SOURCE_RE = re.compile(
        r"sources?\s*:\s*\[(?P<block>[^\]]+)\]", re.IGNORECASE | re.DOTALL)
    _UQLOAD_URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
    _UQLOAD_FILE_CODE_RE = re.compile(
        r"file_code=([a-zA-Z0-9]+)", re.IGNORECASE)
    _UQLOAD_EMBED_RE = re.compile(
        r"https?://(?:www\.)?uqload\.[a-z]+/embed-[^\"']+", re.IGNORECASE)

    def __init__(self, driver: webdriver.Chrome):
        super().__init__(driver)
        self._http = requests.Session()
        self._user_agent: str = ""

    def _wait_for(self, xpath: str, timeout: int | None = None):
        timeout = timeout or self.DEFAULT_WAIT
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located((By.XPATH, xpath))
            )
        except TimeoutException:
            return []

    @staticmethod
    def _normalize_url(url: str | None) -> str | None:
        if not url:
            return None
        return urllib.parse.urljoin("https://papadustream.credit", url)

    def _sync_session_cookies(self, target_url: str) -> None:
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
            if normalized_domain and normalized_domain not in domain and domain not in normalized_domain:
                continue

            self._http.cookies.set(
                name,
                value,
                domain=cookie_domain,
                path=cookie.get("path", "/"),
            )

    def _extract_series_entries(self) -> List[tuple[str, str | None, str | None]]:
        tiles = self._wait_for("//div[contains(@class,'short_in')]")
        entries: List[tuple[str, str | None, str | None]] = []

        for tile in tiles:
            try:
                title_el = tile.find_element(
                    By.XPATH, ".//div[contains(@class,'short_title')]/a")
                title = title_el.text.strip()
            except Exception:
                title_el = None
                title = (
                    tile.get_attribute("data-title")
                    or tile.get_attribute("title")
                    or tile.get_attribute("aria-label")
                    or ""
                ).strip()

            if not title:
                continue

            detail_url = None
            if title_el is not None:
                try:
                    detail_url = title_el.get_attribute("href")
                except Exception:
                    detail_url = None

            if not detail_url:
                try:
                    detail_url = tile.find_element(
                        By.XPATH, ".//a[contains(@class,'short_img')]"
                    ).get_attribute("href")
                except Exception:
                    detail_url = None

            image = None
            try:
                img_el = tile.find_element(By.XPATH, ".//img")
                image = img_el.get_attribute(
                    "data-src") or img_el.get_attribute("src")
            except Exception:
                image = None

            entries.append((title, self._normalize_url(detail_url), image))

        return entries

    def _collect_season_medias(
        self, series_title: str, detail_url: str | None, fallback_image: str | None
    ) -> List[Media]:
        if not detail_url:
            return []

        season_medias: List[Media] = []
        try:
            self.driver.get(detail_url)
        except Exception:
            return season_medias

        # Give the page a brief moment and wait explicitly for season anchors
        time.sleep(0.2)
        season_anchors = self._wait_for(
            "//div[contains(@class,'seasontab')]//a[contains(@href,'-saison.html')]",
            timeout=6,
        )

        if not season_anchors:
            # Fallback: treat detail page as seasonless media
            season_medias.append(
                Media(title=series_title, url=detail_url, image_url=fallback_image))
            return season_medias

        for anchor in season_anchors:
            try:
                season_url = self._normalize_url(anchor.get_attribute("href"))
            except Exception:
                season_url = None

            if not season_url:
                continue

            # Build a readable season label
            season_label = anchor.text.strip()
            if not season_label:
                season_label = anchor.get_attribute("title") or ""

            season_title = f"{series_title} {season_label}".strip()

            season_image = fallback_image
            try:
                img_el = anchor.find_element(By.XPATH, ".//img")
                season_image = (
                    img_el.get_attribute("data-src")
                    or img_el.get_attribute("src")
                    or season_image
                )
            except Exception:
                pass

            season_medias.append(
                Media(title=season_title, url=season_url, image_url=season_image)
            )

        return season_medias

    def search_media(self, text: str) -> List[Media]:
        uri = urllib.parse.quote(text)
        search_url = f"https://papadustream.credit/f/l.title={uri}/p.cat=11/sort=editdate/order=desc/"
        self.driver.get(search_url)

        series_entries = self._extract_series_entries()

        medias: List[Media] = []
        for series_title, detail_url, image in series_entries:
            season_medias = self._collect_season_medias(
                series_title, detail_url, image)
            medias.extend(season_medias)
            if len(medias) >= 50:
                break

        return medias[:50]

    def _get_episode_links(self, season_url: str) -> List[str]:
        self.driver.get(season_url)

        episode_anchors = self._wait_for(
            "//div[contains(@class,'saisontab')]//a[contains(@href,'-episode.html')]",
            timeout=6,
        )

        episode_links: List[str] = []
        for anchor in episode_anchors:
            try:
                ep_url = self._normalize_url(anchor.get_attribute("href"))
            except Exception:
                ep_url = None

            if ep_url:
                episode_links.append(ep_url)

        return episode_links

    def _get_uq_from_episode(self, episode_url: str):
        candidates: Set[str] = set()

        try:
            self.driver.get(episode_url)
        except Exception:
            return []

        time.sleep(0.3)

        clickable_divs = self._wait_for(
            "//div[contains(@class,'lien') and contains(@onclick,'uqload_')]",
            timeout=6,
        )

        for div in clickable_divs:
            with suppress(Exception):
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", div
                )
                self.driver.execute_script("arguments[0].click();", div)
                time.sleep(0.25)

        iframe_elements = self._wait_for(
            "//iframe[contains(@src,'uqload')]", timeout=8)
        for iframe in iframe_elements:
            src = None
            with suppress(Exception):
                src = iframe.get_attribute("src")
            if src:
                candidates.add(src)

            iframe_links = self._collect_uqload_links_from_iframe(iframe)
            candidates.update(iframe_links)

            if src:
                fetched_html = self._fetch_iframe_html(
                    src, referer=episode_url)
                if fetched_html:
                    parsed_links = self._parse_uqload_links_from_html(
                        fetched_html)
                    candidates.update(parsed_links)

        return list(candidates)

    def _collect_uqload_links_from_iframe(self, iframe) -> Set[str]:
        links: Set[str] = set()
        try:
            with suppress(Exception):
                self.driver.execute_script(
                    "arguments[0].removeAttribute('sandbox');", iframe)
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
        if not html:
            return set()

        links: Set[str] = set()

        source_match = self._UQLOAD_SOURCE_RE.search(html)
        if source_match:
            block = source_match.group("block")
            for match in self._UQLOAD_URL_RE.findall(block):
                if "uqload" in match:
                    links.add(match.strip("'\""))

        for match in self._UQLOAD_EMBED_RE.findall(html):
            links.add(match.strip("'\""))

        file_code_match = self._UQLOAD_FILE_CODE_RE.search(html)
        if file_code_match:
            code = file_code_match.group(1)
            links.add(f"https://uqload.cx/embed-{code}.html")
            links.add(f"https://uqload.net/embed-{code}.html")

        return links

    def _fetch_iframe_html(self, iframe_url: str, referer: str) -> str | None:
        headers = {
            "User-Agent": self._get_user_agent(),
            "Referer": referer,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        try:
            self._sync_session_cookies(iframe_url)
            response = self._http.get(iframe_url, headers=headers, timeout=10)
            if response.ok and "html" in response.headers.get("Content-Type", ""):
                return response.text
        except Exception:
            return None
        return None

    def _get_user_agent(self) -> str:
        if self._user_agent:
            return self._user_agent

        try:
            self._user_agent = self.driver.execute_script(
                "return navigator.userAgent;")
        except Exception:
            self._user_agent = (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            )
        return self._user_agent

    @staticmethod
    def _normalize_uqload_candidate(link: str) -> str | None:
        if not link:
            return None

        cleaned = link.strip().strip("'\"")
        if "uqload" not in cleaned:
            return None

        if "/embed-" in cleaned:
            return cleaned.split("?")[0]

        # Try to extract the file code from various URL shapes.
        match = PapaduStreamProvider._UQLOAD_FILE_CODE_RE.search(cleaned)
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
        uqvideos: List[UqVideo] = []
        seen_links: Set[str] = set()

        episode_links = self._get_episode_links(url)
        for episode_link in episode_links:
            candidates = self._get_uq_from_episode(episode_link)
            for candidate in candidates:
                normalized = self._normalize_uqload_candidate(candidate)
                if not normalized or normalized in seen_links:
                    continue
                seen_links.add(normalized)

                try:
                    uqload = UQLoad(url=normalized)
                    video_info = await run_in_threadpool(uqload.get_video_info)
                    uqvideos.append(
                        UqVideo(dict=video_info, html_url=normalized))
                except Exception as exc:
                    print(f"Error fetching video info for {normalized}: {exc}")

        return uqvideos
