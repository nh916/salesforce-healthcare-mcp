"""
A client to interact with Salesforce API
"""

from __future__ import annotations

from typing import Any, Self

import httpx

from mcp_salesforce.config import settings
from mcp_salesforce.salesforce.models import (
    AppointmentRequest,
    AppointmentUpdateRequest,
    ContactRequest,
    ContactUpdateRequest,
)


# TODO: do I even need this?
class SalesforceAuthError(RuntimeError):
    """
    Raised when Salesforce OAuth authentication fails
    """


class SalesforceClient:
    """
    Salesforce REST client using OAuth refresh-token flow.

    This client:
      - Stores long-lived refresh token from config
      - Mints short-lived access tokens via the OAuth token endpoint
      - Caches the current access token in memory
      - Retries once on INVALID_SESSION_ID by refreshing and re-sending the request
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
        self._api_base_url = f"{self._instance_url}/services/data/{self._api_version}"

        self._token_url = "https://login.salesforce.com/services/oauth2/token"
        self._timeout = httpx.Timeout(30)  # 30 seconds

        self._httpx_client = httpx.Client(timeout=self._timeout)
        self._access_token = ""

    def _refresh_access_token(self) -> str:
        """
        Refresh and cache an access token using the refresh token.

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

        response: httpx.Response = self._httpx_client.post(self._token_url, data=data)

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

        # ALWAYS recompute after possible change
        self._api_base_url = f"{self._instance_url}/services/data/{self._api_version}"

        self._access_token = token

        return token

    def _make_request(
        self: Self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        retry_on_invalid_session: bool = True,
    ) -> httpx.Response:
        """
        Make an authenticated Salesforce REST request.

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

        path = path.lstrip(
            "/"
        )  # remove the leading slash from the path to not have "//sobjects/Contact/{contact_id}"

        url: str = f"{self._api_base_url}/{path}"

        if not self._access_token:
            token = self._refresh_access_token()
        else:
            token = self._access_token

        headers: dict[str, str] = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        if method.upper() in {"POST", "PATCH"}:
            headers["Content-Type"] = "application/json"

        response: httpx.Response = self._httpx_client.request(
            method=method, url=url, params=params, json=json, headers=headers
        )

        # Common SF invalid-session shape:
        # [{"message":"Session expired or invalid","errorCode":"INVALID_SESSION_ID"}]
        if (
            retry_on_invalid_session
            and response.status_code == 401
            and "INVALID_SESSION_ID" in response.text
        ):
            token = self._refresh_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            }
            response = self._httpx_client.request(
                method=method, url=url, params=params, json=json, headers=headers
            )

        response.raise_for_status()

        return response

    # ----------------------------------------------------------------------------------------------------------
    # Contacts (sObject: Contact)
    # ----------------------------------------------------------------------------------------------------------

    def create_contact(self: Self, data: ContactRequest) -> str:
        """
        Create a Contact.

        Args:
            data (ContactRequest): Contact fields as a validated request model.

        Returns:
            str: The created Contact Id from Salesforce

        Raises:
            KeyError: in case the key is not in the dict and the JSON response comes back from the server different than expected
        """
        response: httpx.Response = self._make_request(
            method="POST", path="/sobjects/Contact", json=data.model_dump(mode="json")
        )
        response.raise_for_status()
        return str(response.json()["id"])

    # TODO: return a pydantic model instead
    def get_contact(self: Self, contact_id: str) -> dict[str, Any]:
        """
        Fetch a Contact by Id

        Args:
            contact_id (str): contact_id within salesforce to find the contact

        Returns:
            dict[str, Any]: returns the response JSON from Salesforce
        """
        response: httpx.Response = self._make_request(
            method="GET", path=f"/sobjects/Contact/{contact_id}"
        )

        response.raise_for_status()
        return response.json()

    def update_contact(self: Self, contact_id: str, data: ContactUpdateRequest) -> None:
        """
        Update a Contact by Id.

        Args:
            contact_id: The contact ID from Salesforce to update.
            data (ContactUpdateRequest): Fields to update (only set fields are sent).

        Returns:
            None
        """
        response: httpx.Response = self._make_request(
            method="PATCH",
            path=f"/sobjects/Contact/{contact_id}",
            json=data.model_dump(mode="json", exclude_none=True),
        )
        response.raise_for_status()

    def delete_contact(self: Self, contact_id: str) -> None:
        """
        Delete a Contact by Id

        Args:
            contact_id (str): the contact ID from Salesforce that we want to update

        Returns:
            None
        """
        response: httpx.Response = self._make_request(
            method="DELETE", path=f"/sobjects/Contact/{contact_id}"
        )
        response.raise_for_status()

    def query(self: Self, soql: str) -> dict[str, Any]:
        """
        Run a SOQL query via /query.
        Helper method for the methods that need to list the contents of a table

        Args:
            soql: A SOQL query string.

        Returns:
            Dict[str, Any]: Salesforce query response JSON.
        """
        response: httpx.Response = self._make_request(
            method="GET", path="/query", params={"q": soql}
        )
        response.raise_for_status()
        return dict(response.json())

    def list_contacts(self: Self, limit: int = 10) -> dict[str, Any]:
        """
        List recent Contacts (simple convenience wrapper)

        Returns:
            dict[str, Any]: the response from Salesforce
        """

        soql: str = (
            "SELECT Id, FirstName, LastName, Phone, Email "
            "FROM Contact ORDER BY CreatedDate DESC "
            f"LIMIT {int(limit)}"
        )
        return self.query(soql)

    # ---------------------------------------------------------------------------------
    # Appointments (sObject: Event)
    # ---------------------------------------------------------------------------------

    def create_appointment(self: Self, data: AppointmentRequest) -> str:
        """
        Create an appointment (Event).

        Args:
            data (AppointmentRequest): Event fields as a validated request model.

        Returns:
            The created appointment ID.
        """
        response: httpx.Response = self._make_request(
            method="POST", path="/sobjects/Event", json=data.model_dump(mode="json")
        )
        response.raise_for_status()
        return response.json()["id"]

    def get_appointment(self: Self, event_id: str) -> dict[str, Any]:
        """
        Fetch an appointment (Event) by Id

        Notes:
            We are using the built in table of `Events` from Salesforce

        Args:
            event_id (str): the ID of the appointment that we want

        Returns:
            dict[str, Any]: the response from Salesforce
        """
        response: httpx.Response = self._make_request(
            method="GET", path=f"/sobjects/Event/{event_id}"
        )
        response.raise_for_status()
        return dict(response.json())

    def update_appointment(
        self: Self, event_id: str, data: AppointmentUpdateRequest
    ) -> None:
        """
        Update an appointment (Event) by Id.

        Args:
            event_id (str): The ID of the appointment to update.
            data (AppointmentUpdateRequest): Fields to update (only set fields are sent).

        Returns:
            None
        """
        response: httpx.Response = self._make_request(
            method="PATCH",
            path=f"/sobjects/Event/{event_id}",
            json=data.model_dump(mode="json", exclude_none=True),
        )
        response.raise_for_status()

    def delete_appointment(self: Self, event_id: str) -> None:
        """
        Delete an appointment (Event) by Id

        Args:
            event_id (str): the ID of the appointment that we want to delete

        Returns:
            None
        """

        response: httpx.Response = self._make_request(
            method="DELETE", path=f"/sobjects/Event/{event_id}"
        )
        response.raise_for_status()

    def list_appointments(self: Self, limit: int = 10) -> dict[str, Any]:
        """
        List recent appointments (Events)

        Args:
            limit (int): the number of appointments that we want to return

        Returns:
            dict[str, Any]: the response from Salesforce
        """

        soql: str = (
            "SELECT Id, Subject, StartDateTime, EndDateTime, WhoId "
            "FROM Event ORDER BY StartDateTime DESC "
            f"LIMIT {int(limit)}"
        )

        return self.query(soql)
