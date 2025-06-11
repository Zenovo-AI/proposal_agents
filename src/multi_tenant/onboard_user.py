import logging
import os
import secrets
import string
import time
import psycopg2 # type: ignore
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type, before_sleep_log # type: ignore
import logging
from database.db_helper import initialize_database
from models.models import users_table
from multi_tenant.register_user import register_user
from multi_tenant.superuser import create_tenant_database
from sqlalchemy import select # type: ignore

def generate_secure_password(length: int = 16) -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

# ✅ Tenacity retry logic with exponential backoff
# @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(5))
# def connect_with_tenacity(conn_info: dict):
    # return psycopg2.connect(**conn_info)

logger = logging.getLogger(__name__)

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(psycopg2.OperationalError),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def connect_with_tenacity(conn_info: dict):
    return psycopg2.connect(**conn_info)


def onboard_user(db_user: str, email: str, pg_super_conn_info: dict, master_db_engine):
    """
    1. Check if tenant DB exists; create if not
    2. Create user working directory
    3. Register user in master DB with unique DB credentials (early, idempotent)
    4. Initialize tenant DB
    5. Return (user, db_name, db_conn_str, working_dir, user_password)
    """
    db_name = email.replace("@", "_").replace(".", "_")

    # Early return if user already registered
    with master_db_engine.connect() as conn:
        res = conn.execute(
            select(users_table).where(users_table.c.email == email)
        ).fetchone()
        if res:
            return res.user, db_name, res.db_conn_str, res.working_dir, res.password

    user_password = generate_secure_password()
    tenant_db_conn_str = f"postgresql://{db_user}:{user_password}@{pg_super_conn_info['host']}:{pg_super_conn_info['port']}/{db_name}"
    working_dir = f"./data/lightRAG/{db_name}"
    os.makedirs(working_dir, exist_ok=True)

    register_user(
        master_db_engine,
        db_user,
        email,
        tenant_db_conn_str,
        working_dir,
        db_password=user_password
    )

    create_tenant_database(db_user, db_name, pg_super_conn_info, user_password)
    time.sleep(2)
    # await configure_age_extensions(db_name, pg_super_conn_info, graph_name='chunk_entity_relation', tenant_user=db_user)

    try:
        logging.info(f"Connecting with password: {user_password}")
        initialize_database(db_user, db_name, user_password)
    except Exception as e:
        logging.error(f"Failed to initialize tenant DB for {email}: {e}")
        raise

    return db_user, db_name, tenant_db_conn_str, working_dir, user_password
