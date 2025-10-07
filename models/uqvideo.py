from typing import Dict


class UqVideo:
    def __init__(self, dict: Dict, html_url: str):
        self.duration = dict.get("duration")
        self.image_url = dict.get("image_url")
        self.resolution = dict.get("resolution")
        self.size_in_bytes = dict.get("size")
        self.title = dict.get("title")
        self.type = dict.get("type")
        self.url = dict.get("url")
        self.html_url = html_url

    def to_dict(self):
        return {
            "duration": self.duration,
            "image_url": self.image_url,
            "resolution": self.resolution,
            "size_in_bytes": self.size_in_bytes,
            "title": self.title,
            "type": self.type,
            "url": self.url,
            "html_url": self.html_url,
        }

    def __repr__(self):
        return f"UqVideo(title={self.title}, url={self.url})"
