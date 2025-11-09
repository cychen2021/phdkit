# EmailNotifier Test Suite

## Overview

This test suite validates the `EmailNotifier` class's persistent SMTP connection management, error handling, and reconnection logic.

## Running Tests

```bash
cd /workspaces/hdf5analysis/phdkit
uv run pytest tests/test_email_notifier.py -v
```

## Test Cases

### 1. `test_basic_email_send`
Tests basic email sending functionality with connection reuse across multiple sends.

**Validates:**
- SMTP connection creation
- Email formatting and sending
- Connection reuse within same notifier instance

### 2. `test_connection_reuse`
Verifies that a single SMTP connection is reused for multiple emails sent within the timeout period.

**Validates:**
- Only one SMTP connection created for multiple sends
- Connection pooling works correctly

### 3. `test_connection_timeout_reconnect`
Tests that connections are automatically recreated after the 5-minute timeout.

**Validates:**
- Connection age tracking
- Automatic reconnection after timeout
- New connection establishes successfully

### 4. `test_connection_failure_and_retry`
Simulates network failures and validates retry logic.

**Validates:**
- Failed sends trigger reconnection
- One retry attempt is made
- Retry succeeds with new connection

### 5. `test_noop_health_check`
Tests the SMTP NOOP command health check that detects dead connections.

**Validates:**
- NOOP command called before reusing connection
- Failed NOOP triggers reconnection
- New connection created successfully

### 6. `test_complete_failure_handling`
Tests graceful handling when all retry attempts fail.

**Validates:**
- Exceptions don't crash the program
- Errors are logged to stderr
- System continues after failures

### 7. `test_cleanup_on_del`
Tests that SMTP connections are properly closed on object destruction.

**Validates:**
- `__del__` method closes connections
- No resource leaks

### 8. `test_multihop_scenario`
Simulates the actual multihop bisearch scenario with start/end emails.

**Validates:**
- Both "Multihop start" and "Multihop end" emails send successfully
- Connection is reused between start and end
- Realistic usage pattern works

## Debugging Email Issues

### Enable Debug Output

Set the `PHDKIT_EMAIL_DEBUG` environment variable:

```bash
export PHDKIT_EMAIL_DEBUG=1
uv run hdf tnt bisearch ...
```

This will print to stdout whenever an email is sent successfully.

### Check SMTP Connection

If emails aren't being sent, check:

1. **Configuration is loaded**: Ensure `hdf.config.toml` and `hdf.env.toml` have correct SMTP settings
2. **Network connectivity**: Try manually connecting to the SMTP server
3. **Authentication**: Verify email credentials are correct
4. **Firewall/ports**: Ensure port 587 (or your SMTP port) is open

### Common Issues

**Issue: "Multihop start" sends but "Multihop end" doesn't**

This was the original bug - SMTP connection died between sends without proper health checks. Now fixed with:
- 5-minute connection timeout tracking
- NOOP health checks before each send
- Automatic reconnection on failure

**Issue: "ERROR: Failed to send email" in stderr**

Check the error message details:
- `Network error`: Network connectivity issue
- `Authentication failed`: Wrong credentials
- `Connection timeout`: SMTP server unreachable or slow
- `Connection closed`: Server dropped the connection

**Issue: No emails and no errors**

The logger might not have the email output attached. Check that:
```python
logger.add_output(LogOutput.email(notifier, level=LogLevel.CRITICAL))
```
is called before logging critical messages.

## Mock SMTP Server

The tests use a `MockSMTP` class that simulates:
- Connection creation and authentication
- Email sending
- NOOP health checks
- Connection failures
- Timeouts

This allows testing without real SMTP credentials or network access.

## Implementation Details

### Connection State Management

The `EmailNotifier` maintains:
- `_smtp_connection`: Current SMTP connection (or None)
- `_last_send_time`: Timestamp of last successful send
- `_connection_timeout`: 300 seconds (5 minutes)

### Health Check Flow

Before each send:
1. Check if connection exists
2. Check if connection age < 5 minutes
3. Send NOOP command to verify connection is alive
4. If any check fails, close old connection and create new one
5. Attempt to send email
6. On failure, close connection and retry once

### Error Handling

All SMTP exceptions are caught and:
1. Logged to stderr immediately
2. Connection is closed
3. One reconnection attempt is made
4. If retry fails, error is logged again and operation continues

This ensures email failures don't crash the bisearch process.
