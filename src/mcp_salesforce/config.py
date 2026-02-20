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


settings: Settings = Settings()


def main() -> None:
    """Entry point for validating environment configuration.

    Prints loaded Salesforce configuration values.
    """
    print("Salesforce Config Loaded:")
    print(f"SF_CLIENT_ID: {settings.SALESFORCE_CLIENT_ID}")
    print(f"SF_CLIENT_SECRET: {'*' * 8}")  # don't print secrets
    print(f"SF_REFRESH_TOKEN: {'*' * 8}")
    print(f"SF_INSTANCE_URL: {settings.SALESFORCE_INSTANCE_URL}")
    print(f"SF_API_VERSION: {settings.SALESFORCE_API_VERSION}")


if __name__ == "__main__":
    main()
