"""결제 서비스.

Stripe 결제 처리 (skeleton).
"""

from typing import Optional
from core.logging import get_logger

logger = get_logger("services.payment")


class PaymentService:
    """결제 서비스.

    Stripe를 사용한 구독 결제 처리.
    TODO: Stripe SDK 연동 구현
    """

    def __init__(self, stripe_key: str):
        """서비스 초기화.

        Args:
            stripe_key: Stripe Secret Key
        """
        self.stripe_key = stripe_key
        # TODO: stripe.api_key = stripe_key

    async def create_checkout_session(
        self,
        price_id: str,
        user_id: str,
        success_url: str,
        cancel_url: str,
    ) -> dict:
        """결제 세션 생성.

        Args:
            price_id: Stripe Price ID
            user_id: 사용자 ID (메타데이터용)
            success_url: 결제 성공 리다이렉트 URL
            cancel_url: 결제 취소 리다이렉트 URL

        Returns:
            checkout_url, session_id
        """
        logger.info(
            "결제 세션 생성",
            price_id=price_id,
            user_id=user_id,
        )

        # TODO: Stripe Checkout Session 생성
        # session = stripe.checkout.Session.create(
        #     payment_method_types=['card'],
        #     line_items=[{'price': price_id, 'quantity': 1}],
        #     mode='subscription',
        #     success_url=success_url,
        #     cancel_url=cancel_url,
        #     client_reference_id=user_id,
        #     metadata={'user_id': user_id},
        # )

        # 임시 응답
        return {
            "checkout_url": "https://checkout.stripe.com/placeholder",
            "session_id": "cs_test_placeholder",
        }

    async def get_subscription(self, user_id: str) -> Optional[dict]:
        """구독 정보 조회.

        Args:
            user_id: 사용자 ID

        Returns:
            구독 정보 또는 None
        """
        logger.info("구독 조회", user_id=user_id)

        # TODO: 실제 구독 정보 조회
        # 1. DB에서 user_id로 stripe_customer_id 조회
        # 2. Stripe에서 구독 정보 조회

        return None

    async def cancel_subscription(self, subscription_id: str) -> bool:
        """구독 취소.

        Args:
            subscription_id: Stripe Subscription ID

        Returns:
            취소 성공 여부
        """
        logger.info("구독 취소", subscription_id=subscription_id)

        # TODO: stripe.Subscription.modify(subscription_id, cancel_at_period_end=True)

        return True

    async def handle_webhook(self, payload: bytes, signature: str) -> dict:
        """웹훅 처리.

        Args:
            payload: 웹훅 바디
            signature: Stripe-Signature 헤더

        Returns:
            처리 결과
        """
        logger.info("웹훅 수신")

        # TODO: Stripe 웹훅 검증 및 이벤트 처리
        # event = stripe.Webhook.construct_event(payload, signature, webhook_secret)
        #
        # if event['type'] == 'checkout.session.completed':
        #     session = event['data']['object']
        #     await self._handle_checkout_completed(session)
        #
        # elif event['type'] == 'customer.subscription.updated':
        #     subscription = event['data']['object']
        #     await self._handle_subscription_updated(subscription)
        #
        # elif event['type'] == 'customer.subscription.deleted':
        #     subscription = event['data']['object']
        #     await self._handle_subscription_deleted(subscription)

        return {"received": True}

    async def _handle_checkout_completed(self, session: dict):
        """결제 완료 처리."""
        user_id = session.get("client_reference_id")
        subscription_id = session.get("subscription")

        logger.info(
            "결제 완료",
            user_id=user_id,
            subscription_id=subscription_id,
        )

        # TODO: DB에 구독 정보 저장

    async def _handle_subscription_updated(self, subscription: dict):
        """구독 업데이트 처리."""
        subscription_id = subscription.get("id")
        status = subscription.get("status")

        logger.info(
            "구독 업데이트",
            subscription_id=subscription_id,
            status=status,
        )

        # TODO: DB 업데이트

    async def _handle_subscription_deleted(self, subscription: dict):
        """구독 취소 처리."""
        subscription_id = subscription.get("id")

        logger.info(
            "구독 취소됨",
            subscription_id=subscription_id,
        )

        # TODO: DB 업데이트
