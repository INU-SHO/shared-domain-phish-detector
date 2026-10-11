import re
from typing import Optional


MAX_URL_RETRIES = 2
DEFAULT_RETRY_WAIT_SEC = 30.0     # rate-limit fallback when no hint is in the message
RETRY_SAFETY_MARGIN_SEC = 5.0     # added to the SDK's "try again in X" hint
PARSER_RETRY_WAIT_SEC = 2.0       # parser-error retry wait

_RATE_LIMIT_MARKERS = ("rate_limit_exceeded", " 429", "status_code=429")


def is_rate_limit_error(exc: BaseException) -> bool:
    return "RateLimit" in type(exc).__name__ or any(m in str(exc) for m in _RATE_LIMIT_MARKERS)


def is_transient_parser_error(exc: BaseException) -> bool:
    if not isinstance(exc, AttributeError):
        return False
    msg = str(exc)
    if "'NoneType' object has no attribute" not in msg:
        return False
    return ("model_dump" in msg) or ("dict" in msg)


def is_retriable_error(exc: BaseException) -> bool:
    return is_rate_limit_error(exc) or is_transient_parser_error(exc)


def retry_tag(exc: BaseException) -> str:
    if is_rate_limit_error(exc):
        return "rate-limit"
    if is_transient_parser_error(exc):
        return "parser-error"
    return "unknown"


def _parse_retry_after_sec(exc: BaseException) -> Optional[float]:
    msg = str(exc)
    m = re.search(r"try again in\s+([\d.]+)\s*(ms|s)\b", msg)
    if not m:
        return None
    value = float(m.group(1))
    return value / 1000.0 if m.group(2) == "ms" else value


def retry_wait_for(exc: BaseException) -> float:
    if is_rate_limit_error(exc):
        hint = _parse_retry_after_sec(exc)
        return hint + RETRY_SAFETY_MARGIN_SEC if hint is not None else DEFAULT_RETRY_WAIT_SEC
    return PARSER_RETRY_WAIT_SEC
