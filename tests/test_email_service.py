import smtplib
from unittest.mock import MagicMock, patch

import pytest

from src.email_service import EmailService


@pytest.fixture
def service():
    with patch.dict("os.environ", {
        "SMTP_USER": "test@gmail.com",
        "SMTP_PASSWORD": "senha-app",
        "EMAIL_RECIPIENT": "destino@email.com",
        "SMTP_HOST": "smtp.gmail.com",
        "SMTP_PORT": "587",
    }):
        return EmailService()


def test_send_email_success(service):
    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        service.send(subject="Teste", plain_body="Corpo do e-mail", subtitle="Sub")
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@gmail.com", "senha-app")
        mock_server.sendmail.assert_called_once()


def test_send_email_failure(service):
    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.return_value.__enter__.side_effect = smtplib.SMTPException("Erro")
        with pytest.raises(smtplib.SMTPException):
            service.send(subject="Erro", plain_body="Falha")


def test_missing_env_raises():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError):
            EmailService()
