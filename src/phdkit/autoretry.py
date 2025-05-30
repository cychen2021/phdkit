"""AutoRetry class for retrying function calls with additive-increase/multiplicative-decrease."""

from typing import Callable, Any
import time
from .log import Logger

__all__ = ["AutoRetry", "AutoRetryError"]


class AutoRetryError(Exception):
    """Custom exception for LLMBridge errors."""

    def __init__(self, message: str, exceptions: list[Exception] = []):
        super().__init__(message)
        self.message = message
        self.exceptions = exceptions

    def __str__(self) -> str:
        return f"AutoRetryError: {self.message}"

    def __repr__(self) -> str:
        return f"AutoRetryError({self.message!r}, {self.exceptions!r})"


class AutoRetry:
    """A class to automatically retry a function call with exponential backoff.

    This class wraps a function and retries it on failure, with an increasing delay
    between attempts. The delay is multiplied by an increment factor after each failure,
    and decreased by a fixed amount after a successful attempt.
    The retry logic is useful for handling transient errors in API calls or other operations
    that may fail intermittently.
    """

    def __init__(
        self,
        func: Callable[..., Any],
        logger: Logger | None = None,
        *,
        max_retrys: int = 5,
        increment_factor: float = 2,
        decrement_num: int = 10,
    ):
        """Initialize the AutoRetry instance.
        Args:
            func: The function to wrap with retry logic.
            logger: Optional logger for debug messages.
            max_retrys: Maximum number of retry attempts.
            increment_factor: Factor by which the retry delay is multiplied after each failure.
            decrement_num: Amount by which the retry delay is decreased after a successful attempt.
        """

        self.llm_api_call = func
        self.max_retrys = max_retrys
        self.__init_retry_delay = 10.0
        self.retry_delay = self.__init_retry_delay
        self.increment_factor = increment_factor
        self.decrement_num = decrement_num
        self.logger = logger

    def reset(self):
        """Reset the delay to initial values."""

        self.retry_delay = self.__init_retry_delay

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.call(*args, **kwds)

    def call(self, *args, **kwargs) -> Any:
        """Call the wrapped function with retry logic."""

        exceptions = []
        retry_count = 0
        while retry_count < self.max_retrys:
            try:
                r = self.llm_api_call(*args, **kwargs)
                self.retry_delay -= max(self.__init_retry_delay, self.decrement_num)
                if self.logger is not None:
                    self.logger.debug(
                        f"AutoRetry: {self.llm_api_call.__name__} succeeded",
                        f"{args=}, {kwargs=}, result={repr(r)}\n{retry_count=}, {self.retry_delay=}",
                    )
                return r
            except Exception as e:
                exceptions.append(e)
                retry_count += 1
                if self.logger is not None:
                    self.logger.debug(
                        f"AutoRetry: {self.llm_api_call.__name__} failed",
                        f"{args=}, {kwargs=}\n{repr(e)}\n{retry_count=}, {self.retry_delay=}",
                    )
                if retry_count >= self.max_retrys:
                    if self.logger is not None:
                        self.logger.error(
                            f"AutoRetry: {self.llm_api_call.__name__} failed",
                            f"{args=}, {kwargs=}\n{exceptions=}\n{self.max_retrys=}, {self.retry_delay=}",
                        )
                    raise AutoRetryError(
                        f"AutoRetry failed after {self.max_retrys} attempts.",
                        exceptions=exceptions,
                    )
                self.retry_delay *= self.increment_factor
                time.sleep(self.retry_delay)
