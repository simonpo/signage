"""
Base API client with retry logic and connection pooling.
All API clients should inherit from this.
"""

import logging
import time
from typing import Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class APIClient:
    """
    Base class for API clients with robust error handling.
    Provides retry logic and connection pooling.
    """

    def __init__(self, timeout: int = 10, max_retries: int = 3):
        """
        Initialize API client.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a session with retry strategy and connection pooling."""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,  # Exponential backoff: 1s, 2s, 4s
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _make_request(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
    ) -> Optional[requests.Response]:
        """
        Make HTTP request with exponential backoff retry.

        Args:
            url: Request URL
            method: HTTP method (GET, POST, etc.)
            headers: Request headers
            params: Query parameters
            json_data: JSON body data

        Returns:
            Response object or None on failure
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                    timeout=self.timeout,
                )

                response.raise_for_status()
                return response

            except requests.exceptions.HTTPError as e:
                if attempt < self.max_retries:
                    wait_time = 2 ** (attempt - 1)  # Exponential backoff
                    logger.warning(
                        f"HTTP {e.response.status_code} on attempt {attempt}/{self.max_retries}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"HTTP request failed after {self.max_retries} attempts: {e}")
                    return None

            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries:
                    wait_time = 2 ** (attempt - 1)
                    logger.warning(
                        f"Request error on attempt {attempt}/{self.max_retries}: {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts: {e}")
                    return None

        return None

    def close(self) -> None:
        """Close the session and clean up resources."""
        if self.session:
            self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
