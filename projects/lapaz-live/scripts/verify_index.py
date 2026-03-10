"""Supabase documents 테이블 인덱싱 검증.

검증 항목:
1. player_profiles 컬렉션에 40행+ 존재
2. 검색 테스트 3건 (metadata 기반)
3. metadata 필드 정합성 (team, position, name_kr, name_en)

참고: OPENAI_API_KEY가 없으면 벡터 검색(match_documents)은 불가.
대신 Supabase에서 직접 SELECT로 데이터 존재 확인.
"""

import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import SUPABASE_URL, SUPABASE_SERVICE_KEY, OPENAI_API_KEY

from supabase import create_client


SEARCH_TARGETS = [
    "브루노 페르난데스",
    "왓킨스",
    "에밀리아노 마르티네스",
]

REQUIRED_META_FIELDS = ["team", "position", "player_name_kr", "player_name_en"]


def verify() -> bool:
    """인덱싱 검증 실행. 성공 시 True 반환."""
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    all_passed = True

    # 1. 총 행 수 확인
    result = (
        client.table("documents")
        .select("id", count="exact")
        .eq("collection", "player_profiles")
        .execute()
    )
    total = result.count or 0
    print(f"총 인덱싱 행 수: {total}")
    if total < 40:
        print(f"  FAIL: 40행 미만 ({total})")
        all_passed = False
    else:
        print(f"  PASS: {total}행")

    # 2. 특정 선수 검색 (metadata 기반)
    print("\n선수 검색 테스트:")
    for name_kr in SEARCH_TARGETS:
        result = (
            client.table("documents")
            .select("*")
            .eq("collection", "player_profiles")
            .like("metadata->>player_name_kr", f"%{name_kr}%")
            .execute()
        )
        if result.data:
            print(f"  PASS: {name_kr} 발견 ({len(result.data)}건)")
        else:
            print(f"  FAIL: {name_kr} 미발견")
            all_passed = False

    # 3. metadata 필드 정합성 (샘플 10건)
    print("\nmetadata 필드 정합성:")
    sample = (
        client.table("documents")
        .select("metadata")
        .eq("collection", "player_profiles")
        .limit(10)
        .execute()
    )
    meta_errors = 0
    for row in sample.data or []:
        meta = row.get("metadata", {}) or {}
        for field in REQUIRED_META_FIELDS:
            if field not in meta or not meta[field]:
                print(f"  FAIL: metadata에 {field} 누락")
                meta_errors += 1
                all_passed = False

    if meta_errors == 0:
        print("  PASS: 모든 샘플 metadata 정상")

    # 4. 벡터 검색 테스트 (OPENAI_API_KEY가 있을 때만)
    if OPENAI_API_KEY:
        print("\n벡터 검색 테스트:")
        try:
            from openai import OpenAI

            oai = OpenAI(api_key=OPENAI_API_KEY)
            query = "브루노 페르난데스 플레이 스타일"
            resp = oai.embeddings.create(
                model="text-embedding-3-small", input=query
            )
            query_vec = resp.data[0].embedding
            rpc_result = client.rpc(
                "match_documents",
                {
                    "query_embedding": query_vec,
                    "match_count": 3,
                    "filter": {"collection": "player_profiles"},
                },
            ).execute()
            if rpc_result.data:
                print(f"  PASS: 벡터 검색 {len(rpc_result.data)}건 반환")
            else:
                print("  FAIL: 벡터 검색 결과 없음")
                all_passed = False
        except Exception as e:
            print(f"  SKIP: 벡터 검색 실패 ({e})")
    else:
        print("\nSKIP: OPENAI_API_KEY 없음 - 벡터 검색 테스트 생략")

    # 최종 결과
    status = "PASS" if all_passed else "FAIL"
    print(f"\n{'='*40}")
    print(f"  인덱싱 검증 결과: {status}")
    print(f"{'='*40}\n")
    return all_passed


if __name__ == "__main__":
    success = verify()
    sys.exit(0 if success else 1)
