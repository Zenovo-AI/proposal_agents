import hashlib
import logging
from fastapi import Request, HTTPException, Depends # type: ignore
from itsdangerous import URLSafeTimedSerializer, BadSignature # type: ignore
from sqlalchemy import select # type: ignore
from sqlalchemy.engine import create_engine # type: ignore
from models.models import users_table
from config.appconfig import settings as app_settings





serializer = URLSafeTimedSerializer(app_settings.session_secret_key)


def get_user_email_from_session(request: Request) -> str:
    user_session = request.cookies.get("user_session")
    if not user_session:
        raise HTTPException(status_code=401, detail="User session not found")

    try:
        serializer = URLSafeTimedSerializer(app_settings.session_secret_key)
        decoded_session = serializer.loads(user_session)
        email = decoded_session["email"]
    except BadSignature as e:
        logging.error(f"Failed to decode session token: {e}")
        raise HTTPException(status_code=401, detail="Invalid user session")

    logging.info(f"✅ Decoded user email: {email}")
    return email



def get_user_session(request: Request):
    cookie = request.cookies.get("user_session")
    print("[get_user_session] Raw cookie:", cookie)
    if not cookie:
        logging.warning("No session token found.")
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        session_data = serializer.loads(cookie)
        print("[get_user_session] Decoded session:", session_data)
    except BadSignature:
        raise HTTPException(status_code=401, detail="Invalid session")

    return session_data


def get_tenant_db_connection_info(email: str = Depends(get_user_email_from_session)):
    info = lookup_user_db_credentials(email)
    return info


def lookup_user_db_credentials(email: str):
    engine = create_engine(app_settings.master_db_url)
    with engine.connect() as conn:
        result = conn.execute(
            select(users_table).where(users_table.c.email == email)
        ).fetchone()

        if not result:
            logging.error(f"User {email} not found in users_table.")
            raise HTTPException(status_code=404, detail="User not registered")

        logging.info(f"User record found: {result}")

    # Extract database connection info
        db_user = result.user
        db_name = result.database_name
        working_dir = result.working_dir
        db_password = result.password
        
        logging.info(f"Database credentials for {email} retrieved successfully.")
        logging.info(f"DB User: {db_user}, DB Name: {db_name}, Working Dir: {working_dir}")
        logging.info(f"DB Password: {db_password}")
    return db_user, db_name, db_password, working_dir
