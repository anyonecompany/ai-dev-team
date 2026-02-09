#!/bin/bash
#
# React 컴포넌트 생성기
# 버전: 1.0.0
#
# 사용법:
#   bash .claude/scripts/generators/gen-component.sh ComponentName type
#
# 타입:
#   page - 페이지 컴포넌트 (데이터 로딩, 레이아웃)
#   form - 폼 컴포넌트 (입력, 유효성 검증)
#   list - 리스트 컴포넌트 (목록, 페이지네이션)
#
# 예시:
#   bash .claude/scripts/generators/gen-component.sh UserProfile page
#   bash .claude/scripts/generators/gen-component.sh LoginForm form
#   bash .claude/scripts/generators/gen-component.sh UserList list
#

set -e

# =============================================================================
# 설정
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"
FRONTEND_DIR="$PROJECT_ROOT/dashboard/frontend"
COMPONENTS_DIR="$FRONTEND_DIR/src/components"

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
    echo -e "${RED}❌ 사용법: $0 ComponentName type${NC}"
    echo -e "${CYAN}타입: page, form, list${NC}"
    echo -e "${CYAN}예시: $0 UserProfile page${NC}"
    exit 1
fi

COMPONENT_NAME="$1"
COMPONENT_TYPE="$2"

# 컴포넌트명 검증 (PascalCase)
if [[ ! "$COMPONENT_NAME" =~ ^[A-Z][a-zA-Z0-9]*$ ]]; then
    echo -e "${RED}❌ 컴포넌트명은 PascalCase여야 합니다 (예: UserProfile)${NC}"
    exit 1
fi

# 타입 검증
if [[ ! "$COMPONENT_TYPE" =~ ^(page|form|list)$ ]]; then
    echo -e "${RED}❌ 타입은 page, form, list 중 하나여야 합니다${NC}"
    exit 1
fi

COMPONENT_DIR="$COMPONENTS_DIR/$COMPONENT_NAME"

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}🔧 React 컴포넌트 생성기${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "컴포넌트: ${GREEN}$COMPONENT_NAME${NC}"
echo -e "타입: ${GREEN}$COMPONENT_TYPE${NC}"
echo ""

# =============================================================================
# 디렉토리 존재 확인
# =============================================================================
if [ -d "$COMPONENT_DIR" ]; then
    echo -e "${RED}❌ 컴포넌트 디렉토리가 이미 존재합니다: $COMPONENT_DIR${NC}"
    exit 1
fi

mkdir -p "$COMPONENT_DIR"

# =============================================================================
# 타입 파일 생성 (공통)
# =============================================================================
cat > "$COMPONENT_DIR/types.ts" << ENDOFTYPES
/**
 * ${COMPONENT_NAME} 컴포넌트 타입 정의
 * 자동 생성됨 — $(date '+%Y-%m-%d %H:%M:%S')
 */

export interface ${COMPONENT_NAME}Props {
  className?: string;
  // TODO: 필요한 props 추가
}

export interface ${COMPONENT_NAME}State {
  isLoading: boolean;
  error: string | null;
  // TODO: 필요한 state 추가
}
ENDOFTYPES

# =============================================================================
# Page 타입 컴포넌트
# =============================================================================
if [ "$COMPONENT_TYPE" = "page" ]; then

cat > "$COMPONENT_DIR/${COMPONENT_NAME}.tsx" << 'ENDOFPAGE'
/**
 * COMPONENT_NAME 페이지 컴포넌트
 * 자동 생성됨 — TIMESTAMP
 */

import { useEffect, useState } from 'react';
import type { COMPONENT_NAMEProps } from './types';

export function COMPONENT_NAME({ className = '' }: COMPONENT_NAMEProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<unknown>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        // TODO: 데이터 로드 로직
        // const result = await api.getData();
        // setData(result);
        setData({ message: 'Hello' });
      } catch (err) {
        setError(err instanceof Error ? err.message : '데이터를 불러오는데 실패했습니다.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  if (isLoading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-gray-500">로딩 중...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  return (
    <div className={`p-4 ${className}`}>
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">COMPONENT_NAME</h1>
      </header>

      <main>
        {/* TODO: 페이지 콘텐츠 구현 */}
        <pre className="bg-gray-100 p-4 rounded">
          {JSON.stringify(data, null, 2)}
        </pre>
      </main>
    </div>
  );
}
ENDOFPAGE

sed -i '' "s/COMPONENT_NAME/${COMPONENT_NAME}/g" "$COMPONENT_DIR/${COMPONENT_NAME}.tsx"
sed -i '' "s/TIMESTAMP/$(date '+%Y-%m-%d %H:%M:%S')/g" "$COMPONENT_DIR/${COMPONENT_NAME}.tsx"

fi

# =============================================================================
# Form 타입 컴포넌트
# =============================================================================
if [ "$COMPONENT_TYPE" = "form" ]; then

cat > "$COMPONENT_DIR/${COMPONENT_NAME}.tsx" << 'ENDOFFORM'
/**
 * COMPONENT_NAME 폼 컴포넌트
 * 자동 생성됨 — TIMESTAMP
 */

import { useState, FormEvent, ChangeEvent } from 'react';
import type { COMPONENT_NAMEProps } from './types';

interface FormData {
  // TODO: 폼 필드 정의
  field1: string;
  field2: string;
}

interface FormErrors {
  field1?: string;
  field2?: string;
}

export function COMPONENT_NAME({ className = '' }: COMPONENT_NAMEProps) {
  const [formData, setFormData] = useState<FormData>({
    field1: '',
    field2: '',
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const validate = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.field1.trim()) {
      newErrors.field1 = '필수 입력 항목입니다.';
    }

    if (!formData.field2.trim()) {
      newErrors.field2 = '필수 입력 항목입니다.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // 입력 시 해당 필드 에러 클리어
    if (errors[name as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitError(null);

    if (!validate()) {
      return;
    }

    try {
      setIsSubmitting(true);
      // TODO: 폼 제출 로직
      // await api.submit(formData);
      console.log('Form submitted:', formData);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : '제출에 실패했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className={`space-y-4 ${className}`}>
      {submitError && (
        <div className="p-3 bg-red-100 text-red-700 rounded">
          {submitError}
        </div>
      )}

      <div>
        <label htmlFor="field1" className="block text-sm font-medium text-gray-700">
          Field 1
        </label>
        <input
          type="text"
          id="field1"
          name="field1"
          value={formData.field1}
          onChange={handleChange}
          className={`mt-1 block w-full rounded border px-3 py-2 ${
            errors.field1 ? 'border-red-500' : 'border-gray-300'
          }`}
        />
        {errors.field1 && (
          <p className="mt-1 text-sm text-red-500">{errors.field1}</p>
        )}
      </div>

      <div>
        <label htmlFor="field2" className="block text-sm font-medium text-gray-700">
          Field 2
        </label>
        <input
          type="text"
          id="field2"
          name="field2"
          value={formData.field2}
          onChange={handleChange}
          className={`mt-1 block w-full rounded border px-3 py-2 ${
            errors.field2 ? 'border-red-500' : 'border-gray-300'
          }`}
        />
        {errors.field2 && (
          <p className="mt-1 text-sm text-red-500">{errors.field2}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {isSubmitting ? '제출 중...' : '제출'}
      </button>
    </form>
  );
}
ENDOFFORM

sed -i '' "s/COMPONENT_NAME/${COMPONENT_NAME}/g" "$COMPONENT_DIR/${COMPONENT_NAME}.tsx"
sed -i '' "s/TIMESTAMP/$(date '+%Y-%m-%d %H:%M:%S')/g" "$COMPONENT_DIR/${COMPONENT_NAME}.tsx"

fi

# =============================================================================
# List 타입 컴포넌트
# =============================================================================
if [ "$COMPONENT_TYPE" = "list" ]; then

# 리스트 아이템 컴포넌트
cat > "$COMPONENT_DIR/${COMPONENT_NAME}Item.tsx" << 'ENDOFITEM'
/**
 * COMPONENT_NAMEItem 컴포넌트
 * 자동 생성됨 — TIMESTAMP
 */

interface ItemProps {
  item: {
    id: string;
    title: string;
    // TODO: 아이템 필드 추가
  };
  onSelect?: (id: string) => void;
}

export function COMPONENT_NAMEItem({ item, onSelect }: ItemProps) {
  return (
    <div
      onClick={() => onSelect?.(item.id)}
      className="p-4 border-b hover:bg-gray-50 cursor-pointer"
    >
      <h3 className="font-medium">{item.title}</h3>
      {/* TODO: 아이템 내용 구현 */}
    </div>
  );
}
ENDOFITEM

sed -i '' "s/COMPONENT_NAME/${COMPONENT_NAME}/g" "$COMPONENT_DIR/${COMPONENT_NAME}Item.tsx"
sed -i '' "s/TIMESTAMP/$(date '+%Y-%m-%d %H:%M:%S')/g" "$COMPONENT_DIR/${COMPONENT_NAME}Item.tsx"

# 메인 리스트 컴포넌트
cat > "$COMPONENT_DIR/${COMPONENT_NAME}.tsx" << 'ENDOFLIST'
/**
 * COMPONENT_NAME 리스트 컴포넌트
 * 자동 생성됨 — TIMESTAMP
 */

import { useEffect, useState } from 'react';
import type { COMPONENT_NAMEProps } from './types';
import { COMPONENT_NAMEItem } from './COMPONENT_NAMEItem';

interface Item {
  id: string;
  title: string;
}

export function COMPONENT_NAME({ className = '' }: COMPONENT_NAMEProps) {
  const [items, setItems] = useState<Item[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const ITEMS_PER_PAGE = 20;

  useEffect(() => {
    const fetchItems = async () => {
      try {
        setIsLoading(true);
        setError(null);
        // TODO: 데이터 로드 로직
        // const result = await api.getItems({ page, limit: ITEMS_PER_PAGE });
        // setItems(prev => page === 1 ? result : [...prev, ...result]);
        // setHasMore(result.length === ITEMS_PER_PAGE);

        // 샘플 데이터
        const sampleItems = Array.from({ length: 5 }, (_, i) => ({
          id: `${page}-${i}`,
          title: `Item ${(page - 1) * ITEMS_PER_PAGE + i + 1}`,
        }));
        setItems((prev) => (page === 1 ? sampleItems : [...prev, ...sampleItems]));
        setHasMore(page < 3);
      } catch (err) {
        setError(err instanceof Error ? err.message : '데이터를 불러오는데 실패했습니다.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchItems();
  }, [page]);

  const handleSelect = (id: string) => {
    console.log('Selected:', id);
    // TODO: 선택 처리
  };

  const handleLoadMore = () => {
    if (!isLoading && hasMore) {
      setPage((prev) => prev + 1);
    }
  };

  if (error && items.length === 0) {
    return (
      <div className={`p-8 text-center ${className}`}>
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  if (!isLoading && items.length === 0) {
    return (
      <div className={`p-8 text-center text-gray-500 ${className}`}>
        데이터가 없습니다.
      </div>
    );
  }

  return (
    <div className={className}>
      <div className="divide-y">
        {items.map((item) => (
          <COMPONENT_NAMEItem
            key={item.id}
            item={item}
            onSelect={handleSelect}
          />
        ))}
      </div>

      {isLoading && (
        <div className="p-4 text-center text-gray-500">
          로딩 중...
        </div>
      )}

      {!isLoading && hasMore && (
        <button
          onClick={handleLoadMore}
          className="w-full p-4 text-blue-600 hover:bg-gray-50"
        >
          더 보기
        </button>
      )}
    </div>
  );
}
ENDOFLIST

sed -i '' "s/COMPONENT_NAME/${COMPONENT_NAME}/g" "$COMPONENT_DIR/${COMPONENT_NAME}.tsx"
sed -i '' "s/TIMESTAMP/$(date '+%Y-%m-%d %H:%M:%S')/g" "$COMPONENT_DIR/${COMPONENT_NAME}.tsx"

fi

# =============================================================================
# Index 파일 생성 (공통)
# =============================================================================
cat > "$COMPONENT_DIR/index.tsx" << ENDOFINDEX
/**
 * ${COMPONENT_NAME} 컴포넌트 export
 * 자동 생성됨 — $(date '+%Y-%m-%d %H:%M:%S')
 */

export { ${COMPONENT_NAME} } from './${COMPONENT_NAME}';
export type { ${COMPONENT_NAME}Props } from './types';
ENDOFINDEX

# =============================================================================
# 결과 출력
# =============================================================================
echo -e "${GREEN}✅ ${COMPONENT_NAME} 컴포넌트 생성 완료${NC}"
echo ""
echo -e "생성된 파일:"
ls -la "$COMPONENT_DIR" | grep -v "^total\|^\."
echo ""
echo -e "${YELLOW}사용법:${NC}"
echo -e "  ${CYAN}import { ${COMPONENT_NAME} } from '@/components/${COMPONENT_NAME}';${NC}"
echo ""
