import stripe
from src.config import settings

stripe.api_key = settings.stripe_secret_key

class StripeService:
    def create_checkout_session(self, user_email: str, price_id: str):
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{'price': price_id, 'quantity': 1}],
                mode='subscription',
                success_url=f"{settings.cors_origins[0]}/success",
                cancel_url=f"{settings.cors_origins[0]}/cancel",
                customer_email=user_email,
            )
            return session.url
        except Exception as e:
            return str(e)

stripe_service = StripeService()