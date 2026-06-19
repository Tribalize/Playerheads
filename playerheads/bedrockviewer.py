from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote


PROFILE_URL = "https://bedrockviewer.com/profile/{gamertag}/json"
SKIN_DOWNLOAD_URL = "https://bedrockviewer.com/download-skin/{xuid}"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@dataclass(frozen=True)
class Profile:
    gamertag: str
    xuid: str
    has_skin: bool


class BedrockViewerClient:
    def __init__(self, session=None, timeout: int = 20):
        self.session = session or _default_session()
        self.timeout = timeout

    @staticmethod
    def profile_url(gamertag: str) -> str:
        return PROFILE_URL.format(gamertag=quote(str(gamertag), safe=""))

    @staticmethod
    def skin_download_url(xuid: str) -> str:
        return SKIN_DOWNLOAD_URL.format(xuid=xuid)

    def fetch_profile(self, gamertag: str) -> Profile:
        url = self.profile_url(gamertag)
        response = self.session.get(url, timeout=self.timeout)
        if response.status_code != 200:
            raise ValueError(f"BedrockViewer profile request failed for {gamertag}: HTTP {response.status_code} at {url}")
        try:
            data = response.json()
        except Exception as exc:
            raise ValueError(f"BedrockViewer profile for {gamertag} returned invalid JSON at {url}") from exc
        if not isinstance(data, dict):
            raise ValueError(f"BedrockViewer profile for {gamertag} returned invalid JSON at {url}")
        xuid = str(data.get("XUID") or "").strip()
        if not xuid:
            keys = ", ".join(sorted(str(key) for key in data.keys()))
            raise ValueError(f"BedrockViewer profile for {gamertag} did not include XUID. Response keys: {keys}")
        resolved_name = str(data.get("Gamertag") or gamertag)
        return Profile(gamertag=resolved_name, xuid=xuid, has_skin=bool(data.get("skin")))

    def download_skin(self, xuid: str) -> bytes:
        url = self.skin_download_url(xuid)
        response = self.session.get(url, timeout=self.timeout)
        if response.status_code != 200:
            raise ValueError(f"BedrockViewer skin download failed for XUID {xuid}: HTTP {response.status_code} at {url}")
        content_type = str(response.headers.get("Content-Type", "")).lower()
        if "image/png" not in content_type:
            raise ValueError(f"BedrockViewer skin download for XUID {xuid} did not return image/png. Content-Type: {content_type}")
        if not response.content.startswith(PNG_SIGNATURE):
            raise ValueError(f"BedrockViewer skin download for XUID {xuid} did not return PNG data.")
        return response.content


def _default_session():
    import requests

    return requests.Session()
