import logging
import psycopg2  # type: ignore
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT  # type: ignore
from config.appconfig import settings as app_settings
from psycopg2 import sql

logging.basicConfig(level=logging.INFO)

# def create_tenant_database(db_name: str, pg_super_conn_info: dict, user_password: str):
#     """
#     Create a new PostgreSQL database and user for a tenant, and set up required extensions.

#     Steps:
#     - Connects as superuser.
#     - Creates user and database if not exists.
#     - Connects to tenant DB as superuser to enable extensions: vector, age.
#     - Loads 'age' and sets search_path to ag_catalog.
#     """

#     pg_super_conn_info = {
#         "dbname": app_settings.db_name,
#         "user": app_settings.user,
#         "password": app_settings.password,
#         "host": app_settings.host,
#         "port": app_settings.port_db
#     }

#     # Step 1: Connect to superuser database
#     conn = psycopg2.connect(**pg_super_conn_info)
#     conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
#     cur = conn.cursor()

#     # Step 2: Check and create database and user
#     cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
#     if cur.fetchone():
#         logging.info(f"Database '{db_name}' already exists. Skipping creation.")
#     else:
#         cur.execute(f"CREATE USER {db_name} WITH PASSWORD %s;", (user_password,))
#         cur.execute(f"CREATE DATABASE {db_name} OWNER {db_name};")
#         logging.info(f"Database '{db_name}' and user created.")

#     cur.close()
#     conn.close()

#     # Step 3: Connect to tenant DB as superuser to setup extensions
#     try:
#         extension_conn = psycopg2.connect(
#             dbname=db_name,
#             user=pg_super_conn_info["user"],
#             password=pg_super_conn_info["password"],
#             host=pg_super_conn_info["host"],
#             port=pg_super_conn_info["port"]
#         )
#         extension_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
#         extension_cur = extension_conn.cursor()

#         # Create necessary extensions
#         extension_cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
#         extension_cur.execute("CREATE EXTENSION IF NOT EXISTS age;")
#         extension_cur.execute("LOAD 'age';")
#         extension_cur.execute("SET search_path TO ag_catalog;")

#         # Create the AGE graph for LightRAG
#         extension_cur.execute("SELECT * FROM create_graph('chunk_entity_relation')")
#         logging.info(f"Extensions 'vector' and 'age' configured on '{db_name}'.")

#         extension_cur.close()
#         extension_conn.close()
#     except Exception as e:
#         logging.error(f"Failed to configure extensions in '{db_name}': {e}")
#         raise


def create_tenant_database(user: str, db_name: str, pg_super_conn_info: dict, user_password: str) -> str:
    """
    Create a PostgreSQL user and database for a tenant,
    enable required extensions, and grant necessary privileges.

    Returns:
        The username created.
    """
    try:
        conn = psycopg2.connect(**pg_super_conn_info)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Create user if not exists
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (user,))
        if not cur.fetchone():
            cur.execute(
                sql.SQL("CREATE USER {} WITH PASSWORD %s;").format(sql.Identifier(user)),
                (user_password,)
            )
            logging.info(f"User '{user}' created.")
            
            # Make user a SUPERUSER (⚠️ Risky)
            cur.execute(
                sql.SQL("ALTER ROLE {} WITH SUPERUSER;").format(sql.Identifier(user))
            )
            logging.info(f"User '{user}' promoted to SUPERUSER.")
        else:
            logging.info(f"User '{user}' already exists.")

        # Create DB if not exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        if not cur.fetchone():
            cur.execute(
                sql.SQL("CREATE DATABASE {} OWNER {};").format(sql.Identifier(db_name), sql.Identifier(user))
            )
            logging.info(f"Database '{db_name}' created.")
        else:
            logging.info(f"Database '{db_name}' already exists.")

        # Grant privileges
        cur.execute(
            sql.SQL("GRANT CONNECT ON DATABASE {} TO {};").format(sql.Identifier(db_name), sql.Identifier(user))
        )

        cur.close()
        conn.close()

        # Set up extensions
        extension_conn = psycopg2.connect(
            dbname=db_name,
            user=pg_super_conn_info["user"],
            password=pg_super_conn_info["password"],
            host=pg_super_conn_info["host"],
            port=pg_super_conn_info["port"]
        )
        extension_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        extension_cur = extension_conn.cursor()

        extension_cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        extension_cur.execute("CREATE EXTENSION IF NOT EXISTS age;")
        extension_cur.execute("LOAD 'age';")
        extension_cur.execute("SET search_path TO ag_catalog;")
        extension_cur.execute("SELECT * FROM create_graph('chunk_entity_relation');")

        extension_cur.execute(
            sql.SQL("GRANT USAGE ON SCHEMA public TO {};").format(sql.Identifier(user))
        )
        extension_cur.execute(
            sql.SQL("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {};").format(sql.Identifier(user))
        )

        extension_cur.close()
        extension_conn.close()

        return user

    except Exception as e:
        logging.error(f"Error during tenant database creation: {e}")
        raise



# def create_tenant_database(user: str, db_name: str, pg_super_conn_info: dict, user_password: str) -> str:
#     """
#     Create a PostgreSQL user and database for a tenant,
#     enable required extensions, and grant necessary privileges.

#     Returns:
#         The username created.
#     """
#     conn = psycopg2.connect(**pg_super_conn_info)
#     conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
#     cur = conn.cursor()

#     # Create user if not exists
#     cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (user,))
#     if not cur.fetchone():
#         cur.execute(f"CREATE USER {user} WITH PASSWORD %s;", (user_password,))
#         logging.info(f"User '{user}' created.")
        
#         # Make user a SUPERUSER (⚠️ Risky)
#         cur.execute(f"ALTER ROLE {user} WITH SUPERUSER;")
#         logging.info(f"User '{user}' promoted to SUPERUSER.")
#     else:
#         logging.info(f"User '{user}' already exists.")

#     # Create DB if not exists
#     cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
#     if not cur.fetchone():
#         cur.execute(f"CREATE DATABASE {db_name} OWNER {user};")
#         logging.info(f"Database '{db_name}' created.")
#     else:
#         logging.info(f"Database '{db_name}' already exists.")

#     # Grant privileges
#     cur.execute(f"GRANT CONNECT ON DATABASE {db_name} TO {user};")

#     cur.close()
#     conn.close()

#     # Set up extensions
#     try:
#         extension_conn = psycopg2.connect(
#             dbname=db_name,
#             user=pg_super_conn_info["user"],
#             password=pg_super_conn_info["password"],
#             host=pg_super_conn_info["host"],
#             port=pg_super_conn_info["port"]
#         )
#         extension_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
#         extension_cur = extension_conn.cursor()

#         extension_cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
#         extension_cur.execute("CREATE EXTENSION IF NOT EXISTS age;")
#         extension_cur.execute("LOAD 'age';")
#         extension_cur.execute("SET search_path TO ag_catalog;")
#         extension_cur.execute("SELECT * FROM create_graph('chunk_entity_relation');")

#         extension_cur.execute(f"GRANT USAGE ON SCHEMA public TO {user};")
#         extension_cur.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {user};")

#         extension_cur.close()
#         extension_conn.close()
#     except Exception as e:
#         logging.error(f"Failed to configure extensions in '{db_name}': {e}")
#         raise