from unittest.mock import MagicMock, patch

import pytest
from slack_sdk.errors import SlackApiError

from src.slack_service import SlackService


@pytest.fixture
def service():
    with patch.dict("os.environ", {
        "SLACK_BOT_TOKEN": "xoxb-test-token",
        "SLACK_USER_ID": "U0123456789",
    }):
        with patch("src.slack_service.WebClient"):
            svc = SlackService()
            svc._client = MagicMock()
            return svc


def test_send_dm_success(service):
    service._client.chat_postMessage.return_value = {"ts": "12345.67890"}
    service.send_direct_message("Olá, Heitor!")
    service._client.chat_postMessage.assert_called_once_with(
        channel="U0123456789", text="Olá, Heitor!", mrkdwn=True
    )


def test_send_dm_failure(service):
    service._client.chat_postMessage.side_effect = SlackApiError(
        message="Error", response={"error": "not_authed"}
    )
    with pytest.raises(SlackApiError):
        service.send_direct_message("Teste")


def test_missing_user_id_raises():
    with patch.dict("os.environ", {"SLACK_BOT_TOKEN": "xoxb-test", "SLACK_USER_ID": ""}):
        with patch("src.slack_service.WebClient"):
            with pytest.raises(ValueError):
                SlackService()
