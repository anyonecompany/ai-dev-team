#!/bin/bash
#
# Supabase 마이그레이션 생성기
# 버전: 1.0.0
#
# 사용법:
#   bash .claude/scripts/generators/gen-migration.sh "migration_name" "field1:type field2:type:modifier"
#
# 필드 타입:
#   text, integer, boolean, float (→real), datetime (→timestamptz), json (→jsonb), uuid
#
# 수식어 (optional):
#   unique, nullable, default:value
#
# 예시:
#   bash .claude/scripts/generators/gen-migration.sh "create_users_table" "name:text email:text:unique age:integer"
#   bash .claude/scripts/generators/gen-migration.sh "create_products_table" "title:text price:float:default:0 stock:integer:default:0"
#

set -e

# =============================================================================
# 설정
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"
SUPABASE_DIR="$PROJECT_ROOT/dashboard/supabase"
MIGRATIONS_DIR="$SUPABASE_DIR/migrations"

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
    echo -e "${RED}❌ 사용법: $0 \"migration_name\" \"field1:type field2:type:modifier\"${NC}"
    echo -e "${CYAN}예시: $0 \"create_users_table\" \"name:text email:text:unique age:integer\"${NC}"
    exit 1
fi

MIGRATION_NAME="$1"
FIELDS="$2"

# 마이그레이션 이름에서 테이블 이름 추출
TABLE_NAME=$(echo "$MIGRATION_NAME" | sed 's/create_//' | sed 's/_table//')

# 타임스탬프
TIMESTAMP=$(date '+%Y%m%d%H%M%S')
MIGRATION_FILE="$MIGRATIONS_DIR/${TIMESTAMP}_${MIGRATION_NAME}.sql"

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}🗄️  Supabase 마이그레이션 생성기${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "마이그레이션: ${GREEN}$MIGRATION_NAME${NC}"
echo -e "테이블: ${GREEN}$TABLE_NAME${NC}"
echo -e "필드: ${GREEN}$FIELDS${NC}"
echo ""

# =============================================================================
# 디렉토리 생성
# =============================================================================
mkdir -p "$MIGRATIONS_DIR"

# =============================================================================
# 타입 매핑 함수
# =============================================================================
map_sql_type() {
    local field_type="$1"
    case "$field_type" in
        text|string|str) echo "TEXT" ;;
        integer|int) echo "INTEGER" ;;
        boolean|bool) echo "BOOLEAN" ;;
        float|number|real) echo "REAL" ;;
        datetime|timestamp|timestamptz) echo "TIMESTAMPTZ" ;;
        date) echo "DATE" ;;
        json|jsonb) echo "JSONB" ;;
        uuid) echo "UUID" ;;
        bigint) echo "BIGINT" ;;
        smallint) echo "SMALLINT" ;;
        *) echo "TEXT" ;;
    esac
}

# =============================================================================
# 필드 파싱 및 SQL 생성
# =============================================================================
COLUMN_DEFS=""
INDEX_DEFS=""
UNIQUE_COLUMNS=""

for field in $FIELDS; do
    # 필드 파싱: name:type:modifier1:modifier2...
    IFS=':' read -ra PARTS <<< "$field"

    FIELD_NAME="${PARTS[0]}"
    FIELD_TYPE=$(map_sql_type "${PARTS[1]}")

    # 기본값: NOT NULL
    NULLABLE="NOT NULL"
    DEFAULT_VAL=""
    IS_UNIQUE=false

    # 수식어 처리
    for ((i=2; i<${#PARTS[@]}; i++)); do
        modifier="${PARTS[$i]}"
        case "$modifier" in
            unique)
                IS_UNIQUE=true
                ;;
            nullable)
                NULLABLE=""
                ;;
            default)
                # 다음 부분이 기본값
                if [ $((i+1)) -lt ${#PARTS[@]} ]; then
                    default_value="${PARTS[$((i+1))]}"
                    case "$FIELD_TYPE" in
                        TEXT) DEFAULT_VAL="DEFAULT '$default_value'" ;;
                        BOOLEAN)
                            if [ "$default_value" = "true" ]; then
                                DEFAULT_VAL="DEFAULT true"
                            else
                                DEFAULT_VAL="DEFAULT false"
                            fi
                            ;;
                        *) DEFAULT_VAL="DEFAULT $default_value" ;;
                    esac
                    ((i++))
                fi
                ;;
        esac
    done

    # 컬럼 정의 추가
    COLUMN_DEFS+="  ${FIELD_NAME} ${FIELD_TYPE} ${NULLABLE} ${DEFAULT_VAL},\n"

    # UNIQUE 인덱스 추가
    if [ "$IS_UNIQUE" = true ]; then
        UNIQUE_COLUMNS+="CREATE UNIQUE INDEX IF NOT EXISTS idx_${TABLE_NAME}_${FIELD_NAME} ON ${TABLE_NAME}(${FIELD_NAME});\n"
    fi

    # 일반 인덱스 (text, uuid 필드)
    if [[ "$FIELD_TYPE" =~ ^(TEXT|UUID)$ ]] && [ "$IS_UNIQUE" = false ]; then
        INDEX_DEFS+="CREATE INDEX IF NOT EXISTS idx_${TABLE_NAME}_${FIELD_NAME} ON ${TABLE_NAME}(${FIELD_NAME});\n"
    fi
done

# =============================================================================
# 마이그레이션 파일 생성
# =============================================================================
cat > "$MIGRATION_FILE" << ENDOFSQL
-- Migration: ${MIGRATION_NAME}
-- Created: $(date '+%Y-%m-%d %H:%M:%S')
-- 자동 생성됨

-- ============================================================================
-- 테이블 생성
-- ============================================================================

CREATE TABLE IF NOT EXISTS ${TABLE_NAME} (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
$(echo -e "$COLUMN_DEFS" | sed 's/,$//')
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- Row Level Security (RLS)
-- ============================================================================

ALTER TABLE ${TABLE_NAME} ENABLE ROW LEVEL SECURITY;

-- 기본 정책 (인증된 사용자만 접근)
-- TODO: 프로젝트 요구사항에 맞게 정책 수정
CREATE POLICY "Enable read for authenticated users" ON ${TABLE_NAME}
  FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Enable insert for authenticated users" ON ${TABLE_NAME}
  FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Enable update for authenticated users" ON ${TABLE_NAME}
  FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Enable delete for authenticated users" ON ${TABLE_NAME}
  FOR DELETE
  TO authenticated
  USING (true);

-- ============================================================================
-- 인덱스
-- ============================================================================

-- 기본 인덱스
CREATE INDEX IF NOT EXISTS idx_${TABLE_NAME}_created_at ON ${TABLE_NAME}(created_at);
CREATE INDEX IF NOT EXISTS idx_${TABLE_NAME}_updated_at ON ${TABLE_NAME}(updated_at);

-- UNIQUE 인덱스
$(echo -e "$UNIQUE_COLUMNS")
-- 일반 인덱스
$(echo -e "$INDEX_DEFS")
-- ============================================================================
-- updated_at 자동 갱신 트리거
-- ============================================================================

-- 트리거 함수 (없으면 생성)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS \$\$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
\$\$ language 'plpgsql';

-- 트리거 적용
DROP TRIGGER IF EXISTS update_${TABLE_NAME}_updated_at ON ${TABLE_NAME};
CREATE TRIGGER update_${TABLE_NAME}_updated_at
  BEFORE UPDATE ON ${TABLE_NAME}
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 롤백 (필요 시 주석 해제)
-- ============================================================================

-- DROP TRIGGER IF EXISTS update_${TABLE_NAME}_updated_at ON ${TABLE_NAME};
-- DROP TABLE IF EXISTS ${TABLE_NAME};
ENDOFSQL

echo -e "${GREEN}✅ 생성: $MIGRATION_FILE${NC}"

# =============================================================================
# 결과 출력
# =============================================================================
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ 마이그레이션 파일 생성 완료${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}다음 단계:${NC}"
echo -e "  1. 생성된 파일 검토: ${CYAN}cat $MIGRATION_FILE${NC}"
echo -e "  2. RLS 정책 프로젝트 요구사항에 맞게 수정"
echo -e "  3. Supabase에 적용:"
echo -e "     - Supabase Dashboard > SQL Editor에서 실행"
echo -e "     - 또는 supabase db push (Supabase CLI)"
echo ""
