import logging
from models.models import users_table
from sqlalchemy.dialects.postgresql import insert # type: ignore

# def register_user(engine, email, db_conn_str, working_dir, db_password):
#     with engine.connect() as conn:
#         existing = conn.execute(select(users_table).where(users_table.c.email == email)).fetchone()
#         if existing:
#             return False  # User already registered
#         conn.execute(
#             insert(users_table).values(email=email, db_conn_str=db_conn_str, working_dir=working_dir, password=db_password)
#         )
#         return True


def register_user(engine, db_user, email, db_conn_str, working_dir, db_password):
    """
    Registers the user into the main master user table.

    Uses `INSERT ... ON CONFLICT DO NOTHING` to ensure idempotency.

    Args:
        engine: SQLAlchemy engine connected to master DB.
        email (str): User email.
        db_conn_str (str): Connection string to tenant DB.
        working_dir (str): Path for local document storage.
        db_password (str): Password for tenant DB user.
    """
    insert_stmt = insert(users_table).values(
        user=db_user,
        email=email,
        db_conn_str=db_conn_str,
        working_dir=working_dir,
        database_name=email.replace("@", "_").replace(".", "_"),
        password=db_password
    ).on_conflict_do_nothing(index_elements=['user'])

    try:
        with engine.begin() as conn:
            conn.execute(insert_stmt)
            conn.commit()
    except Exception as e:
        logging.error(f"Error inserting user {email}: {e}")
        raise
    

