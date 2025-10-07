#!/usr/bin/env python3
"""
Quick local parser for the saved `source.html` to validate XPaths/selectors
for PapaduStreamProvider without running Selenium.

Usage: python3 scripts/parse_source.py ../source.html
"""
import sys
import re
from pathlib import Path


def find_tiles(html: str):
    # Find blocks with class short_in and extract anchor href, image data-src/src and title link
    tiles = []
    # match the anchor with class short_img
    for m in re.finditer(r"<a[^>]+class=[\'\"]?[^>]*short_img[^>]*>[\s\S]*?<\/a>", html, re.I):
        a = m.group(0)
        href = re.search(r'href=[\"\']([^\"\']+)', a)
        img = re.search(r'<img[^>]+data-src=[\"\']([^\"\']+)', a)
        if not img:
            img = re.search(r'<img[^>]+src=[\"\']([^\"\']+)', a)
        title = re.search(r'title=[\"\']([^\"\']+)', a)
        tiles.append({
            'href': href.group(1) if href else None,
            'image': img.group(1) if img else None,
            'title': title.group(1) if title else None,
        })
    return tiles


def find_titles(html: str):
    # Find the short_title links
    titles = []
    for m in re.finditer(r"<div[^>]+class=[\'\"]?short_title[^>]*>[\s\S]*?<a[^>]+href=[\"\']([^\"\']+)[\"\'][^>]*>([^<]+)<\/a>", html, re.I):
        titles.append({'href': m.group(1), 'title': m.group(2).strip()})
    return titles


def find_seasons(html: str):
    # seasons links contain '-saison.html'
    return re.findall(r'href=[\"\']([^\"\']*-saison\.html)[\"\']', html, re.I)


def find_episodes(html: str):
    # episode links contain '-episode.html'
    return re.findall(r'href=[\"\']([^\"\']*-episode\.html)[\"\']', html, re.I)


def find_uqload_links(html: str):
    # find data-href or data-url-default or href containing uqload
    links = set()
    for m in re.finditer(r"(data-href|data-url-default|href)=[\"\']([^\"\']*uqload[^\"\']*)[\"\']", html, re.I):
        links.add(m.group(2))
    return list(links)


def main():
    if len(sys.argv) < 2:
        print("Usage: parse_source.py path/to/source.html")
        return

    path = Path(sys.argv[1])
    html = path.read_text(encoding='utf-8')

    tiles = find_tiles(html)
    titles = find_titles(html)
    seasons = find_seasons(html)
    episodes = find_episodes(html)
    uq_links = find_uqload_links(html)

    print(f"Found {len(tiles)} poster tiles")
    for t in tiles[:10]:
        print("  ", t)

    print(f"\nFound {len(titles)} titles")
    for t in titles[:10]:
        print("  ", t)

    print(f"\nFound {len(seasons)} season links (examples)")
    for s in seasons[:10]:
        print("  ", s)

    print(f"\nFound {len(episodes)} episode links (examples)")
    for e in episodes[:10]:
        print("  ", e)

    print(f"\nFound {len(uq_links)} uqload links (examples)")
    for u in uq_links[:10]:
        print("  ", u)


if __name__ == '__main__':
    main()
