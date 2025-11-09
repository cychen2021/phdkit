#!/usr/bin/env python3
"""Manual test script for EmailNotifier with real SMTP server.

Usage:
    export EMAIL_SMTP="smtp.gmail.com:587"
    export EMAIL_SENDER="your-email@gmail.com"
    export EMAIL_RECEIVER="your-email@gmail.com"
    export EMAIL_PASSWORD="your-app-password"
    export PHDKIT_EMAIL_DEBUG=1

    uv run python tests/manual_email_test.py
"""

import sys
import time
from pathlib import Path

# Add phdkit to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from phdkit.log import EmailNotifier
from phdkit.configlib import config


def test_basic_send():
    """Test basic email sending."""
    print("Test 1: Basic email send")
    notifier = EmailNotifier()
    config[notifier].load(None, None)  # Load from environment

    try:
        notifier.send("Test Email 1", "This is a test email from EmailNotifier.")
        print("✓ Test 1 passed: Email sent successfully")
        return True
    except Exception as e:
        print(f"✗ Test 1 failed: {e!r}")
        return False


def test_connection_reuse():
    """Test connection reuse across multiple sends."""
    print("\nTest 2: Connection reuse (multiple sends)")
    notifier = EmailNotifier()
    config[notifier].load(None, None)

    try:
        notifier.send("Test Email 2a", "First email in sequence")
        print("  Sent email 1")

        time.sleep(1)

        notifier.send("Test Email 2b", "Second email in sequence")
        print("  Sent email 2")

        time.sleep(1)

        notifier.send("Test Email 2c", "Third email in sequence")
        print("  Sent email 3")

        print("✓ Test 2 passed: All emails sent successfully")
        return True
    except Exception as e:
        print(f"✗ Test 2 failed: {e!r}")
        return False


def test_timeout_reconnect():
    """Test connection timeout and reconnection."""
    print("\nTest 3: Connection timeout and reconnection")
    notifier = EmailNotifier()
    notifier._connection_timeout = 3  # Override to 3 seconds for testing
    config[notifier].load(None, None)

    try:
        notifier.send("Test Email 3a", "First email before timeout")
        print("  Sent email 1")

        print("  Waiting 4 seconds for timeout...")
        time.sleep(4)

        notifier.send("Test Email 3b", "Second email after timeout")
        print("  Sent email 2 (should have reconnected)")

        print("✓ Test 3 passed: Reconnection after timeout successful")
        return True
    except Exception as e:
        print(f"✗ Test 3 failed: {e!r}")
        return False


def test_multihop_simulation():
    """Simulate the multihop start/end scenario."""
    print("\nTest 4: Multihop start/end simulation")
    notifier = EmailNotifier()
    config[notifier].load(None, None)

    try:
        # Simulate multihop start
        notifier.send("Multihop start", "Starting analysis at test location")
        print("  Sent 'Multihop start' email")

        # Simulate some work
        print("  Simulating analysis work...")
        time.sleep(2)

        # Simulate multihop end
        notifier.send("Multihop end successfully", "Analysis completed successfully")
        print("  Sent 'Multihop end' email")

        print("✓ Test 4 passed: Multihop simulation successful")
        return True
    except Exception as e:
        print(f"✗ Test 4 failed: {e!r}")
        return False


def main():
    print("=" * 60)
    print("EmailNotifier Manual Test Suite")
    print("=" * 60)
    print()

    # Check environment variables
    import os

    required_vars = ["EMAIL_SMTP", "EMAIL_SENDER", "EMAIL_RECEIVER", "EMAIL_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]

    if missing_vars:
        print("ERROR: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print()
        print("Please set all required variables before running tests.")
        print("See docstring at top of this file for example.")
        return 1

    print(f"SMTP Server: {os.environ['EMAIL_SMTP']}")
    print(f"From: {os.environ['EMAIL_SENDER']}")
    print(f"To: {os.environ['EMAIL_RECEIVER']}")
    print()

    # Run tests
    results = []
    results.append(test_basic_send())
    results.append(test_connection_reuse())
    results.append(test_timeout_reconnect())
    results.append(test_multihop_simulation())

    # Summary
    print()
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
