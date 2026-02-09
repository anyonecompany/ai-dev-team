#!/bin/bash
#
# FastAPI CRUD API 생성기
# 버전: 1.0.0
#
# 사용법:
#   bash .claude/scripts/generators/gen-api-crud.sh ModelName "field1:type field2:type"
#
# 예시:
#   bash .claude/scripts/generators/gen-api-crud.sh User "name:str email:str age:int is_active:bool"
#   bash .claude/scripts/generators/gen-api-crud.sh Product "title:str price:float stock:int"
#

set -e

# =============================================================================
# 설정
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"
BACKEND_DIR="$PROJECT_ROOT/dashboard/backend"

# 색상
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# =============================================================================
# 입력 검증
# =============================================================================
if [ $# -lt 2 ]; then
    echo -e "${RED}❌ 사용법: $0 ModelName \"field1:type field2:type ...\"${NC}"
    echo -e "${CYAN}예시: $0 User \"name:str email:str age:int\"${NC}"
    exit 1
fi

MODEL_NAME="$1"
FIELDS="$2"

# 모델명 검증 (PascalCase)
if [[ ! "$MODEL_NAME" =~ ^[A-Z][a-zA-Z0-9]*$ ]]; then
    echo -e "${RED}❌ 모델명은 PascalCase여야 합니다 (예: User, Product)${NC}"
    exit 1
fi

# 소문자 변환
MODEL_LOWER=$(echo "$MODEL_NAME" | tr '[:upper:]' '[:lower:]')
MODEL_SNAKE=$(echo "$MODEL_NAME" | sed 's/\([A-Z]\)/_\L\1/g' | sed 's/^_//')

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}🔧 CRUD API 생성기${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "모델: ${GREEN}$MODEL_NAME${NC}"
echo -e "필드: ${GREEN}$FIELDS${NC}"
echo ""

# =============================================================================
# 디렉토리 생성
# =============================================================================
mkdir -p "$BACKEND_DIR/schemas"
mkdir -p "$BACKEND_DIR/services"
mkdir -p "$BACKEND_DIR/routers"

# =============================================================================
# 타입 매핑 함수
# =============================================================================
map_python_type() {
    local field_type="$1"
    case "$field_type" in
        str|string) echo "str" ;;
        int|integer) echo "int" ;;
        float|number) echo "float" ;;
        bool|boolean) echo "bool" ;;
        datetime) echo "datetime" ;;
        date) echo "date" ;;
        list) echo "List" ;;
        dict) echo "Dict" ;;
        uuid) echo "str" ;;
        *) echo "str" ;;
    esac
}

# =============================================================================
# 필드 파싱
# =============================================================================
FIELD_DEFS=""
FIELD_DEFS_OPTIONAL=""
FIELD_NAMES=""

for field in $FIELDS; do
    IFS=':' read -r fname ftype <<< "$field"
    ptype=$(map_python_type "$ftype")

    FIELD_DEFS+="    $fname: $ptype\n"
    FIELD_DEFS_OPTIONAL+="    $fname: Optional[$ptype] = None\n"
    FIELD_NAMES+="$fname "
done

# =============================================================================
# 파일 존재 확인
# =============================================================================
SCHEMA_FILE="$BACKEND_DIR/schemas/${MODEL_LOWER}.py"
SERVICE_FILE="$BACKEND_DIR/services/${MODEL_LOWER}_service.py"
ROUTER_FILE="$BACKEND_DIR/routers/${MODEL_LOWER}.py"

for file in "$SCHEMA_FILE" "$SERVICE_FILE" "$ROUTER_FILE"; do
    if [ -f "$file" ]; then
        echo -e "${RED}❌ 파일이 이미 존재합니다: $file${NC}"
        echo -e "${YELLOW}덮어쓰려면 먼저 삭제하세요.${NC}"
        exit 1
    fi
done

# =============================================================================
# 1. Schema 파일 생성
# =============================================================================
cat > "$SCHEMA_FILE" << ENDOFSCHEMA
"""${MODEL_NAME} 스키마 정의.

자동 생성됨 — $(date '+%Y-%m-%d %H:%M:%S')
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ${MODEL_NAME}Create(BaseModel):
    """${MODEL_NAME} 생성 스키마."""

$(echo -e "$FIELD_DEFS")

class ${MODEL_NAME}Update(BaseModel):
    """${MODEL_NAME} 업데이트 스키마."""

$(echo -e "$FIELD_DEFS_OPTIONAL")

class ${MODEL_NAME}Response(BaseModel):
    """${MODEL_NAME} 응답 스키마."""

    id: str
$(echo -e "$FIELD_DEFS")    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
ENDOFSCHEMA

echo -e "${GREEN}✅ 생성: $SCHEMA_FILE${NC}"

# =============================================================================
# 2. Service 파일 생성
# =============================================================================
cat > "$SERVICE_FILE" << ENDOFSERVICE
"""${MODEL_NAME} 서비스.

Supabase CRUD 함수.
자동 생성됨 — $(date '+%Y-%m-%d %H:%M:%S')
"""

from typing import List, Optional
from datetime import datetime
import uuid

import structlog
from supabase import Client

from schemas.${MODEL_LOWER} import ${MODEL_NAME}Create, ${MODEL_NAME}Update, ${MODEL_NAME}Response


logger = structlog.get_logger("services.${MODEL_LOWER}")

TABLE_NAME = "${MODEL_LOWER}s"


class ${MODEL_NAME}Service:
    """${MODEL_NAME} CRUD 서비스."""

    def __init__(self, supabase: Client):
        """서비스 초기화."""
        self.db = supabase

    async def create(self, data: ${MODEL_NAME}Create) -> ${MODEL_NAME}Response:
        """
        ${MODEL_NAME} 생성.

        Args:
            data: 생성할 데이터

        Returns:
            생성된 ${MODEL_NAME}
        """
        now = datetime.utcnow().isoformat()
        record = {
            "id": str(uuid.uuid4()),
            **data.model_dump(),
            "created_at": now,
            "updated_at": now,
        }

        result = self.db.table(TABLE_NAME).insert(record).execute()
        logger.info("${MODEL_NAME} 생성됨", id=record["id"])
        return ${MODEL_NAME}Response(**result.data[0])

    async def get(self, id: str) -> Optional[${MODEL_NAME}Response]:
        """
        ${MODEL_NAME} 조회.

        Args:
            id: ${MODEL_NAME} ID

        Returns:
            ${MODEL_NAME} 또는 None
        """
        result = self.db.table(TABLE_NAME).select("*").eq("id", id).execute()
        if not result.data:
            return None
        return ${MODEL_NAME}Response(**result.data[0])

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[${MODEL_NAME}Response]:
        """
        ${MODEL_NAME} 목록 조회.

        Args:
            skip: 건너뛸 개수
            limit: 조회할 개수

        Returns:
            ${MODEL_NAME} 목록
        """
        result = (
            self.db.table(TABLE_NAME)
            .select("*")
            .order("created_at", desc=True)
            .range(skip, skip + limit - 1)
            .execute()
        )
        return [${MODEL_NAME}Response(**row) for row in result.data]

    async def update(
        self,
        id: str,
        data: ${MODEL_NAME}Update,
    ) -> Optional[${MODEL_NAME}Response]:
        """
        ${MODEL_NAME} 업데이트.

        Args:
            id: ${MODEL_NAME} ID
            data: 업데이트할 데이터

        Returns:
            업데이트된 ${MODEL_NAME} 또는 None
        """
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get(id)

        update_data["updated_at"] = datetime.utcnow().isoformat()

        result = (
            self.db.table(TABLE_NAME)
            .update(update_data)
            .eq("id", id)
            .execute()
        )

        if not result.data:
            return None

        logger.info("${MODEL_NAME} 업데이트됨", id=id)
        return ${MODEL_NAME}Response(**result.data[0])

    async def delete(self, id: str) -> bool:
        """
        ${MODEL_NAME} 삭제.

        Args:
            id: ${MODEL_NAME} ID

        Returns:
            삭제 성공 여부
        """
        result = self.db.table(TABLE_NAME).delete().eq("id", id).execute()
        if result.data:
            logger.info("${MODEL_NAME} 삭제됨", id=id)
            return True
        return False
ENDOFSERVICE

echo -e "${GREEN}✅ 생성: $SERVICE_FILE${NC}"

# =============================================================================
# 3. Router 파일 생성
# =============================================================================
cat > "$ROUTER_FILE" << ENDOFROUTER
"""${MODEL_NAME} API 라우터.

자동 생성됨 — $(date '+%Y-%m-%d %H:%M:%S')
"""

from typing import List

from fastapi import APIRouter, HTTPException, Query, Depends
import structlog

from schemas.${MODEL_LOWER} import ${MODEL_NAME}Create, ${MODEL_NAME}Update, ${MODEL_NAME}Response
from services.${MODEL_LOWER}_service import ${MODEL_NAME}Service
from core.dependencies import get_supabase


router = APIRouter(prefix="/${MODEL_LOWER}s", tags=["${MODEL_NAME}"])
logger = structlog.get_logger("api.${MODEL_LOWER}")


def get_service(supabase=Depends(get_supabase)) -> ${MODEL_NAME}Service:
    """${MODEL_NAME}Service 의존성."""
    return ${MODEL_NAME}Service(supabase)


@router.post("/", response_model=${MODEL_NAME}Response, status_code=201)
async def create_${MODEL_LOWER}(
    data: ${MODEL_NAME}Create,
    service: ${MODEL_NAME}Service = Depends(get_service),
):
    """
    ${MODEL_NAME} 생성.

    Args:
        data: 생성 데이터

    Returns:
        생성된 ${MODEL_NAME}
    """
    return await service.create(data)


@router.get("/{id}", response_model=${MODEL_NAME}Response)
async def get_${MODEL_LOWER}(
    id: str,
    service: ${MODEL_NAME}Service = Depends(get_service),
):
    """
    ${MODEL_NAME} 조회.

    Args:
        id: ${MODEL_NAME} ID

    Returns:
        ${MODEL_NAME}

    Raises:
        404: ${MODEL_NAME}를 찾을 수 없음
    """
    result = await service.get(id)
    if not result:
        raise HTTPException(status_code=404, detail="${MODEL_NAME}을(를) 찾을 수 없습니다.")
    return result


@router.get("/", response_model=List[${MODEL_NAME}Response])
async def list_${MODEL_LOWER}s(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: ${MODEL_NAME}Service = Depends(get_service),
):
    """
    ${MODEL_NAME} 목록 조회.

    Args:
        skip: 건너뛸 개수
        limit: 조회할 개수

    Returns:
        ${MODEL_NAME} 목록
    """
    return await service.list(skip=skip, limit=limit)


@router.put("/{id}", response_model=${MODEL_NAME}Response)
async def update_${MODEL_LOWER}(
    id: str,
    data: ${MODEL_NAME}Update,
    service: ${MODEL_NAME}Service = Depends(get_service),
):
    """
    ${MODEL_NAME} 업데이트.

    Args:
        id: ${MODEL_NAME} ID
        data: 업데이트 데이터

    Returns:
        업데이트된 ${MODEL_NAME}

    Raises:
        404: ${MODEL_NAME}를 찾을 수 없음
    """
    result = await service.update(id, data)
    if not result:
        raise HTTPException(status_code=404, detail="${MODEL_NAME}을(를) 찾을 수 없습니다.")
    return result


@router.delete("/{id}")
async def delete_${MODEL_LOWER}(
    id: str,
    service: ${MODEL_NAME}Service = Depends(get_service),
):
    """
    ${MODEL_NAME} 삭제.

    Args:
        id: ${MODEL_NAME} ID

    Returns:
        삭제 결과

    Raises:
        404: ${MODEL_NAME}를 찾을 수 없음
    """
    success = await service.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail="${MODEL_NAME}을(를) 찾을 수 없습니다.")
    return {"status": "deleted", "id": id}
ENDOFROUTER

echo -e "${GREEN}✅ 생성: $ROUTER_FILE${NC}"

# =============================================================================
# 결과 출력
# =============================================================================
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ ${MODEL_NAME} CRUD API 생성 완료${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "생성된 파일:"
echo -e "  ${CYAN}schemas/${MODEL_LOWER}.py${NC}          - Pydantic 스키마"
echo -e "  ${CYAN}services/${MODEL_LOWER}_service.py${NC} - CRUD 서비스"
echo -e "  ${CYAN}routers/${MODEL_LOWER}.py${NC}          - API 라우터"
echo ""
echo -e "${YELLOW}다음 단계:${NC}"
echo -e "  1. main.py에 라우터 등록:"
echo -e "     ${CYAN}from routers.${MODEL_LOWER} import router as ${MODEL_LOWER}_router${NC}"
echo -e "     ${CYAN}app.include_router(${MODEL_LOWER}_router, prefix=\"/api\")${NC}"
echo -e "  2. Supabase에 테이블 생성 (gen-migration.sh 사용)"
echo ""
