import os
import random, string
import psycopg2
from multi_tenant.register_user import register_user
from utils import sanitize_email

def generate_password(length=16):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def create_tenant_role(cur, role_name, password):
    cur.execute(f"CREATE ROLE {role_name} WITH LOGIN PASSWORD %s;", (password,))
    cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {role_name} TO {role_name};")

def onboard_user(email, pg_super_conn_info, master_db_engine):
    # ...
    tenant_dbname = sanitize_email(email)
    tenant_role = tenant_dbname + "_user"
    tenant_password = generate_password()

    with psycopg2.connect(**pg_super_conn_info) as conn:
        with conn.cursor() as cur:
            # Create database
            cur.execute(f'CREATE DATABASE "{tenant_dbname}"')
            # Create role
            create_tenant_role(cur, tenant_role, tenant_password)
            # Grant privileges (optional, or alter db owner to tenant_role)
            cur.execute(f"ALTER DATABASE {tenant_dbname} OWNER TO {tenant_role}")


    working_dir = f"./data/lightRAG/{tenant_dbname}"
    os.makedirs(working_dir, exist_ok=True)
    tenant_db_conn_str = f"postgresql://{tenant_role}:{tenant_password}@{pg_super_conn_info['host']}:{pg_super_conn_info['port']}/{tenant_dbname}"

    # Store tenant_db_conn_str in master DB
    register_user(master_db_engine, email, tenant_db_conn_str, working_dir)
    return tenant_db_conn_str, working_dir
