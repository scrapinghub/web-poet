from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetaRefresh:
    """A meta refresh, as :attr:`HtmlMetadata.meta_refresh` reports it."""

    delay: float
    """The delay before the refresh, in seconds."""

    url: str
    """The absolute URL to load."""


@dataclass(frozen=True)
class HtmlMetadata:
    """The HTML metadata of a response, as
    :func:`~web_poet.preextract_selectors` returns it."""

    base_url: str
    """The URL that relative URLs of the response resolve against."""

    meta_refresh: MetaRefresh | None
    """The meta refresh that a web browser would follow, or ``None``."""
