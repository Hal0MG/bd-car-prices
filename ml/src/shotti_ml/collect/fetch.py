"""A deliberately slow, self-identifying HTTP client for fetching public pages.

It exists to make the polite behaviour a property of the code rather than a promise:

- it reads robots.txt first and refuses any path the site disallows;
- it waits at least `delay` seconds (plus a little jitter) between requests;
- it backs off on 429 and 5xx errors, honouring Retry-After;
- it stops the whole run after several failures in a row, instead of hammering a site that is struggling.
"""

from __future__ import annotations

import random
import time
import urllib.error
import urllib.request
import urllib.robotparser
from typing import Callable
from urllib.parse import urlsplit

USER_AGENT = "shotti-ml/0.1 (+https://github.com/Hal0MG/bd-car-prices; price-transparency research)"
_RETRYABLE = {429, 500, 502, 503, 504}


class FetchError(Exception):
    """One page could not be fetched; the run can carry on."""


class Disallowed(FetchError):
    """robots.txt does not allow this path."""


class Halt(Exception):
    """Too many failures in a row. The run should stop."""


class PoliteFetcher:
    def __init__(
        self,
        *,
        delay: float = 3.0,
        jitter: float = 1.0,
        timeout: float = 30.0,
        max_retries: int = 2,
        max_consecutive_failures: int = 3,
        user_agent: str = USER_AGENT,
        opener: Callable = urllib.request.urlopen,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
        rng: random.Random | None = None,
    ) -> None:
        self.delay = delay
        self.jitter = jitter
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_consecutive_failures = max_consecutive_failures
        self.user_agent = user_agent
        self._open = opener
        self._sleep = sleep
        self._clock = clock
        self._rng = rng or random.Random()
        self._next_ok = 0.0
        self._robots: dict[str, urllib.robotparser.RobotFileParser] = {}
        self.consecutive_failures = 0
        self.requests = 0

    # -- pacing ---------------------------------------------------------

    def _pause(self) -> None:
        wait = self._next_ok - self._clock()
        if wait > 0:
            self._sleep(wait)

    def _schedule_next(self) -> None:
        self._next_ok = self._clock() + self.delay + self._rng.uniform(0, self.jitter)

    # -- one request ----------------------------------------------------

    def _request(self, url: str) -> str:
        self._pause()
        self.requests += 1
        request = urllib.request.Request(url, headers={"User-Agent": self.user_agent, "Accept": "text/html,text/plain"})
        try:
            with self._open(request, timeout=self.timeout) as response:
                return response.read().decode("utf-8", "replace")
        finally:
            self._schedule_next()

    # -- robots.txt -----------------------------------------------------

    def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self._robots:
            parser = urllib.robotparser.RobotFileParser()
            try:
                parser.parse(self._request(origin + "/robots.txt").splitlines())
            except urllib.error.HTTPError as error:
                # RFC 9309: a missing robots.txt (4xx) means anything goes; a server error means stay away.
                if 400 <= error.code < 500:
                    parser.parse([])
                else:
                    parser.disallow_all = True
            except (urllib.error.URLError, TimeoutError):
                parser.disallow_all = True
            self._robots[origin] = parser
        return self._robots[origin].can_fetch(self.user_agent, url)

    # -- fetching with retries ------------------------------------------

    def get(self, url: str) -> str:
        if not self.allowed(url):
            raise Disallowed(f"robots.txt disallows {url}")

        failure: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                text = self._request(url)
                self.consecutive_failures = 0
                return text
            except urllib.error.HTTPError as error:
                failure = error
                if error.code in _RETRYABLE and attempt < self.max_retries:
                    self._sleep(min(_retry_after(error) or self.delay * 2 ** (attempt + 1), 60))
                    continue
                break
            except (urllib.error.URLError, TimeoutError) as error:
                failure = error
                if attempt < self.max_retries:
                    self._sleep(self.delay * 2 ** (attempt + 1))
                    continue
                break

        self.consecutive_failures += 1
        if self.consecutive_failures >= self.max_consecutive_failures:
            raise Halt(f"{self.consecutive_failures} failures in a row; last: {failure}")
        raise FetchError(f"{url}: {failure}")


def _retry_after(error: urllib.error.HTTPError) -> float | None:
    value = error.headers.get("Retry-After") if error.headers else None
    try:
        return float(value) if value else None
    except ValueError:
        return None
