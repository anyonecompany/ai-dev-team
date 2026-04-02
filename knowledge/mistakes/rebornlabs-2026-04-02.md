# 리본랩스 어드민 — 추가 이슈들 (2026-04-01~02)

## 10. Supabase 뷰의 user_role() 함수 의존성
- vehicles_dealer_view, dealers_name_view가 user_role() IN (...) 조건 사용
- service_role JWT에는 user_role 클레임이 없어서 'none' 반환 → 빈 결과
- 교훈: service_role로 조회할 때는 뷰 대신 테이블 직접 조회. 뷰의 user_role() 조건은 RLS가 아닌 쿼리 조건이므로 service_role도 차단됨.

## 11. pdf-lib + 한글 폰트 topDict 에러
- Pretendard OTF → 임베딩 성공, drawText에서 topDict undefined 에러
- NotoSansKR TTF → drawText는 성공, 한글 글자 사이 이상한 문자(ⴠ) 삽입
- 교훈: pdf-lib의 한글(CJK) 지원은 불안정. HTML→PDF(html2pdf.js, puppeteer) 방식이 안전.

## 12. puppeteer Vercel 빌드 실패
- puppeteer-core + @sparticuz/chromium 설치 → Turbopack 빌드에서 31개 에러
- native 모듈 의존성이 Vercel Serverless와 비호환
- 교훈: Vercel에서 puppeteer는 사용 불가. 클라이언트 사이드 html2pdf.js 또는 외부 PDF 서비스 사용.

## 13. Server Component에서 cookies().set() 불가
- layout.tsx에서 프로필 캐시 쿠키 설정 시도 → 500 에러
- Next.js 16에서 Server Component는 쿠키 읽기만 가능
- 교훈: 쿠키 설정은 미들웨어(proxy.ts) 또는 Route Handler에서만.

## 14. apiFetch FormData Content-Type 충돌
- FormData body에 Content-Type: application/json 자동 설정 → multipart boundary 누락
- 모든 파일 업로드(서명/계약서/증빙/사진) API에서 400 에러
- 교훈: FormData 전송 시 Content-Type 헤더를 설정하지 않아야 함 (브라우저가 자동 설정).

## 15. API-프론트 필드명 불일치 반복 발생
- dashboard: monthly_sales vs month_sales
- settlements: total_dealer_fee vs total_dealer_fees
- contracts/sign: data.data vs data.contract
- 교훈: API 응답 타입과 프론트 인터페이스를 한 곳에서 관리하거나, 응답 직후 타입 검증.
