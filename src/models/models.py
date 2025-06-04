from sqlalchemy import MetaData, Table, Column, String # type: ignore

metadata = MetaData()

users_table = Table(
    "users",
    metadata,
    Column("user", String, primary_key=True),
    Column("email", String, nullable=False),
    Column("database_name", String, nullable=False),
    Column("db_conn_str", String, nullable=False),
    Column("working_dir", String),
    Column("password", String, nullable=False)
)
