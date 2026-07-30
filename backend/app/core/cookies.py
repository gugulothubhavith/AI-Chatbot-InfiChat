"""Refresh-token cookie helpers.

The refresh token is the long-lived credential; keeping it in an httpOnly
cookie means client-side JavaScript (and therefore any XSS payload) cannot
read or exfiltrate it, unlike localStorage. The short-lived access token stays
in the response body for the SPA to hold in memory.

These helpers centralise the cookie attributes so every auth endpoint sets and
clears the cookie identically.
"""

from fastapi import Response

from app.core.config import settings


def _cookie_kwargs() -> dict:
    kwargs = {
        "key": settings.REFRESH_COOKIE_NAME,
        "httponly": True,
        "secure": settings.is_production,  # HTTPS-only in prod; relaxed for local http dev
        "samesite": settings.REFRESH_COOKIE_SAMESITE,
        "path": "/",
    }
    if settings.REFRESH_COOKIE_DOMAIN:
        kwargs["domain"] = settings.REFRESH_COOKIE_DOMAIN
    return kwargs


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Attach the refresh token as an httpOnly cookie to the response."""
    response.set_cookie(
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        **_cookie_kwargs(),
    )


def clear_refresh_cookie(response: Response) -> None:
    """Remove the refresh cookie (used on logout).

    delete_cookie must use the same path/domain the cookie was set with, or the
    browser keeps the old one.
    """
    kwargs = _cookie_kwargs()
    response.delete_cookie(
        key=kwargs["key"],
        path=kwargs["path"],
        domain=kwargs.get("domain"),
        samesite=kwargs["samesite"],
    )
