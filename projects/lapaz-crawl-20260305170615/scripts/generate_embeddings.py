"""764건 documents에 Voyage AI voyage-3 임베딩 생성 스크립트."""

import os
import sys
import time

import voyageai
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

BATCH_SIZE = 50  # Voyage API 배치 제한


def main():
    voyage_key = os.environ.get("VOYAGE_API_KEY")
    if not voyage_key:
        print("VOYAGE_API_KEY가 .env에 설정되어 있지 않습니다.")
        sys.exit(1)

    vo = voyageai.Client(api_key=voyage_key)
    supabase = create_client(
        os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"]
    )

    # 임베딩이 NULL인 문서 조회
    print("임베딩이 없는 문서 조회 중...")
    result = (
        supabase.table("documents")
        .select("id, content")
        .is_("embedding", "null")
        .order("id")
        .execute()
    )
    docs = result.data or []
    total = len(docs)
    print(f"총 {total}건의 문서에 임베딩 생성 필요 (voyage-3, 1024차원)")

    if total == 0:
        print("모든 문서에 이미 임베딩이 있습니다.")
        return

    success = 0
    errors = 0

    for i in range(0, total, BATCH_SIZE):
        batch = docs[i : i + BATCH_SIZE]
        texts = [doc["content"][:8000] for doc in batch]

        try:
            response = vo.embed(texts, model="voyage-3", input_type="document")
            embeddings = response.embeddings
        except Exception as e:
            print(f"  배치 {i // BATCH_SIZE + 1} 임베딩 생성 실패: {e}")
            errors += len(batch)
            continue

        for j, embedding in enumerate(embeddings):
            doc_id = batch[j]["id"]

            try:
                supabase.table("documents").update(
                    {"embedding": embedding}
                ).eq("id", doc_id).execute()
                success += 1
            except Exception as e:
                print(f"  문서 {doc_id} 업데이트 실패: {e}")
                errors += 1

        processed = min(i + BATCH_SIZE, total)
        elapsed_pct = processed / total * 100
        print(f"  진행률: {processed}/{total} ({elapsed_pct:.1f}%) - 성공: {success}, 실패: {errors}")

        # rate limit 방지
        if i + BATCH_SIZE < total:
            time.sleep(1)

    print(f"\n완료! 성공: {success}, 실패: {errors}, 전체: {total}")


if __name__ == "__main__":
    main()
