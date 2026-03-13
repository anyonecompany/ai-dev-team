"""Notion API wrapper with rate limiting and retry."""

import time
from typing import Any

import httpx
from notion_client import Client
from notion_client.errors import APIResponseError

from .config import NOTION_API_KEY

_RATE_LIMIT_SLEEP = 0.4
_RETRY_SLEEP = 3.0
_NOTION_VERSION = "2022-06-28"


class NotionClientWrapper:
    """Notion API 래퍼. 속도 제한 대응 및 재시도 포함."""

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
        """1회 재시도."""
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
        """DB 쿼리. 전체 결과를 페이지네이션으로 수집.

        notion-client v2.7.0 (API 2025-09-03)에서 databases.query가 제거됨.
        2022-06-28 버전 헤더로 직접 HTTP 호출.
        """
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

    def create_page(self, parent_db_id: str, properties: dict, children: list[dict] | None = None) -> dict:
        """DB에 새 페이지 생성."""
        kwargs: dict[str, Any] = {
            "parent": {"database_id": parent_db_id},
            "properties": properties,
        }
        if children:
            kwargs["children"] = children
        return self._retry_once(self.client.pages.create, **kwargs)

    def update_page(self, page_id: str, properties: dict) -> dict:
        """페이지 속성 업데이트."""
        return self._retry_once(self.client.pages.update, page_id=page_id, properties=properties)

    def find_project_by_name(self, project_name: str) -> str | None:
        """프로젝트명으로 검색하여 page_id 반환."""
        from .config import PROJECT_DB_ID

        results = self.query_db(
            PROJECT_DB_ID,
            filter={
                "property": "\ud504\ub85c\uc81d\ud2b8\uba85",
                "title": {"equals": project_name},
            },
        )
        if results:
            return results[0]["id"]
        return None


# 싱글턴
_instance: NotionClientWrapper | None = None


def get_client() -> NotionClientWrapper:
    """싱글턴 클라이언트 반환."""
    global _instance
    if _instance is None:
        _instance = NotionClientWrapper()
    return _instance
