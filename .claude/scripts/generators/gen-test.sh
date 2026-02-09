#!/bin/bash
#
# 테스트 파일 생성기
# 버전: 1.0.0
#
# 사용법:
#   bash .claude/scripts/generators/gen-test.sh path/to/file.py
#   bash .claude/scripts/generators/gen-test.sh path/to/Component.tsx
#
# 예시:
#   bash .claude/scripts/generators/gen-test.sh dashboard/backend/services/user_service.py
#   bash .claude/scripts/generators/gen-test.sh dashboard/frontend/src/components/UserList/UserList.tsx
#

set -e

# =============================================================================
# 설정
# =============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# =============================================================================
# 입력 검증
# =============================================================================
if [ $# -lt 1 ]; then
    echo -e "${RED}❌ 사용법: $0 path/to/file${NC}"
    echo -e "${CYAN}예시: $0 dashboard/backend/services/user_service.py${NC}"
    exit 1
fi

SOURCE_FILE="$1"

if [ ! -f "$SOURCE_FILE" ]; then
    echo -e "${RED}❌ 파일을 찾을 수 없습니다: $SOURCE_FILE${NC}"
    exit 1
fi

# 파일 정보 추출
FILE_DIR=$(dirname "$SOURCE_FILE")
FILE_NAME=$(basename "$SOURCE_FILE")
FILE_EXT="${FILE_NAME##*.}"
FILE_BASE="${FILE_NAME%.*}"

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}🧪 테스트 파일 생성기${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "소스: ${GREEN}$SOURCE_FILE${NC}"
echo ""

# =============================================================================
# Python 테스트 생성
# =============================================================================
if [ "$FILE_EXT" = "py" ]; then
    TEST_FILE="$FILE_DIR/test_${FILE_BASE}.py"

    if [ -f "$TEST_FILE" ]; then
        echo -e "${RED}❌ 테스트 파일이 이미 존재합니다: $TEST_FILE${NC}"
        exit 1
    fi

    # 함수/클래스 추출
    FUNCTIONS=$(grep -E "^def [a-z_]+|^async def [a-z_]+|^class [A-Z]" "$SOURCE_FILE" 2>/dev/null | head -20 || true)

    # 테스트 파일 생성
    cat > "$TEST_FILE" << ENDOFPYTEST
"""
${FILE_BASE} 테스트.

자동 생성됨 — $(date '+%Y-%m-%d %H:%M:%S')
소스: ${SOURCE_FILE}
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

# TODO: 필요한 import 추가
# from ${FILE_BASE} import ...


class Test${FILE_BASE^}:
    """${FILE_BASE} 테스트 클래스."""

    @pytest.fixture
    def setup(self):
        """테스트 설정."""
        # TODO: 테스트 fixture 구현
        pass

ENDOFPYTEST

    # 함수별 테스트 골격 추가
    while IFS= read -r line; do
        if [[ "$line" =~ ^(async\ )?def\ ([a-z_]+) ]]; then
            func_name="${BASH_REMATCH[2]}"
            is_async="${BASH_REMATCH[1]}"

            if [ -n "$is_async" ]; then
                cat >> "$TEST_FILE" << ENDOFASYNCTEST

    @pytest.mark.asyncio
    async def test_${func_name}_success(self, setup):
        """
        ${func_name} 성공 케이스.

        Given: 유효한 입력
        When: ${func_name} 호출
        Then: 예상된 결과 반환
        """
        # TODO: mock 설정
        # TODO: 함수 호출
        # TODO: 결과 검증
        pass

    @pytest.mark.asyncio
    async def test_${func_name}_error(self, setup):
        """
        ${func_name} 에러 케이스.

        Given: 잘못된 입력
        When: ${func_name} 호출
        Then: 적절한 예외 발생
        """
        # TODO: 에러 케이스 구현
        pass

    @pytest.mark.asyncio
    async def test_${func_name}_edge_case(self, setup):
        """
        ${func_name} 엣지 케이스.

        Given: 경계값 또는 빈 입력
        When: ${func_name} 호출
        Then: 적절한 처리
        """
        # TODO: 엣지 케이스 구현
        pass
ENDOFASYNCTEST
            else
                cat >> "$TEST_FILE" << ENDOFSYNCTEST

    def test_${func_name}_success(self, setup):
        """
        ${func_name} 성공 케이스.

        Given: 유효한 입력
        When: ${func_name} 호출
        Then: 예상된 결과 반환
        """
        # TODO: 함수 호출 및 검증
        pass

    def test_${func_name}_error(self, setup):
        """
        ${func_name} 에러 케이스.

        Given: 잘못된 입력
        When: ${func_name} 호출
        Then: 적절한 예외 발생
        """
        # TODO: 에러 케이스 구현
        pass

    def test_${func_name}_edge_case(self, setup):
        """
        ${func_name} 엣지 케이스.

        Given: 경계값 또는 빈 입력
        When: ${func_name} 호출
        Then: 적절한 처리
        """
        # TODO: 엣지 케이스 구현
        pass
ENDOFSYNCTEST
            fi
        fi

        if [[ "$line" =~ ^class\ ([A-Z][a-zA-Z]+) ]]; then
            class_name="${BASH_REMATCH[1]}"
            cat >> "$TEST_FILE" << ENDOFCLASSTEST


class Test${class_name}:
    """${class_name} 클래스 테스트."""

    @pytest.fixture
    def instance(self):
        """테스트 인스턴스."""
        # TODO: 인스턴스 생성
        # return ${class_name}(...)
        pass

    def test_init(self, instance):
        """초기화 테스트."""
        # TODO: 초기화 검증
        pass
ENDOFCLASSTEST
        fi
    done <<< "$FUNCTIONS"

    echo -e "${GREEN}✅ 생성: $TEST_FILE${NC}"

fi

# =============================================================================
# TypeScript/React 테스트 생성
# =============================================================================
if [[ "$FILE_EXT" =~ ^(ts|tsx)$ ]]; then
    TEST_FILE="$FILE_DIR/${FILE_BASE}.test.${FILE_EXT}"

    if [ -f "$TEST_FILE" ]; then
        echo -e "${RED}❌ 테스트 파일이 이미 존재합니다: $TEST_FILE${NC}"
        exit 1
    fi

    # 컴포넌트/함수 추출
    EXPORTS=$(grep -E "^export (function|const|class)" "$SOURCE_FILE" 2>/dev/null | head -10 || true)

    # React 컴포넌트인지 확인
    IS_COMPONENT=false
    if grep -q "React\|jsx\|tsx" "$SOURCE_FILE" 2>/dev/null; then
        IS_COMPONENT=true
    fi

    if [ "$IS_COMPONENT" = true ]; then
        cat > "$TEST_FILE" << ENDOFREACTTEST
/**
 * ${FILE_BASE} 컴포넌트 테스트
 * 자동 생성됨 — $(date '+%Y-%m-%d %H:%M:%S')
 * 소스: ${SOURCE_FILE}
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ${FILE_BASE} } from './${FILE_BASE}';

describe('${FILE_BASE}', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('렌더링', () => {
    it('컴포넌트가 정상적으로 렌더링되어야 한다', () => {
      // Given: 기본 props
      // When: 컴포넌트 렌더링
      render(<${FILE_BASE} />);

      // Then: 컴포넌트 존재 확인
      // TODO: 적절한 요소 확인
      // expect(screen.getByRole('...')).toBeInTheDocument();
    });

    it('로딩 상태를 표시해야 한다', () => {
      // Given: 로딩 중인 상태
      // When: 컴포넌트 렌더링
      // Then: 로딩 UI 표시
      // TODO: 로딩 상태 테스트
    });

    it('에러 상태를 표시해야 한다', () => {
      // Given: 에러 발생
      // When: 컴포넌트 렌더링
      // Then: 에러 메시지 표시
      // TODO: 에러 상태 테스트
    });
  });

  describe('인터랙션', () => {
    it('클릭 이벤트를 처리해야 한다', async () => {
      // Given: 렌더링된 컴포넌트
      render(<${FILE_BASE} />);

      // When: 버튼 클릭
      // const button = screen.getByRole('button');
      // fireEvent.click(button);

      // Then: 적절한 동작 수행
      // TODO: 클릭 핸들러 테스트
    });
  });

  describe('엣지 케이스', () => {
    it('빈 데이터를 처리해야 한다', () => {
      // Given: 빈 데이터
      // When: 컴포넌트 렌더링
      // Then: 적절한 빈 상태 표시
      // TODO: 빈 상태 테스트
    });
  });
});
ENDOFREACTTEST
    else
        cat > "$TEST_FILE" << ENDOFTSTEST
/**
 * ${FILE_BASE} 테스트
 * 자동 생성됨 — $(date '+%Y-%m-%d %H:%M:%S')
 * 소스: ${SOURCE_FILE}
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
// TODO: 필요한 import 추가
// import { ... } from './${FILE_BASE}';

describe('${FILE_BASE}', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

ENDOFTSTEST

        # 함수별 테스트 추가
        while IFS= read -r line; do
            if [[ "$line" =~ export\ (function|const)\ ([a-zA-Z]+) ]]; then
                func_name="${BASH_REMATCH[2]}"
                cat >> "$TEST_FILE" << ENDOFFUNCTEST
  describe('${func_name}', () => {
    it('성공 케이스를 처리해야 한다', () => {
      // Given: 유효한 입력
      // When: ${func_name} 호출
      // Then: 예상된 결과 반환
      // TODO: 테스트 구현
    });

    it('에러 케이스를 처리해야 한다', () => {
      // Given: 잘못된 입력
      // When: ${func_name} 호출
      // Then: 적절한 예외 발생
      // TODO: 에러 케이스 구현
    });

    it('엣지 케이스를 처리해야 한다', () => {
      // Given: 경계값 또는 빈 입력
      // When: ${func_name} 호출
      // Then: 적절한 처리
      // TODO: 엣지 케이스 구현
    });
  });

ENDOFFUNCTEST
            fi
        done <<< "$EXPORTS"

        echo "});" >> "$TEST_FILE"
    fi

    echo -e "${GREEN}✅ 생성: $TEST_FILE${NC}"
fi

# =============================================================================
# 결과 출력
# =============================================================================
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ 테스트 파일 생성 완료${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}다음 단계:${NC}"
echo -e "  1. 생성된 테스트 파일에서 TODO 항목 구현"
echo -e "  2. 필요한 mock 설정 추가"
echo -e "  3. 테스트 실행: pytest (Python) 또는 npm test (TypeScript)"
echo ""
