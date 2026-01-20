from __future__ import annotations
from typing import Any
from cli.models import Config, QueueItem

import requests

class ApiClient:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    def _url(self, path: str) -> str:
        return f"{self.cfg.api_base}{path}"

    def _q(self, suffix: str) -> str:
        return f"/queues/{self.cfg.queue_id}{suffix}"

    @staticmethod
    def _json_or_error(r: requests.Response) -> dict:
        ct = (r.headers.get("content-type") or "").lower()
        if "application/json" in ct:
            return r.json()
        return {"ok": False, "error": r.text.strip(), "status": r.status_code}

    def health_ok(self) -> bool:    
        try:
            r = requests.get(self._url("/health"), timeout=5)
            if r.status_code != 200:
                return False
            data = self._json_or_error(r)
            return bool(data.get("ok"))
        except Exception:
            return False

    def fetch_queue_size(self) -> int | None:
        try:
            r = requests.get(self._url(self._q("/size")), timeout=8)
            if r.status_code != 200:
                return None
            data = self._json_or_error(r)
            if not data.get("ok"):
                return None
            return int(data.get("size"))
        except Exception:
            return None

    def enqueue(self, lookup: str, *, limit: int = 200) -> dict:
        data: dict[str, Any] = {"lookup": lookup, "limit": str(limit)}
        r = requests.post(self._url(self._q("/enqueue")), data=data, timeout=20)
        return self._json_or_error(r)

    def fetch_next_item(self) -> QueueItem | None:
        r = requests.post(self._url(self._q("/next")), timeout=15)
        if r.status_code == 204:
            return None
        data = self._json_or_error(r)
        if not data.get("ok"):
            return None
        item = data.get("item")
        if not isinstance(item, dict):
            return None
        qi = QueueItem.from_dict(item)
        if not qi.kind or not qi.value:
            return None
        return qi

    def fetch_peek_items(self) -> QueueItem | None:
        r = requests.get(self._url(self._q("/peek")), timeout=15)
        if r.status_code == 204:
            return None
        data = self._json_or_error(r)
        if not data.get("ok"):
            return None
        item = data.get("item")
        if not isinstance(item, dict):
            return None
        qi = QueueItem.from_dict(item)
        if not qi.kind or not qi.value:
            return None
        return qi

    def snapshot(self, *, limit: int = 10) -> dict:
        r = requests.get(self._url(self._q("")), params={"limit": str(limit)}, timeout=20)
        return self._json_or_error(r)

    def clear(self) -> dict:
        r = requests.post(self._url(self._q("/clear")), timeout=15)
        return self._json_or_error(r)

    def resolve(self, item: QueueItem) -> dict:
        r = requests.post(self._url("/resolve"), json=item.to_resolve_payload(), timeout=30)
        return self._json_or_error(r)