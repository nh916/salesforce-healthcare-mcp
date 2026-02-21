"""
Request models sent to Salesforce API &
Response models for the response gotten from Salesforce API
"""

from pydantic import BaseModel, Field


class ContactRequest(BaseModel):
    """
    Request body for creating or updating a Salesforce Contact
    """

    FirstName: str
    LastName: str
    Phone: str
    Email: str


class AppointmentRequest(BaseModel):
    """
    Request body for creating or updating a Salesforce Event (appointment)
    """

    Subject: str
    StartDateTime: str = Field(description="ISO-8601 datetime with timezone offset")
    EndDateTime: str = Field(description="ISO-8601 datetime with timezone offset")
    WhoId: str = Field(description="Contact ID to link the event to")
