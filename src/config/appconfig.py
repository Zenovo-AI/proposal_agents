"""
This module loads application settings and secrets from environment variables using the `dotenv` package.

It defines the `AppSettings` class, which centralizes all configuration values required across the app.
These include environment details (e.g., environment type, port), authentication credentials for the app
and external services (e.g., Google OAuth, OpenAI), database connection strings, and keys for third-party
APIs such as DigitalOcean Spaces and Google Cloud.

The settings are loaded from a `.env` file into environment variables, making it easy to manage and switch
between different environments (development, staging, production) without hardcoding sensitive information.

An instance of the `AppSettings` class is created and stored as `settings`, providing a convenient and secure
way to access configuration values throughout the application.
"""


# Load .env file using:
from urllib.parse import quote_plus
from dotenv import load_dotenv # type: ignore
load_dotenv()
import os

class AppSettings:
    environment= os.getenv("ENVIRONMENT")
    port = os.getenv("PORT")
    auth_user = os.getenv("AUTH_USERNAME")
    auth_password = os.getenv("AUTH_PASSWORD")
    domain = os.getenv("DOMAIN")
    db_conn_url = os.getenv("DB_CONN_URL")
    db_name = os.getenv("DB_NAME")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_api_base = os.getenv("OPENAI_API_BASE")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    do_spaces_secret_key = os.getenv("DO_SPACES_SECRET_KEY")
    do_spaces_access_key = os.getenv("DO_SPACES_ACCESS_KEY")
    client_secret_b64 = os.getenv("GOOGLE_AUTH_CLIENT_SECRET_B64")
    service_account = os.getenv("SERVICE_ACCOUNT_B64")
    session_secret_key = os.getenv("SESSION_SECRET_KEY")
    google_auth_endpoint = os.getenv("GOOGLE_AUTH_ENDPOINT")
    google_token_endpoint = os.getenv("GOOGLE_TOKEN_ENDPOINT")
    google_userinfo_endpoint = os.getenv("GOOGLE_USERINFO_ENDPOINT")
    redirect_uri_1 = os.getenv("GOOGLE_REDIRECT_URI_1")
    redirect_uri_2 = os.getenv("GOOGLE_REDIRECT_URI_2")
    redirect_uri_3 = os.getenv("GOOGLE_REDIRECT_URI_3")
    db_name = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port_db = os.getenv("DB_PORT")
    

    @property
    def master_db_url(self) -> str:
        # URL-encode password to handle special characters like '@'
        encoded_password = quote_plus(self.password) if self.password else ""
        return (
            f"postgresql://{self.user}:{encoded_password}@"
            f"{self.host}:{self.port_db}/{self.db_name}"
        )

settings = AppSettings()