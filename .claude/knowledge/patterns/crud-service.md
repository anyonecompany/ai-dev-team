# CRUD Service Pattern

> 카테고리: Backend / Service Layer
> 출처: dashboard/backend/services/chat_storage.py, api/tasks.py
> 최종 갱신: 2026-02-03

## 개요

파일 기반 또는 Supabase 기반 CRUD 서비스 패턴.
서비스 레이어에서 데이터 접근을 추상화하고, 라우터에서는 비즈니스 로직에 집중합니다.

## 구현

### 1. 파일 기반 저장소 서비스

```python
# services/storage_service.py
"""파일 기반 저장소 서비스."""

import os
import json
from datetime import datetime
from typing import List, Optional, TypeVar, Generic
from pydantic import BaseModel

from core.config import settings

T = TypeVar('T', bound=BaseModel)


class FileStorageService(Generic[T]):
    """파일 기반 CRUD 저장소."""

    def __init__(self, model_class: type[T], filename: str):
        self.model_class = model_class
        self.storage_dir = os.path.join(settings.PROJECT_ROOT, ".data")
        self.storage_file = os.path.join(self.storage_dir, f"{filename}.json")
        os.makedirs(self.storage_dir, exist_ok=True)

    def _load(self) -> List[dict]:
        """파일에서 데이터 로드."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def _save(self, data: List[dict]) -> None:
        """파일에 데이터 저장."""
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list(self, **filters) -> List[T]:
        """목록 조회 (필터링 지원)."""
        data = self._load()

        for key, value in filters.items():
            if value is not None:
                data = [d for d in data if d.get(key) == value]

        return [self.model_class(**d) for d in data]

    def get(self, id: str) -> Optional[T]:
        """단건 조회."""
        data = self._load()
        for item in data:
            if item.get("id") == id:
                return self.model_class(**item)
        return None

    def create(self, item: T) -> T:
        """생성."""
        data = self._load()
        item_dict = item.model_dump()
        item_dict["created_at"] = datetime.now().isoformat()
        item_dict["updated_at"] = item_dict["created_at"]
        data.append(item_dict)
        self._save(data)
        return self.model_class(**item_dict)

    def update(self, id: str, updates: dict) -> Optional[T]:
        """수정."""
        data = self._load()
        for i, item in enumerate(data):
            if item.get("id") == id:
                item.update(updates)
                item["updated_at"] = datetime.now().isoformat()
                data[i] = item
                self._save(data)
                return self.model_class(**item)
        return None

    def delete(self, id: str) -> bool:
        """삭제."""
        data = self._load()
        original_len = len(data)
        data = [d for d in data if d.get("id") != id]
        if len(data) < original_len:
            self._save(data)
            return True
        return False
```

### 2. Supabase 기반 저장소 서비스

```python
# services/db_service.py
"""Supabase 기반 CRUD 서비스."""

from typing import List, Optional, TypeVar, Generic
from pydantic import BaseModel

from core.database import get_db

T = TypeVar('T', bound=BaseModel)


class SupabaseService(Generic[T]):
    """Supabase CRUD 서비스."""

    def __init__(self, model_class: type[T], table_name: str):
        self.model_class = model_class
        self.table_name = table_name

    def _get_table(self):
        db = get_db()
        if not db:
            raise Exception("Database not initialized")
        return db.table(self.table_name)

    async def list(self, **filters) -> List[T]:
        """목록 조회."""
        query = self._get_table().select("*")

        for key, value in filters.items():
            if value is not None:
                query = query.eq(key, value)

        response = query.execute()
        return [self.model_class(**item) for item in response.data]

    async def get(self, id: str) -> Optional[T]:
        """단건 조회."""
        response = self._get_table().select("*").eq("id", id).single().execute()
        return self.model_class(**response.data) if response.data else None

    async def create(self, item: T) -> T:
        """생성."""
        response = self._get_table().insert(item.model_dump()).execute()
        return self.model_class(**response.data[0])

    async def update(self, id: str, updates: dict) -> Optional[T]:
        """수정."""
        response = self._get_table().update(updates).eq("id", id).execute()
        return self.model_class(**response.data[0]) if response.data else None

    async def delete(self, id: str) -> bool:
        """삭제."""
        response = self._get_table().delete().eq("id", id).execute()
        return len(response.data) > 0
```

### 3. 라우터에서 사용 (의존성 주입)

```python
# api/items.py
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends

from models import Item, ItemCreate, ItemUpdate
from core.dependencies import ItemServiceDep

router = APIRouter()


@router.get("/", response_model=List[Item])
async def list_items(
    service: ItemServiceDep,
    status: Optional[str] = None,
):
    """아이템 목록 조회."""
    return await service.list(status=status)


@router.get("/{item_id}", response_model=Item)
async def get_item(item_id: str, service: ItemServiceDep):
    """아이템 조회."""
    item = await service.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다.")
    return item


@router.post("/", response_model=Item)
async def create_item(item: ItemCreate, service: ItemServiceDep):
    """아이템 생성."""
    return await service.create(Item(**item.model_dump()))


@router.patch("/{item_id}", response_model=Item)
async def update_item(
    item_id: str,
    updates: ItemUpdate,
    service: ItemServiceDep,
):
    """아이템 수정."""
    item = await service.update(item_id, updates.model_dump(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다.")
    return item


@router.delete("/{item_id}")
async def delete_item(item_id: str, service: ItemServiceDep):
    """아이템 삭제."""
    success = await service.delete(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다.")
    return {"status": "deleted", "id": item_id}
```

## 장점

1. **관심사 분리**: 데이터 접근 로직을 서비스 레이어에 격리
2. **교체 용이**: 파일 ↔ Supabase 등 저장소 교체 가능
3. **테스트 용이**: 서비스 모킹으로 라우터 테스트
4. **타입 안전**: Pydantic 모델로 타입 검증
5. **일관된 패턴**: 모든 엔티티에 동일한 CRUD 인터페이스

## 관련 패턴

- [dependencies.py - 의존성 주입](#)
- [supabase-connection.md - DB 연결](#)
