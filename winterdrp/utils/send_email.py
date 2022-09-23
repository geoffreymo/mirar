import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
import ssl
import getpass
import logging
from pathlib import Path
import gzip

import numpy as np

logger = logging.getLogger(__name__)

port = 465  # For SSL

def send_gmail(
        email_recipients: str | list[str],
        email_subject: str,
        email_text: str,
        email_sender: str = os.getenv("WATCHDOG_EMAIL"),
        email_password: str = os.getenv("WATCHDOG_EMAIL_PASSWORD"),
        attachments: str | list[str] = None,
        autocompress: bool = True
):

    # Create a text/plain message
    msg = MIMEMultipart()
    msg.attach(MIMEText(email_text))

    if not isinstance(email_recipients, list):
        email_recipients = [email_recipients]

    # # me == the sender's email address
    # # you == the recipient's email address
    msg['Subject'] = email_subject
    msg['From'] = email_sender
    msg['To'] = ', '.join(email_recipients)

    if attachments is None:
        attachments = []

    if not isinstance(attachments, list):
        attachments = [attachments]

    for file_path in attachments:

        if os.path.exists(file_path):

            base_name = os.path.basename(file_path)

            if not isinstance(file_path, Path):
                file_path = Path(file_path)

            with open(file_path, "rb") as f:

                if np.logical_and(autocompress, file_path.stat().st_size > (1024 * 1024)):
                    data = gzip.compress(f.read())
                    base_name += ".gzip"
                else:
                    data = f.read()

                part = MIMEApplication(
                    data,
                    Name=base_name
                )
            # After the file is closed
            part['Content-Disposition'] = f"attachment; filename={base_name}"
            msg.attach(part)

        else:
            logger.warning(f"Attachment {file_path} not found, skipping.")

    logger.info(f"Sending email to {email_recipients}")

    if email_password is None:
        email_password = getpass.getpass()

    # Create a secure SSL context
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(email_sender, email_password)
        server.send_message(msg)


if __name__ == "__main__":
    from astropy.time import Time

    send_gmail(
        email_sender="winter.data.reduction.pipeline@gmail.com",
        email_recipients="rdstein@caltech.edu",
        email_subject="Tester",
        email_text=f"Test at time: {Time.now()}"
    )
