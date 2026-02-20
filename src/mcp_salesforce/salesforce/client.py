"""
A client to interact with Salesforce API
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

import httpx

from mcp_salesforce.config import settings


class SalesforceAuthError(RuntimeError):
    """Raised when Salesforce OAuth authentication fails."""


class SalesforceAPIError(RuntimeError):
    """Raised when a Salesforce API request fails."""


# TODO: use a pydantic class here instead
@dataclass(frozen=True)
class SalesforceToken:
    """OAuth token state returned by Salesforce.

    Attributes:
        access_token: Bearer token used for Salesforce API calls.
        instance_url: Base instance URL for the org (e.g., https://xxx.my.salesforce.com).
        issued_at_ms: Token issue time in epoch milliseconds (as returned by Salesforce).
        token_type: Token type (typically "Bearer").
        signature: Salesforce signature (returned by token endpoint; usually not needed).
    """

    access_token: str
    instance_url: str
    issued_at_ms: int
    token_type: str
    signature: str


class SalesforceClient:
    """Salesforce REST client using OAuth refresh-token flow.

    This client:
      - Stores long-lived refresh token from config
      - Mints short-lived access tokens via the OAuth token endpoint
      - Caches the current access token in memory
      - Retries once on INVALID_SESSION_ID by refreshing and re-sending the request

    Typical usage:
        client = SalesforceClient(...)
        contact_id = client.create_contact({...})
        contacts = client.list_contacts(limit=10)
    """

    def __init__(self: Self) -> None:
        """
        Initialize the client.

        Args:
            None

        Returns:
            None
        """
        self._client_id = settings.SALESFORCE_CLIENT_ID
        self._client_secret = settings.SALESFORCE_CLIENT_SECRET
        self._refresh_token = settings.SALESFORCE_REFRESH_TOKEN
        self._instance_url = settings.SALESFORCE_INSTANCE_URL.rstrip("/")
        self._api_version = settings.SALESFORCE_API_VERSION

        self._token_url = "https://login.salesforce.com/services/oauth2/token"
        self._timeout = httpx.Timeout(30)  # 30 seconds

        self._http = httpx.Client(timeout=self._timeout)
        self._token: SalesforceToken | None = None

    def _refresh_access_token(self) -> str:
        """Refresh and cache an access token using the refresh token.

        Returns:
            The new access token.

        Raises:
            SalesforceAuthError: If the token refresh fails.
        """
        data: dict[str, str] = {
            "grant_type": "refresh_token",
            "client_id": settings.SALESFORCE_CLIENT_ID,
            "client_secret": settings.SALESFORCE_CLIENT_SECRET,
            "refresh_token": settings.SALESFORCE_REFRESH_TOKEN,
        }

        response: httpx.Response = self._http.post(self._token_url, data=data)

        if response.status_code >= 400:
            raise SalesforceAuthError(
                f"Token refresh failed ({response.status_code}): {response.text}"
            )

        payload: dict[str, object] = response.json()
        token: str = str(payload["access_token"])

        # Salesforce may return instance_url; prefer it if present.
        instance_url: object | None = payload.get("instance_url")

        if instance_url is not None:
            self._instance_url = str(instance_url).rstrip("/")

        self._access_token = token

        return token

    def get_access_token(self) -> str:
        """Get a valid access token, refreshing if necessary.

        Returns:
            str: The access token suitable for Authorization: Bearer ...

        Raises:
            SalesforceAuthError: If we cannot refresh the token.
        """
        if not self._is_token_valid():
            self._refresh_access_token()
        assert self._token is not None
        return self._token.access_token

    def _api_base(self) -> str:
        """Return the REST API base URL for this org."""
        return f"{self._instance_url}/services/data/{self._api_version}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        retry_on_invalid_session: bool = True,
    ) -> httpx.Response:
        """Make an authenticated Salesforce REST request.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE).
            path: Path starting with "/" relative to /services/data/<version>.
            params: Query params.
            json: JSON body.
            retry_on_invalid_session: If True, refresh and retry once when the token is invalid.

        Returns:
            httpx.Response: The HTTP response.

        Raises:
            SalesforceAPIError: For non-success responses (after retry behavior).
        """
        url = f"{self._api_base()}{path}"
        headers = {
            "Authorization": f"Bearer {self.get_access_token()}",
            "Accept": "application/json",
        }
        if method.upper() in {"POST", "PATCH"}:
            headers["Content-Type"] = "application/json"

        resp = self._http.request(
            method, url, params=params, json=json, headers=headers
        )

        # Common SF invalid-session shape:
        # [{"message":"Session expired or invalid","errorCode":"INVALID_SESSION_ID"}]
        if (
            retry_on_invalid_session
            and resp.status_code == 401
            and "INVALID_SESSION_ID" in resp.text
        ):
            self._refresh_access_token()
            headers["Authorization"] = f"Bearer {self.get_access_token()}"
            resp = self._http.request(
                method, url, params=params, json=json, headers=headers
            )

        return resp

    def _raise_for_status(self, resp: httpx.Response) -> None:
        """Raise a helpful error if the response indicates failure."""
        if 200 <= resp.status_code < 300 or resp.status_code == 204:
            return
        raise SalesforceAPIError(
            f"Salesforce API error ({resp.status_code}): {resp.text}"
        )

    # -------------------------
    # Contacts (sObject: Contact)
    # -------------------------

    def create_contact(self, fields: dict[str, Any]) -> str:
        """Create a Contact.

        Args:
            fields: Contact fields in Salesforce API format (e.g., FirstName, LastName, Email).

        Returns:
            str: The created Contact Id.
        """
        resp = self._request("POST", "/sobjects/Contact", json=fields)
        self._raise_for_status(resp)
        return str(resp.json()["id"])

    def get_contact(self, contact_id: str) -> dict[str, Any]:
        """Fetch a Contact by Id."""
        resp = self._request("GET", f"/sobjects/Contact/{contact_id}")
        self._raise_for_status(resp)
        return dict(resp.json())

    def update_contact(self, contact_id: str, fields: dict[str, Any]) -> None:
        """Update a Contact by Id."""
        resp = self._request("PATCH", f"/sobjects/Contact/{contact_id}", json=fields)
        self._raise_for_status(resp)

    def delete_contact(self, contact_id: str) -> None:
        """Delete a Contact by Id."""
        resp = self._request("DELETE", f"/sobjects/Contact/{contact_id}")
        self._raise_for_status(resp)

    def query(self, soql: str) -> dict[str, Any]:
        """Run a SOQL query via /query.

        Args:
            soql: A SOQL query string.

        Returns:
            Dict[str, Any]: Salesforce query response JSON.
        """
        resp = self._request("GET", "/query", params={"q": soql})
        self._raise_for_status(resp)
        return dict(resp.json())

    def list_contacts(self, limit: int = 10) -> dict[str, Any]:
        """List recent Contacts (simple convenience wrapper)."""
        soql = (
            "SELECT Id, FirstName, LastName, Phone, Email "
            "FROM Contact ORDER BY CreatedDate DESC "
            f"LIMIT {int(limit)}"
        )
        return self.query(soql)

    # -------------------------
    # Appointments (sObject: Event)
    # -------------------------

    def create_appointment(self, fields: dict[str, Any]) -> str:
        """Create an appointment (Event)."""
        resp = self._request("POST", "/sobjects/Event", json=fields)
        self._raise_for_status(resp)
        return str(resp.json()["id"])

    def get_appointment(self, event_id: str) -> dict[str, Any]:
        """Fetch an appointment (Event) by Id."""
        resp = self._request("GET", f"/sobjects/Event/{event_id}")
        self._raise_for_status(resp)
        return dict(resp.json())

    def update_appointment(self, event_id: str, fields: dict[str, Any]) -> None:
        """Update an appointment (Event) by Id."""
        resp = self._request("PATCH", f"/sobjects/Event/{event_id}", json=fields)
        self._raise_for_status(resp)

    def delete_appointment(self, event_id: str) -> None:
        """Delete an appointment (Event) by Id."""
        resp = self._request("DELETE", f"/sobjects/Event/{event_id}")
        self._raise_for_status(resp)

    def list_appointments(self, limit: int = 10) -> dict[str, Any]:
        """List recent appointments (Events)."""
        soql = (
            "SELECT Id, Subject, StartDateTime, EndDateTime, WhoId "
            "FROM Event ORDER BY StartDateTime DESC "
            f"LIMIT {int(limit)}"
        )
        return self.query(soql)
