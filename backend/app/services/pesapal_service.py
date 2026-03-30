import logging
from typing import Any, Dict

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class PesapalServiceError(RuntimeError):
    pass


class PesapalService:
    def __init__(self) -> None:
        self.base_url = settings.PESAPAL_BASE_URL.rstrip("/")
        self.consumer_key = settings.PESAPAL_CONSUMER_KEY
        self.consumer_secret = settings.PESAPAL_CONSUMER_SECRET

    def _ensure_credentials(self) -> None:
        if not self.consumer_key or not self.consumer_secret:
            raise PesapalServiceError("Pesapal credentials are not configured.")

    def get_access_token(self) -> str:
        self._ensure_credentials()
        endpoint = f"{self.base_url}/api/Auth/RequestToken"
        payload = {
            "consumer_key": self.consumer_key,
            "consumer_secret": self.consumer_secret,
        }
        try:
            response = httpx.post(endpoint, json=payload, timeout=30.0)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            logger.exception("pesapal_auth_failed", extra={"error": str(exc)})
            raise PesapalServiceError("Failed to authenticate with Pesapal.") from exc

        token = data.get("token")
        if not token:
            logger.error("pesapal_auth_missing_token", extra={"response": data})
            raise PesapalServiceError("Pesapal authentication succeeded without token.")
        return str(token)

    def submit_order_request(self, order_payload: Dict[str, Any]) -> Dict[str, Any]:
        token = self.get_access_token()
        endpoint = f"{self.base_url}/api/Transactions/SubmitOrderRequest"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            response = httpx.post(endpoint, json=order_payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            logger.exception("pesapal_submit_order_failed", extra={"error": str(exc)})
            raise PesapalServiceError("Failed to submit order request to Pesapal.") from exc

        if data.get("status") == "200" and data.get("redirect_url") and data.get("order_tracking_id"):
            return data

        if data.get("error"):
            raise PesapalServiceError(f"Pesapal order request failed: {data.get('error')}")
        raise PesapalServiceError("Pesapal order request did not return required fields.")

    def get_transaction_status(self, order_tracking_id: str) -> Dict[str, Any]:
        if not order_tracking_id:
            raise PesapalServiceError("Order tracking ID is required.")

        token = self.get_access_token()
        endpoint = f"{self.base_url}/api/Transactions/GetTransactionStatus"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"orderTrackingId": order_tracking_id}

        try:
            response = httpx.get(endpoint, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            logger.exception(
                "pesapal_get_status_failed",
                extra={"error": str(exc), "order_tracking_id": order_tracking_id},
            )
            raise PesapalServiceError("Failed to retrieve transaction status from Pesapal.") from exc

