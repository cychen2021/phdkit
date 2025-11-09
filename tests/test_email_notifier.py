"""Tests for EmailNotifier with mock SMTP server."""

import time
from unittest.mock import patch, PropertyMock
import pytest
from phdkit.log import EmailNotifier

# pyright: reportAttributeAccessIssue=false


class MockSMTP:
    """Mock SMTP server for testing."""

    def __init__(self, host, timeout=None):
        self.host = host
        self.timeout = timeout
        self.logged_in = False
        self.tls_started = False
        self._closed = False
        self.sent_emails = []

    def starttls(self):
        """Mock starttls."""
        if self._closed:
            raise RuntimeError("Connection closed")
        self.tls_started = True

    def login(self, user, password):
        """Mock login."""
        if self._closed:
            raise RuntimeError("Connection closed")
        self.logged_in = True

    def sendmail(self, sender, recipients, msg):
        """Mock sendmail."""
        if self._closed:
            raise RuntimeError("Connection closed")
        if not self.logged_in:
            raise RuntimeError("Not logged in")
        self.sent_emails.append(
            {"sender": sender, "recipients": recipients, "msg": msg}
        )

    def noop(self):
        """Mock noop command to check connection health."""
        if self._closed:
            return (500, "Connection closed")
        return (250, "OK")

    def quit(self):
        """Mock quit."""
        self._closed = True

    def close(self):
        """Mock close."""
        self._closed = True


def test_basic_email_send():
    """Test basic email sending with mock SMTP."""
    mock_smtp = MockSMTP("smtp.example.com", timeout=30)

    with patch("phdkit.log.notifier.smtplib.SMTP", return_value=mock_smtp):
        notifier = EmailNotifier()

        # Mock the settings
        type(notifier).receiver = PropertyMock(return_value="receiver@example.com")
        type(notifier).smtp = PropertyMock(return_value="smtp.example.com")
        type(notifier).sender = PropertyMock(return_value="sender@example.com")
        type(notifier).password = PropertyMock(return_value="password123")

        # Send first email
        notifier.send("Test Header 1", "Test Body 1")

        assert len(mock_smtp.sent_emails) == 1
        assert mock_smtp.sent_emails[0]["sender"] == "sender@example.com"
        assert mock_smtp.sent_emails[0]["recipients"] == ["receiver@example.com"]
        assert "Test Header 1" in mock_smtp.sent_emails[0]["msg"]

        # Send second email (should reuse connection)
        notifier.send("Test Header 2", "Test Body 2")

        assert len(mock_smtp.sent_emails) == 2
        assert "Test Header 2" in mock_smtp.sent_emails[1]["msg"]


def test_connection_reuse():
    """Test that connection is reused within timeout."""
    create_count = 0

    def create_mock_smtp(host, timeout=None):
        nonlocal create_count
        create_count += 1
        return MockSMTP(host, timeout)

    with patch("phdkit.log.notifier.smtplib.SMTP", side_effect=create_mock_smtp):
        notifier = EmailNotifier()

        type(notifier).receiver = PropertyMock(return_value="receiver@example.com")
        type(notifier).smtp = PropertyMock(return_value="smtp.example.com")
        type(notifier).sender = PropertyMock(return_value="sender@example.com")
        type(notifier).password = PropertyMock(return_value="password123")

        # Send three emails quickly
        notifier.send("Email 1", "Body 1")
        notifier.send("Email 2", "Body 2")
        notifier.send("Email 3", "Body 3")

        # Should only create one connection
        assert create_count == 1


def test_connection_timeout_reconnect():
    """Test that connection is recreated after timeout."""
    create_count = 0

    def create_mock_smtp(host, timeout=None):
        nonlocal create_count
        create_count += 1
        return MockSMTP(host, timeout)

    with patch("phdkit.log.notifier.smtplib.SMTP", side_effect=create_mock_smtp):
        notifier = EmailNotifier()
        notifier._connection_timeout = 2  # 2 second timeout for testing

        type(notifier).receiver = PropertyMock(return_value="receiver@example.com")
        type(notifier).smtp = PropertyMock(return_value="smtp.example.com")
        type(notifier).sender = PropertyMock(return_value="sender@example.com")
        type(notifier).password = PropertyMock(return_value="password123")

        # Send first email
        notifier.send("Email 1", "Body 1")
        assert create_count == 1

        # Wait for timeout
        time.sleep(2.5)

        # Send second email - should reconnect
        notifier.send("Email 2", "Body 2")
        assert create_count == 2


def test_connection_failure_and_retry():
    """Test that failed send is retried once."""
    call_count = 0

    def create_mock_smtp(host, timeout=None):
        nonlocal call_count
        call_count += 1
        mock = MockSMTP(host, timeout)

        # First connection fails on sendmail
        if call_count == 1:

            def failing_sendmail(*args, **kwargs):
                raise RuntimeError("Network error")

            mock.sendmail = failing_sendmail

        return mock

    with patch("phdkit.log.notifier.smtplib.SMTP", side_effect=create_mock_smtp):
        notifier = EmailNotifier()

        type(notifier).receiver = PropertyMock(return_value="receiver@example.com")
        type(notifier).smtp = PropertyMock(return_value="smtp.example.com")
        type(notifier).sender = PropertyMock(return_value="sender@example.com")
        type(notifier).password = PropertyMock(return_value="password123")

        # Should fail first time, then retry and succeed
        notifier.send("Test Email", "Test Body")

        # Should have tried twice
        assert call_count == 2


def test_noop_health_check():
    """Test that noop health check triggers reconnection."""
    create_count = 0

    def create_mock_smtp(host, timeout=None):
        nonlocal create_count
        create_count += 1
        mock = MockSMTP(host, timeout)

        # Make the first connection's noop fail immediately
        if create_count == 1:

            def failing_noop():
                return (500, "Connection lost")

            mock.noop = failing_noop

        return mock

    with patch("phdkit.log.notifier.smtplib.SMTP", side_effect=create_mock_smtp):
        notifier = EmailNotifier()

        type(notifier).receiver = PropertyMock(return_value="receiver@example.com")
        type(notifier).smtp = PropertyMock(return_value="smtp.example.com")
        type(notifier).sender = PropertyMock(return_value="sender@example.com")
        type(notifier).password = PropertyMock(return_value="password123")

        # Send first email
        notifier.send("Email 1", "Body 1")
        assert create_count == 1

        # Send second email - noop will fail, triggering reconnect
        notifier.send("Email 2", "Body 2")
        assert create_count == 2


def test_complete_failure_handling(capsys):
    """Test that complete failure is handled gracefully."""

    def create_failing_smtp(host, timeout=None):
        mock = MockSMTP(host, timeout)

        def failing_sendmail(*args, **kwargs):
            raise RuntimeError("Complete network failure")

        mock.sendmail = failing_sendmail
        return mock

    with patch("phdkit.log.notifier.smtplib.SMTP", side_effect=create_failing_smtp):
        notifier = EmailNotifier()

        type(notifier).receiver = PropertyMock(return_value="receiver@example.com")
        type(notifier).smtp = PropertyMock(return_value="smtp.example.com")
        type(notifier).sender = PropertyMock(return_value="sender@example.com")
        type(notifier).password = PropertyMock(return_value="password123")

        # Should fail but not raise exception
        notifier.send("Test Email", "Test Body")

        # Check stderr output
        captured = capsys.readouterr()
        assert "ERROR: Failed to send email" in captured.err
        assert "after retry" in captured.err


def test_cleanup_on_del():
    """Test that __del__ closes connection."""
    mock_smtp = MockSMTP("smtp.example.com", timeout=30)

    with patch("phdkit.log.notifier.smtplib.SMTP", return_value=mock_smtp):
        notifier = EmailNotifier()

        type(notifier).receiver = PropertyMock(return_value="receiver@example.com")
        type(notifier).smtp = PropertyMock(return_value="smtp.example.com")
        type(notifier).sender = PropertyMock(return_value="sender@example.com")
        type(notifier).password = PropertyMock(return_value="password123")

        notifier.send("Test", "Body")
        assert not mock_smtp._closed

        # Trigger cleanup
        notifier.__del__()
        assert mock_smtp._closed


def test_multihop_scenario():
    """Test simulating multihop start/end scenario with single notifier instance."""
    emails_sent = []

    def create_mock_smtp(host, timeout=None):
        mock = MockSMTP(host, timeout)
        # Track all emails sent
        original_sendmail = mock.sendmail

        def tracking_sendmail(sender, recipients, msg):
            result = original_sendmail(sender, recipients, msg)
            emails_sent.append({"sender": sender, "msg": msg})
            return result

        mock.sendmail = tracking_sendmail
        return mock

    with patch("phdkit.log.notifier.smtplib.SMTP", side_effect=create_mock_smtp):
        notifier = EmailNotifier()

        type(notifier).receiver = PropertyMock(return_value="receiver@example.com")
        type(notifier).smtp = PropertyMock(return_value="smtp.example.com")
        type(notifier).sender = PropertyMock(return_value="sender@example.com")
        type(notifier).password = PropertyMock(return_value="password123")

        # Simulate multihop start
        notifier.send("Multihop start", "Starting analysis")
        assert len(emails_sent) == 1
        assert "Multihop start" in emails_sent[0]["msg"]

        # Simulate some work (would be the actual bisearch process)
        time.sleep(0.1)

        # Simulate multihop end - should reuse same connection
        notifier.send("Multihop end successfully", "Analysis complete")
        assert len(emails_sent) == 2
        assert "Multihop end successfully" in emails_sent[1]["msg"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
