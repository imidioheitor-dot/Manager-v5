import logging
import os

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)


class SlackService:
    def __init__(self) -> None:
        self._client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
        self._user_id = os.getenv("SLACK_USER_ID")

        if not self._user_id:
            raise ValueError("SLACK_USER_ID must be set in environment variables.")

    def send_direct_message(self, message: str) -> None:
        try:
            response = self._client.chat_postMessage(
                channel=self._user_id,
                text=message,
                mrkdwn=True,
            )
            logger.info("Slack DM sent successfully. ts=%s", response["ts"])
        except SlackApiError as exc:
            logger.error("Failed to send Slack DM. error=%s", exc.response["error"])
            raise
