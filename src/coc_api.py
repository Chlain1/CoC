import os
import time
import typing as t
from urllib.parse import quote

import requests

BASE_URL = "https://api.clashofclans.com/v1"


def _encode_tag(tag: str) -> str:
    tag = tag.strip()
    if not tag.startswith("#"):
        # Akzeptiere auch Tags ohne #, aber füge hinzu
        tag = "#" + tag
    # API erwartet URL-kodiertes #
    return quote(tag, safe="")


class ApiError(Exception):
    pass


class CocApi:
    def __init__(self, token: str, timeout: float = 15.0, max_retries: int = 2):
        self.token = token
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        })

    def _get(self, path: str, params: dict | None = None) -> dict | list | None:
        url = f"{BASE_URL}{path}"
        last_err = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = self.session.get(url, params=params or {}, timeout=self.timeout)
                if resp.status_code == 200:
                    return resp.json()
                if resp.status_code == 403:
                    # Warlog ist privat oder kein Zugriff
                    try:
                        err_data = resp.json()
                        if err_data.get("reason") == "accessDenied":
                            return None  # Behandle wie 404 - nicht verfügbar
                    except:
                        pass
                    raise ApiError(f"Zugriff verweigert (HTTP 403): {resp.text[:300]}")
                if resp.status_code == 401:
                    raise ApiError(f"Unautorisiert (HTTP 401): Token ungültig oder IP falsch")
                if resp.status_code == 404:
                    # Z. B. Warlog privat, Clan existiert nicht oder kein aktueller Krieg
                    return None
                # andere Fehler: wiederholen
                last_err = ApiError(f"HTTP {resp.status_code}: {resp.text[:200]}")
            except requests.RequestException as e:
                last_err = e
            # kleiner Backoff
            time.sleep(0.8 * (attempt + 1))
        if last_err:
            raise ApiError(str(last_err))
        return None

    def get_warlog(self, clan_tag: str, limit: int = 10) -> list | None:
        """Hole die letzten Kriege eines Clans.
        Gibt Liste von Warlog-Items oder None (bei 404/privat) zurück.
        """
        etag = _encode_tag(clan_tag)
        data = self._get(f"/clans/{etag}/warlog", params={"limit": max(1, min(limit, 50))})
        if data is None:
            return None
        if isinstance(data, dict) and "items" in data:
            return t.cast(list, data["items"])  # API liefert {items: [...]}-Wrapper
        # Manche Wrapper variieren; fallback
        return t.cast(list, data)

    def get_currentwar(self, clan_tag: str) -> dict | None:
        """Hole den aktuellen Krieg für einen Clan.
        Gibt Dict oder None (z. B. wenn keinem Krieg beigetreten) zurück.
        """
        etag = _encode_tag(clan_tag)
        data = self._get(f"/clans/{etag}/currentwar")
        if not isinstance(data, dict):
            return None
        return data

    def get_player(self, player_tag: str) -> dict | None:
        """Hole Spieler-Informationen inkl. Clan-Zugehörigkeit.
        Gibt Dict mit player-Daten oder None zurück.
        """
        etag = _encode_tag(player_tag)
        data = self._get(f"/players/{etag}")
        if not isinstance(data, dict):
            return None
        return data

    # Optional: weitere Endpunkte, falls später benötigt
    def get_clan(self, clan_tag: str) -> dict | None:
        etag = _encode_tag(clan_tag)
        data = self._get(f"/clans/{etag}")
        if not isinstance(data, dict):
            return None
        return data
