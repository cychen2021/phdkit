from datetime import datetime
import tomllib
import os
import smtplib
import sys
import time
from email.mime.text import MIMEText
from ..configlib import setting, configurable


def __read_email_config(config_file: str | None) -> dict:
    if config_file is None:
        config = {"email": {}}
        if "EMAIL_RECEIVER" in os.environ:
            config["email"]["email_receiver"] = os.environ["EMAIL_RECEIVER"]
        else:
            config["email"]["email_receiver"] = None

        if "EMAIL_SMTP" in os.environ:
            config["email"]["email_smtp"] = os.environ["EMAIL_SMTP"]
        else:
            config["email"]["email_smtp"] = None

        if "EMAIL_SENDER" in os.environ:
            config["email"]["email_sender"] = os.environ["EMAIL_SENDER"]
        else:
            config["email"]["email_sender"] = None
    else:
        with open(config_file, "rb") as f:
            config = tomllib.load(f)
        # assert set(config.keys()).issubset(
        #     {"email_receiver", "email_smtp", "email_sender"}
        # ), f"Unexpected keys found: {set(config.keys()) - {'email_receiver', 'email_smtp', 'email_sender'}}"
        if "email" not in config:
            config["email"] = {}
        if "email_receiver" not in config["email"]:
            config["email"]["email_receiver"] = None
        if "email_smtp" not in config["email"]:
            config["email"]["email_smtp"] = None
        if "email_sender" not in config["email"]:
            config["email"]["email_sender"] = None
    return config


def __read_email_env_config(config_file: str | None) -> dict:
    if config_file is None:
        config = {"email": {}}
        if "EMAIL_PASSWORD" in os.environ:
            config["email"]["email_password"] = os.environ["EMAIL_PASSWORD"]
        else:
            config["email"]["email_password"] = None
    else:
        with open(config_file, "rb") as f:
            config = tomllib.load(f)
        # assert set(config.keys()).issubset({"email_password"}), f"Unexpected keys found: {set(config.keys()) - {'email_password'}}"
        if "email" not in config:
            config["email"] = {}
        if "email_password" not in config["email"]:
            config["email"]["email_password"] = None
    return config


@configurable(
    config_key="email",
    load_config=__read_email_config,
    load_env=__read_email_env_config,
)
class EmailNotifier:
    """An email notifier.

    Settings:
        reciever (str | None): The email address to send notifications to.
        smtp (str | None): The SMTP server to use for sending emails.
        sender (str | None): The email address to send notifications from.
        password (str | None): The password for the sender's email account.
    Methods:
        send(header: str, body: str): Sends an email with the given header and body.
        close(): Closes the SMTP connection.
    """

    def __init__(self):
        self._smtp_connection: smtplib.SMTP | None = None
        self._last_send_time: float = 0
        self._connection_timeout: float = 300  # 5 minutes
        if os.environ.get("PHDKIT_EMAIL_DEBUG", "0").lower() in [
            "1",
            "true",
            "yes",
            "on",
        ]:
            # We use a debug file as the output of exceptions insider a logger
            #  is often swallowed.
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self._debug_file = open(f"x_phdkit_email_debug_{timestamp}.log", "a")
        else:
            self._debug_file = None

    @setting("email_receiver")
    def receiver(self) -> str | None: ...

    @setting("email_smtp")
    def smtp(self) -> str | None: ...

    @setting("email_sender")
    def sender(self) -> str | None: ...

    @setting("email_password")
    def password(self) -> str | None: ...

    def _ensure_connected(self):
        """Ensure SMTP connection is established and fresh."""
        current_time = time.time()
        connection_age = current_time - self._last_send_time

        # Check if we need to reconnect
        needs_reconnect = False

        if self._smtp_connection is None:
            needs_reconnect = True
        elif connection_age > self._connection_timeout:
            needs_reconnect = True
        else:
            # Health check: try noop to see if connection is alive
            try:
                status, _ = self._smtp_connection.noop()
                if status != 250:
                    needs_reconnect = True
            except Exception:
                needs_reconnect = True

        if needs_reconnect:
            # Close old connection if exists
            if self._smtp_connection is not None:
                try:
                    self._smtp_connection.quit()
                except Exception:
                    pass  # Ignore errors during cleanup
                self._smtp_connection = None

            # Create new connection with 30 second timeout
            assert self.smtp is not None
            assert self.sender is not None
            assert self.password is not None
            self._smtp_connection = smtplib.SMTP(self.smtp, timeout=30)
            self._smtp_connection.starttls()
            self._smtp_connection.login(self.sender, self.password)
            self._last_send_time = current_time

    def close(self):
        """Close the SMTP connection."""
        if self._smtp_connection is not None:
            try:
                self._smtp_connection.quit()
            except Exception:
                pass  # Ignore errors during cleanup
            self._smtp_connection = None

    def __del__(self):
        """Cleanup SMTP connection on object destruction."""
        self.close()

    def send(self, header: str, body: str):
        """Send an email with the given header and body."""

        if (
            self.receiver is None
            or self.smtp is None
            or self.sender is None
            or self.password is None
        ):
            raise ValueError("Email configuration is not set.")

        msg = MIMEText(body)
        msg["Subject"] = header
        msg["From"] = self.sender
        msg["To"] = self.receiver

        try:
            # Ensure connection is alive
            self._ensure_connected()

            assert self._smtp_connection is not None
            # Send the email
            self._smtp_connection.sendmail(
                self.sender, [self.receiver], msg.as_string()
            )
            self._last_send_time = time.time()

            if os.environ.get("PHDKIT_EMAIL_DEBUG", "0").lower() in [
                "1",
                "true",
                "yes",
                "on",
            ]:
                print(
                    f"Email sent: from {self.sender} to {self.receiver} through {self.smtp} at {datetime.now()}",
                    file=self._debug_file,
                    flush=True,
                )

        except Exception as e:
            # Print error to stderr
            print(
                f"ERROR: Failed to send email '{header}': {e!r}",
                file=self._debug_file or sys.stderr,
                flush=True,
            )

            # Close broken connection and try once more
            self.close()

            try:
                self._ensure_connected()
                assert self._smtp_connection is not None
                self._smtp_connection.sendmail(
                    self.sender, [self.receiver], msg.as_string()
                )
                self._last_send_time = time.time()

                if os.environ.get("PHDKIT_EMAIL_DEBUG", "0").lower() in [
                    "1",
                    "true",
                    "yes",
                    "on",
                ]:
                    print(
                        f"Email sent (retry): from {self.sender} to {self.receiver} through {self.smtp} at {datetime.now()}",
                        file=self._debug_file,
                        flush=True,
                    )
            except Exception as retry_error:
                # Final failure - print and give up
                print(
                    f"ERROR: Failed to send email '{header}' after retry: {retry_error!r}",
                    file=self._debug_file or sys.stderr,
                    flush=True,
                )
