"""
This file is reading the env vars from the `.env` file
and converting them to nice variables for us to easily use within our code
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.

    Attributes:
        SALESFORCE_CLIENT_ID: Salesforce Connected App consumer key.
        SALESFORCE_CLIENT_SECRET: Salesforce Connected App consumer secret.
        SALESFORCE_REFRESH_TOKEN: OAuth refresh token for obtaining access tokens.
        SALESFORCE_INSTANCE_URL: Base Salesforce instance URL (e.g., https://xxx.my.salesforce.com).
        SALESFORCE_API_VERSION: Salesforce REST API version (default: v60.0).

    See Also:
        [Pydantic Settings Management](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    SALESFORCE_CLIENT_ID: str
    SALESFORCE_CLIENT_SECRET: str
    SALESFORCE_INSTANCE_URL: str
    SALESFORCE_REFRESH_TOKEN: str
    SALESFORCE_API_VERSION: str = "v60.0"


# Pydantic `BaseSettings` loads required fields from environment variables at runtime.
# Mypy cannot detect this dynamic loading and incorrectly expects constructor args.
# We intentionally ignore the `call-arg` error here.
settings: Settings = Settings()  # type: ignore[call-arg]
