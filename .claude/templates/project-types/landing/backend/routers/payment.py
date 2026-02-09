"""결제 라우터.

Stripe 결제 웹훅 및 API 엔드포인트.
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from core.logging import get_logger
from core.config import settings

router = APIRouter(prefix="/payment", tags=["payment"])
logger = get_logger("payment")


class CreateCheckoutRequest(BaseModel):
    """결제 세션 생성 요청."""
    price_id: str
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    """결제 세션 응답."""
    checkout_url: str
    session_id: str


@router.post("/create-checkout", response_model=CheckoutResponse)
async def create_checkout_session(request: CreateCheckoutRequest):
    """결제 세션 생성.

    Stripe Checkout 세션을 생성하고 URL을 반환합니다.

    TODO: Stripe SDK 연동 구현
    """
    logger.info(
        "결제 세션 생성 요청",
        price_id=request.price_id,
    )

    # TODO: Stripe 연동
    # import stripe
    # stripe.api_key = settings.STRIPE_SECRET_KEY
    # session = stripe.checkout.Session.create(
    #     payment_method_types=['card'],
    #     line_items=[{'price': request.price_id, 'quantity': 1}],
    #     mode='subscription',
    #     success_url=request.success_url,
    #     cancel_url=request.cancel_url,
    # )

    # 임시 응답 (개발용)
    return CheckoutResponse(
        checkout_url="https://checkout.stripe.com/placeholder",
        session_id="cs_test_placeholder",
    )


@router.post("/webhook")
async def payment_webhook(request: Request):
    """Stripe 웹훅 처리.

    결제 완료, 구독 갱신 등의 이벤트를 처리합니다.

    TODO: Stripe 웹훅 검증 및 이벤트 처리 구현
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    logger.info(
        "결제 웹훅 수신",
        signature=sig_header[:20] + "..." if sig_header else "없음",
    )

    # TODO: Stripe 웹훅 검증
    # try:
    #     event = stripe.Webhook.construct_event(
    #         payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
    #     )
    # except ValueError as e:
    #     raise HTTPException(status_code=400, detail="Invalid payload")
    # except stripe.error.SignatureVerificationError as e:
    #     raise HTTPException(status_code=400, detail="Invalid signature")

    # 이벤트 타입별 처리
    # if event['type'] == 'checkout.session.completed':
    #     session = event['data']['object']
    #     # 결제 완료 처리
    # elif event['type'] == 'customer.subscription.updated':
    #     subscription = event['data']['object']
    #     # 구독 업데이트 처리

    return {"status": "received"}


@router.get("/plans")
async def get_pricing_plans():
    """가격 플랜 조회.

    Returns:
        사용 가능한 가격 플랜 목록
    """
    # TODO: Stripe에서 가격 정보 조회 또는 DB에서 조회
    return {
        "plans": [
            {
                "id": "starter",
                "name": "Starter",
                "price": 9,
                "currency": "USD",
                "interval": "month",
                "features": [
                    "기본 기능",
                    "이메일 지원",
                    "1GB 저장공간",
                ],
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": 29,
                "currency": "USD",
                "interval": "month",
                "features": [
                    "모든 기능",
                    "우선 지원",
                    "10GB 저장공간",
                    "API 액세스",
                ],
            },
            {
                "id": "enterprise",
                "name": "Enterprise",
                "price": 99,
                "currency": "USD",
                "interval": "month",
                "features": [
                    "모든 기능",
                    "전담 지원",
                    "무제한 저장공간",
                    "커스텀 연동",
                    "SLA 보장",
                ],
            },
        ]
    }
