"""RAG 파이프라인 커스텀 예외 클래스.

에러 원인별 세분화된 예외를 정의하여 라우터에서 적절한 HTTP 상태 코드와
사용자 친화적 메시지를 반환할 수 있도록 한다.
"""


class RateLimitError(Exception):
    """LLM API 요청 제한 초과 (429).

    Gemini 등 외부 LLM API에서 429 응답을 받았을 때 raise한다.
    재시도 후에도 실패한 경우 최종적으로 발생한다.
    """


class PipelineTimeoutError(Exception):
    """외부 API 호출 타임아웃.

    Gemini API 또는 데이터 소스 API 호출이 시간 내에 완료되지 않았을 때 raise한다.
    Python 내장 TimeoutError와의 이름 충돌을 피하기 위해 PipelineTimeoutError로 명명.
    """


class DataSourceError(Exception):
    """데이터 소스 연결 실패.

    Supabase, football-data.org, API-Football 등 외부 데이터 소스에
    연결할 수 없거나 비정상 응답을 받았을 때 raise한다.
    """


class GenerationError(Exception):
    """기타 답변 생성 실패.

    RateLimitError, PipelineTimeoutError, DataSourceError에 해당하지 않는
    생성 과정의 예외를 래핑한다.
    """
