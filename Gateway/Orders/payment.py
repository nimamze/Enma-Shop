from dataclasses import dataclass
import requests
from django.conf import settings


@dataclass
class ZarinPalResult:
    ok: bool
    code: int | None = None
    message: str = ""
    authority: str | None = None
    payment_url: str | None = None
    ref_id: str | None = None
    raw: dict | None = None


class ZarinPalClient:
    def __init__(self):
        self.merchant_id = settings.ZARINPAL_MERCHANT_ID
        self.request_url = settings.ZARINPAL_REQUEST_URL
        self.verify_url = settings.ZARINPAL_VERIFY_URL
        self.startpay_url = settings.ZARINPAL_STARTPAY_URL
        self.callback_url = settings.ZARINPAL_CALLBACK_URL
        self.currency = settings.ZARINPAL_CURRENCY
        self.timeout = settings.ZARINPAL_TIMEOUT

    def request_payment(self, *, amount, description, metadata=None, cart_data=None):
        if not self.merchant_id or not self.callback_url:
            raise ValueError("ZarinPal merchant ID or callback URL is not configured.")
        payload = {
            "merchant_id": self.merchant_id,
            "amount": amount,
            "currency": self.currency,
            "description": description,
            "callback_url": self.callback_url,
        }
        if metadata:
            payload["metadata"] = metadata
        if cart_data:
            payload["cart_data"] = cart_data
        response = requests.post(
            self.request_url,
            json=payload,
            timeout=self.timeout,
            headers={"accept": "application/json"},
        )
        response.raise_for_status()
        body = response.json()
        data = body.get("data") or {}
        errors = body.get("errors") or {}
        code = data.get("code")
        authority = data.get("authority")
        if code == 100 and authority:
            return ZarinPalResult(
                ok=True,
                code=code,
                message=data.get("message", "Success"),
                authority=authority,
                payment_url=f"{self.startpay_url}{authority}",
                raw=body,
            )
        error_message = data.get("message") or errors.get("message") or "Payment error."
        return ZarinPalResult(
            ok=False,
            code=code,
            message=error_message,
            raw=body,
        )

    def verify_payment(self, *, amount, authority):
        if not self.merchant_id:
            raise ValueError("ZarinPal merchant ID is not configured.")
        payload = {
            "merchant_id": self.merchant_id,
            "amount": amount,
            "authority": authority,
        }
        response = requests.post(
            self.verify_url,
            json=payload,
            timeout=self.timeout,
            headers={"accept": "application/json"},
        )
        response.raise_for_status()
        body = response.json()
        data = body.get("data") or {}
        errors = body.get("errors") or {}
        code = data.get("code")
        ok = code in (100, 101)
        message = data.get("message") or errors.get("message") or "Verification error."
        return ZarinPalResult(
            ok=ok,
            code=code,
            message=message,
            authority=authority,
            ref_id=str(data.get("ref_id")) if data.get("ref_id") is not None else None,
            raw=body,
        )
