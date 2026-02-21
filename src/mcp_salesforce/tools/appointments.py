"""
MCP tools for interacting with Salesforce Contacts and Appointments (Events).
"""

from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_salesforce.salesforce.client import SalesforceClient
from mcp_salesforce.salesforce.models import (
    AppointmentRequest,
    AppointmentUpdateRequest,
    ContactRequest,
    ContactUpdateRequest,
)

# Single shared client instance
salesforce_client = SalesforceClient()


# ---------------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------------


def salesforce_create_contact(data: ContactRequest) -> dict[str, str]:
    """
    Create a Salesforce Contact

    Args:
        data (ContactRequest): data needed to create the contact in Salesforce API

    Returns:
        dict[str, str]: a JSON of the `contact_id` that was created in the Salesforce API
    """
    contact_id: str = salesforce_client.create_contact(data=data)
    return {"Id": contact_id}


def salesforce_get_contact(contact_id: str) -> dict[str, Any]:
    """
    Fetch a Salesforce Contact by Id

    Args:
        contact_id (str): the contact ID of the row made in Salesforce table

    Returns:
        dict[str, Any]: the response object gotten from Salesforce API
    """
    return salesforce_client.get_contact(contact_id=contact_id)


def salesforce_update_contact(
    contact_id: str, data: ContactUpdateRequest
) -> dict[str, str]:
    """
    Update a Salesforce Contact by Id

    Args:
        contact_id (str): the contact ID of the row within Salesforce table to update
        data (ContactUpdateRequest): the updated data to send to Salesforce to overwrite the row

    Returns:
        dict[str, bool]: dict with status and the `contact_id` that just updated
    """
    salesforce_client.update_contact(contact_id=contact_id, data=data)

    return {
        "status": "success",
        "contact_id": contact_id,
    }


def salesforce_delete_contact(contact_id: str) -> dict[str, str]:
    """
    Delete a Salesforce Contact by Id

    Args:
        contact_id (str): the ID of the contact row that we want to delete from Salesforce `Contacts` table

    Returns:
        dict[str, str]: dict with status and the `contact_id` that just deleted
    """
    salesforce_client.delete_contact(contact_id)
    return {
        "status": "success",
        "contact_id": contact_id,
    }


def salesforce_list_contacts(limit: int = 10) -> dict[str, Any]:
    """
    List recent Salesforce Contacts
    """
    return salesforce_client.list_contacts(limit=limit)


# ---------------------------------------------------------------------------------
# Appointments (Events)
# ---------------------------------------------------------------------------------


def salesforce_create_appointment(data: AppointmentRequest) -> dict[str, Any]:
    """
    Create a Salesforce appointment (Event)
    """
    event_id = salesforce_client.create_appointment(data)
    return {"Id": str(event_id)}


def salesforce_get_appointment(event_id: str) -> dict[str, Any]:
    """
    Fetch a Salesforce appointment (Event) by Id
    """
    return salesforce_client.get_appointment(event_id)


def salesforce_update_appointment(
    event_id: str, data: AppointmentUpdateRequest
) -> dict[str, Any]:
    """
    Update a Salesforce appointment (Event) by Id
    """
    salesforce_client.update_appointment(event_id, data)
    return {"ok": True}


def salesforce_delete_appointment(event_id: str) -> dict[str, Any]:
    """
    Delete a Salesforce appointment (Event) by Id
    """
    salesforce_client.delete_appointment(event_id)
    return {"ok": True}


def salesforce_list_appointments(limit: int = 10) -> dict[str, Any]:
    """
    List recent Salesforce appointments (Events)
    """
    return salesforce_client.list_appointments(limit=limit)


def salesforce_query(soql: str) -> dict[str, Any]:
    """
    Run a SOQL query via Salesforce /query endpoint
    """
    return salesforce_client.query(soql)


# ---------------------------------------------------------------------------------
# Registration Helper
# ---------------------------------------------------------------------------------


def register_salesforce_tools(mcp: FastMCP) -> None:
    """Register Salesforce tools on an MCP server instance."""
    mcp.tool(name="salesforce_create_contact")(salesforce_create_contact)
    mcp.tool(name="salesforce_get_contact")(salesforce_get_contact)
    mcp.tool(name="salesforce_update_contact")(salesforce_update_contact)
    mcp.tool(name="salesforce_delete_contact")(salesforce_delete_contact)
    mcp.tool(name="salesforce_list_contacts")(salesforce_list_contacts)

    mcp.tool(name="salesforce_create_appointment")(salesforce_create_appointment)
    mcp.tool(name="salesforce_get_appointment")(salesforce_get_appointment)
    mcp.tool(name="salesforce_update_appointment")(salesforce_update_appointment)
    mcp.tool(name="salesforce_delete_appointment")(salesforce_delete_appointment)
    mcp.tool(name="salesforce_list_appointments")(salesforce_list_appointments)

    mcp.tool(name="salesforce_query")(salesforce_query)
