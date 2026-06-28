import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Meeting Guardian</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f4f6f9; margin: 0; padding: 20px; color: #333; }}
    .container {{ max-width: 600px; margin: 0 auto; background: #fff;
                  border-radius: 12px; overflow: hidden;
                  box-shadow: 0 2px 12px rgba(0,0,0,.08); }}
    .header {{ background: linear-gradient(135deg, #1a73e8, #0d47a1);
               padding: 28px 32px; color: #fff; }}
    .header h1 {{ margin: 0; font-size: 22px; font-weight: 600; }}
    .header p  {{ margin: 4px 0 0; opacity: .85; font-size: 14px; }}
    .body  {{ padding: 28px 32px; line-height: 1.7; white-space: pre-wrap; }}
    .footer {{ background: #f4f6f9; padding: 16px 32px;
               font-size: 12px; color: #888; text-align: center; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🛡️ Meeting Guardian</h1>
      <p>{subtitle}</p>
    </div>
    <div class="body">{body}</div>
    <div class="footer">
      Enviado automaticamente pelo Meeting Guardian &bull; {date}
    </div>
  </div>
</body>
</html>
"""


class EmailService:
    def __init__(self) -> None:
        self._smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self._smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self._smtp_user = os.getenv("SMTP_USER")
        self._smtp_password = os.getenv("SMTP_PASSWORD")
        self._recipient = os.getenv("EMAIL_RECIPIENT")

        if not all([self._smtp_user, self._smtp_password, self._recipient]):
            raise ValueError("SMTP_USER, SMTP_PASSWORD and EMAIL_RECIPIENT must be set.")

    def send(self, subject: str, plain_body: str, subtitle: str = "") -> None:
        from datetime import datetime

        html_body = HTML_TEMPLATE.format(
            subtitle=subtitle or subject,
            body=plain_body.replace("\n", "<br>"),
            date=datetime.now().strftime("%d/%m/%Y %H:%M"),
        )

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self._smtp_user
        msg["To"] = self._recipient
        msg.attach(MIMEText(plain_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            with smtplib.SMTP(self._smtp_host, self._smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(self._smtp_user, self._smtp_password)
                server.sendmail(self._smtp_user, self._recipient, msg.as_string())
            logger.info("Email sent to %s", self._recipient)
        except smtplib.SMTPException as exc:
            logger.error("Failed to send email: %s", exc)
            raise
