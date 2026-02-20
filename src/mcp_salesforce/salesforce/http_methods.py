"""
Putting the available HTTP methods within this file so easily reference them when needed.
Having them as an enum helps a lot in keeping the code clean and never having any
typos or any small issues
"""

from enum import StrEnum


class HttpMethod(StrEnum):
    """
    HTTP methods supported by the Salesforce client
    """

    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    DELETE = "DELETE"
