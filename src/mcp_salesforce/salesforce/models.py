"""
Request models sent to Salesforce API &
Response models for the response gotten from Salesforce API
"""

from typing import Optional

from pydantic import BaseModel, Field


class ContactRequest(BaseModel):
    """
    Request body for creating a Salesforce Contact.
    """

    FirstName: str
    LastName: str
    Phone: str
    Email: str


class ContactUpdateRequest(BaseModel):
    """
    Request body for updating a Salesforce Contact (partial; only set fields are sent).
    """

    FirstName: Optional[str] = None
    LastName: Optional[str] = None
    Phone: Optional[str] = None
    Email: Optional[str] = None


class AppointmentRequest(BaseModel):
    """
    Request body for creating a Salesforce Event (appointment).
    """

    Subject: str
    StartDateTime: str = Field(description="ISO-8601 datetime with timezone offset")
    EndDateTime: str = Field(description="ISO-8601 datetime with timezone offset")
    WhoId: Optional[str] = Field(
        default=None, description="Contact or Lead ID to link the event to"
    )


class AppointmentUpdateRequest(BaseModel):
    """
    Request body for updating a Salesforce Event (partial; only set fields are sent).
    """

    Subject: Optional[str] = None
    StartDateTime: Optional[str] = None
    EndDateTime: Optional[str] = None
    WhoId: Optional[str] = None
