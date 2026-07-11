import logging
from typing import Optional

from app.config import Settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def send_match_notification(
        self,
        to_email: str,
        item_title: str,
        match_title: str,
        confidence: float,
    ) -> None:
        subject = f"LostLink: Possible match found for '{item_title}'"
        body = (
            f"Good news! We found a possible match for your item '{item_title}'.\n\n"
            f"Matched item: {match_title}\n"
            f"Confidence score: {confidence * 100:.1f}%\n\n"
            f"Log in to LostLink to review and claim the item."
        )
        await self._send_email(to_email, subject, body)

    async def send_claim_notification(
        self,
        to_email: str,
        item_title: str,
        claimer_name: str,
    ) -> None:
        subject = f"LostLink: Claim request for '{item_title}'"
        body = (
            f"{claimer_name} has submitted a claim for your item '{item_title}'.\n\n"
            f"Please review the claim in your LostLink dashboard."
        )
        await self._send_email(to_email, subject, body)

    async def send_claim_status_notification(
        self,
        to_email: str,
        item_title: str,
        approved: bool,
    ) -> None:
        status_text = "approved" if approved else "rejected"
        subject = f"LostLink: Your claim for '{item_title}' was {status_text}"
        body = f"Your claim for '{item_title}' has been {status_text}."
        await self._send_email(to_email, subject, body)

    async def _send_email(self, to_email: str, subject: str, body: str) -> None:
        if not self.settings.resend_api_key:
            logger.info("Email skipped (no API key): %s -> %s", subject, to_email)
            return

        try:
            import resend

            resend.api_key = self.settings.resend_api_key
            resend.Emails.send(
                {
                    "from": self.settings.email_from,
                    "to": [to_email],
                    "subject": subject,
                    "text": body,
                }
            )
        except Exception:
            logger.exception("Failed to send email to %s", to_email)
