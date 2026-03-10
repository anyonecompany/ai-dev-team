"""Notion API 클라이언트 — httpx 직접 호출 (notion-client 2.7.0 호환)."""

import time
from typing import Any

import httpx
from notion_client import Client
from notion_client.errors import APIResponseError

from .config import NOTION_API_KEY

_RATE_LIMIT_SLEEP = 0.4
_RETRY_SLEEP = 3.0
_NOTION_VERSION = "2022-06-28"


class NotionClient:
    """Notion API 래퍼."""

    def __init__(self) -> None:
        self.client = Client(auth=NOTION_API_KEY)
        self._http = httpx.Client(
            base_url="https://api.notion.com/v1/",
            headers={
                "Authorization": f"Bearer {NOTION_API_KEY}",
                "Notion-Version": _NOTION_VERSION,
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    def _sleep(self) -> None:
        time.sleep(_RATE_LIMIT_SLEEP)

    def _retry_once(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            result = func(*args, **kwargs)
            self._sleep()
            return result
        except APIResponseError:
            time.sleep(_RETRY_SLEEP)
            result = func(*args, **kwargs)
            self._sleep()
            return result

    def query_db(self, database_id: str, filter: dict | None = None) -> list[dict]:
        """DB 쿼리 (페이지네이션 포함)."""
        results: list[dict] = []
        has_more = True
        start_cursor: str | None = None
        while has_more:
            body: dict[str, Any] = {}
            if filter:
                body["filter"] = filter
            if start_cursor:
                body["start_cursor"] = start_cursor
            resp = self._http.post(f"databases/{database_id}/query", json=body)
            resp.raise_for_status()
            data = resp.json()
            self._sleep()
            results.extend(data["results"])
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")
        return results

    def create_page(
        self,
        parent_db_id: str,
        properties: dict,
        children: list[dict] | None = None,
        icon: str | None = None,
    ) -> dict:
        """DB에 새 페이지 생성."""
        kwargs: dict[str, Any] = {
            "parent": {"database_id": parent_db_id},
            "properties": properties,
        }
        if children:
            kwargs["children"] = children
        if icon:
            kwargs["icon"] = {"type": "emoji", "emoji": icon}
        return self._retry_once(self.client.pages.create, **kwargs)

    def update_page(self, page_id: str, properties: dict) -> dict:
        """페이지 속성 업데이트."""
        return self._retry_once(self.client.pages.update, page_id=page_id, properties=properties)

    def find_project_by_name(self, project_name: str) -> str | None:
        """프로젝트명으로 page_id 반환."""
        from .config import PROJECT_DB_ID
        results = self.query_db(PROJECT_DB_ID, filter={
            "property": "프로젝트명",
            "title": {"equals": project_name},
        })
        return results[0]["id"] if results else None


_instance: NotionClient | None = None


def get_client() -> NotionClient:
    """싱글턴 클라이언트."""
    global _instance
    if _instance is None:
        _instance = NotionClient()
    return _instance
