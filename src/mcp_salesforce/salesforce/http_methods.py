"""
Putting the available HTTP methods within this file so easily reference them when needed.
Having them as an enum helps a lot in keeping the code clean and never having any
typos or any small issues
"""

from enum import StrEnum


# TODO: consider using thie for the methods within the `Salesforce` client later on
#  to the code to make the code stronger
#  need automated testing and more testing to be sure the code works correctly with the enums
#  that I don't want to do right now
class HttpMethod(StrEnum):
    """
    HTTP methods supported by the Salesforce client
    """

    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    DELETE = "DELETE"
