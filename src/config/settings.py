"""
This module defines core project settings using Pydantic's `BaseSettings` class.

The `Settings` class encapsulates essential application configuration such as the API prefix,
version number, and project name. These values can be automatically populated from environment
variables, enabling flexible and environment-specific configurations.

Although the environment file path is currently commented out, Pydantic supports reading from
`.env` files for local development or deployment configurations.

A helper function `get_setting()` is also provided to return an instance of the `Settings` class,
offering a convenient way to access these project-wide constants across the application.
"""


from pydantic_settings import BaseSettings # type: ignore


class Settings(BaseSettings):
    """
    This class extends the BaseSettings class from FastAPI.
    It contains the project definitions.

    Args:
        None.

    Returns:
        class: extends the settings class.
    """
    #app_config : SettingsConfigDict = SettingsConfigDict(env_file=(".env",".env.prod"))

    API_STR: str = "/api/v1"

    VERSION: str = "3.0.2"
    
    PROJECT_NAME: str = "RAG Server"

def get_setting():
    """
    Return the settings object.

    Args:
        None.

    Returns:
        class: extends the settings class.
    """
    return Settings()
