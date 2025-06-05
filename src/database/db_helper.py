"""
Handles the initialization and management of an SQLite database for storing document metadata and content across various sections.

Functions:
- `initialize_database`: Creates tables for each document section.
- `insert_file_metadata`: Inserts file metadata and content into the relevant section table.
- `delete_file`: Deletes a document by its file name from the section table.
- `get_uploaded_sections`: Retrieves sections with uploaded documents.
- `reload_session_state`: Reloads the session state with embeddings and documents from the database.
"""


# import json
# import sqlite3
# from langchain_openai import OpenAI # type: ignore
# from pathlib import Path
# from config.appconfig import settings as app_settings


# # ------------ Database Initialization and Management ------------


# # Initialize single table
# def initialize_database():
#     conn = sqlite3.connect("database/files.db")
#     cursor = conn.cursor()

#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS documents (
#             id INTEGER PRIMARY KEY,
#             doc_id TEXT UNIQUE,
#             file_name TEXT UNIQUE,
#             file_content TEXT,
#             upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         );
#     """)

#     conn.commit()
#     conn.close()


# # Insert file content
# def insert_file_metadata(doc_id, file_name, file_content):
#     conn = sqlite3.connect("database/files.db")
#     cursor = conn.cursor()
#     try:
#         cursor.execute("""
#             INSERT INTO documents (doc_id, file_name, file_content)
#             VALUES (?, ?, ?);
#         """, (doc_id, file_name, file_content))
#         print(f"Inserted: {file_name} with doc_id: {doc_id}")
#         conn.commit()
#     except sqlite3.IntegrityError:
#         print(f"File {file_name} or doc_id already exists in the database.")
#     except Exception as e:
#         print(f"Error inserting file metadata: {e}")
#     finally:
#         conn.close()



# # Delete file
# def delete_file(file_name):
#     conn = sqlite3.connect("database/files.db")
#     cursor = conn.cursor()
#     try:
#         cursor.execute("DELETE FROM documents WHERE file_name = ?", (file_name,))
#         conn.commit()
#         print(f"File {file_name} deleted.")
#     except Exception as e:
#         print(f"Error deleting file: {e}")
#     finally:
#         conn.close()

# # Check if file exists
# def check_if_file_exists(file_name):
#     conn = sqlite3.connect("database/files.db")
#     cursor = conn.cursor()
#     cursor.execute("SELECT 1 FROM documents WHERE file_name = ?", (file_name,))
#     result = cursor.fetchone()
#     conn.close()
#     return result is not None


# def check_working_directory(file_name, section):
#     """
#     Check if the corresponding working directory exists for the processed file.

#     :param file_name: The name of the file to check.
#     :param section: The selected section.
#     :return: True if the working directory exists, False otherwise.
#     """
#     working_dir = Path(f"./analysis_workspace/{section}/{file_name.split('.')[0]}")
#     return working_dir.exists() and working_dir.is_dir()  # Returns True if the directory exists


# # ---------------- Database for RFQ Metadata ----------------

# def init_db():
#     conn = sqlite3.connect("database/rfq_metadata.db")
#     cursor = conn.cursor()
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS documents (
#             id TEXT PRIMARY KEY,
#             organization_name TEXT,
#             rfq_number TEXT,
#             rfq_title TEXT,
#             submission_deadline TEXT,
#             country_or_region TEXT,
#             filename TEXT
#         )
#     ''')
#     conn.commit()
#     conn.close()


# def extract_metadata_with_llm(text):
#     llm = OpenAI(temperature=0, openai_api_key=app_settings.openai_api_key)
#     prompt = f"""
#     You are an AI assistant that extracts metadata from tender documents.

#     Given the text below, return a JSON object with:
#     - organization_name
#     - rfq_title
#     - rfq_number
#     - submission_deadline (YYYY-MM-DD)
#     - country_or_region

#     Only return a valid JSON. Here's the document content:
#     \"\"\"{text}\"\"\"
#     """
#     response = llm.invoke(prompt)
#     print("[extract_metadata_with_llm] LLM Response:", response)
#     # return response.strip()

#     return json.loads(response.choices[0].message.content)



# def save_metadata_to_db(data):
#     conn = sqlite3.connect("database/rfq_metadata.db")
#     cursor = conn.cursor()
#     cursor.execute('''
#         INSERT INTO documents (id, organization_name, rfq_number, rfq_title, submission_deadline, country_or_region, filename)
#         VALUES (?, ?, ?, ?, ?, ?, ?)
#     ''', (
#         data["id"],
#         data["organization_name"],
#         data["rfq_number"],
#         data["rfq_title"],
#         data["submission_deadline"],
#         data["country_or_region"],
#         data["filename"]
#     ))
#     conn.commit()
#     conn.close()

# # ----------------- Retrieve from both databases -----------------
# def get_all_metadata():
#     # Connect to files.db to get doc_ids
#     conn_files = sqlite3.connect("database/files.db")
#     cursor_files = conn_files.cursor()
#     cursor_files.execute("SELECT doc_id FROM documents")
#     doc_ids = [row[0] for row in cursor_files.fetchall()]
#     conn_files.close()

#     # Connect to rfq_metadata.db to get metadata
#     conn_metadata = sqlite3.connect("database/rfq_metadata.db")
#     cursor_metadata = conn_metadata.cursor()
#     metadata = {}
#     for doc_id in doc_ids:
#         cursor_metadata.execute("SELECT organization_name, rfq_title FROM metadata WHERE doc_id = ?", (doc_id,))
#         row = cursor_metadata.fetchone()
#         if row:
#             metadata[doc_id] = {
#                 "organization_name": row[0],
#                 "rfq_title": row[1]
#             }
#     conn_metadata.close()
#     return metadata



from datetime import datetime, timedelta, timezone
import json
import logging
import traceback
import uuid
import psycopg2 # type: ignore
from psycopg2.extras import RealDictCursor # type: ignore
from langchain_openai import OpenAI  # type: ignore
from pathlib import Path
from config.appconfig import settings as app_settings
from utils import parse_response_for_doc_ids
import psycopg2 # type: ignore
from config.appconfig import settings as app_settings

# # Database connection parameters
# PG_PARAMS = {
#     "dbname": app_settings.db_name,
#     "user": app_settings.user,
#     "password": app_settings.password,  
#     "host": app_settings.host, 
#     "port": app_settings.port_db
# }

# # ------------ Database Initialization and Management ------------

# def get_pg_connection():
#     return psycopg2.connect(**PG_PARAMS)

def open_tenant_db_connection(db_user: str, db_name: str, db_password: str):
    conn = psycopg2.connect(
        user=db_user,
        dbname=db_name,
        password=db_password,
        host=app_settings.host,
        port=app_settings.port_db,
    )
    return conn


def initialize_age(db_user: str, db_name: str, db_password: str):
    conn = psycopg2.connect(
        user=db_user,
        dbname=db_name,
        password=db_password,
        host=app_settings.host,
        port=app_settings.port_db,
    )
    cur = conn.cursor()

    # Ensure AGE extension is created (needed only once per DB)
    cur.execute("CREATE EXTENSION IF NOT EXISTS age;")

    # Load AGE into the session (required every time)
    cur.execute("LOAD 'age';")

    # Set the search_path for using ag_catalog
    cur.execute("SET search_path = ag_catalog;")

    conn.commit()
    cur.close()
    conn.close()



def initialize_database(db_user: str, db_name: str, db_password: str):
    conn = open_tenant_db_connection(db_user, db_name, db_password)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            document_names TEXT PRIMARY KEY,
            file_name TEXT UNIQUE,
            file_content TEXT,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rfqs (
            rfq_id SERIAL PRIMARY KEY,
            document_name TEXT UNIQUE,
            organisation_name TEXT,
            reference_no TEXT UNIQUE,
            title TEXT,
            submission_deadline DATE,
            country_or_region TEXT,
            file_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            contact_email TEXT
        );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proposals (
        proposal_id SERIAL PRIMARY KEY,
        rfq_id INTEGER REFERENCES rfqs(rfq_id) ON DELETE CASCADE,
        proposal_title TEXT,
        proposal_content TEXT,
        is_winning BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        summary TEXT,
        proposal_author TEXT
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()


def insert_file_metadata(document_name, file_name, file_content, db_user, db_name, db_password):
    conn = open_tenant_db_connection(db_user, db_name, db_password)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO documents (document_name, file_name, file_content)
            VALUES (%s, %s, %s)
            ON CONFLICT (document_name) DO NOTHING;
        """, (document_name, file_name, file_content))
        print(f"Inserted: {file_name} with document_name: {document_name}")
        conn.commit()
    except Exception as e:
        print(f"Error inserting file metadata: {e}")
    finally:
        cursor.close()
        conn.close()

# ---------------- Metadata with LLM ----------------

def extract_metadata_with_llm(text):
    llm = OpenAI(temperature=0, openai_api_key=app_settings.openai_api_key)
    prompt = f"""
    You are an AI assistant that extracts metadata from tender documents.
    Understand the content of the document and extract the following metadata fields.
    Do not return wrong information or make assumptions.
    Be sure of the following fields:
    - organization_name
    - title
    - reference_no
    - submission_deadline (YYYY-MM-DD)
    - country_or_region
    If any of these fields are not present in the text, return null for that field.

    Given the text below, return a JSON object with:
    - organization_name
    - title
    - reference_no
    - submission_deadline (YYYY-MM-DD)
    - country_or_region

    Only return a valid JSON. Here's the document content:
    \"\"\"{text}\"\"\"
    """
    response = llm.invoke(prompt)
    print("[extract_metadata_with_llm] LLM Response:", response)
    return json.loads(response)


def insert_document(document_name: str, file_name: str, file_content: str, db_user, db_name, db_password):
    conn = open_tenant_db_connection(db_user, db_name, db_password)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO documents (document_name, file_name, file_content)
            VALUES (%s, %s, %s)
            ON CONFLICT (document_name) DO UPDATE SET
                file_name = EXCLUDED.file_name,
                file_content = EXCLUDED.file_content,
                upload_time = CURRENT_TIMESTAMP;
        """, (document_name, file_name, file_content))
        conn.commit()
    except Exception as e:
        print(f"❌ Error inserting document: {e}")
    finally:
        cursor.close()
        conn.close()



def save_metadata_to_db(data, db_user, db_name, db_password):
    conn = open_tenant_db_connection(db_user, db_name, db_password)
    logging.info("Connected to DB: %s", conn.dsn)
    cursor = conn.cursor()
    try:
        logging.info("Inserting metadata into rfqs: %s", data)
        cursor.execute("""
            INSERT INTO rfqs (
                document_name,
                organization_name,
                reference_no,
                title,
                submission_deadline,
                country_or_region,
                filename,
                contact_email
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (document_name) DO UPDATE SET
                organization_name = EXCLUDED.organization_name,
                reference_no = EXCLUDED.reference_no,
                title = EXCLUDED.title,
                submission_deadline = EXCLUDED.submission_deadline,
                country_or_region = EXCLUDED.country_or_region,
                filename = EXCLUDED.filename,
                contact_email = EXCLUDED.contact_email;
        """, (
            data.get("document_name") or data.get("id") or data.get("filename"),
            data.get("organization_name"),
            data.get("reference_no"),
            data.get("title"),
            data.get("submission_deadline"),
            data.get("country_or_region"),
            data.get("filename"),
            data.get("contact_email"),
        ))

        conn.commit()
        logging.info(f"✅ RFQ metadata saved for {data.get('document_name')}")
    except Exception as e:
        logging.error("❌ Error saving RFQ metadata: %s\nData: %s", e, data)
        logging.error(traceback.format_exc())
    finally:
        cursor.close()
        conn.close()


# def save_metadata_to_db(data):
#     conn = get_pg_connection()
#     logging.info("Connected to DB: %s", conn.dsn)
#     cursor = conn.cursor()
#     try:
#         logging.info("Inserting metadata:", data)
#         cursor.execute("""
#             INSERT INTO metadata (doc_id, organization_name, rfq_number, rfq_title, submission_deadline, country_or_region, filename)
#             VALUES (%s, %s, %s, %s, %s, %s, %s)
#             ON CONFLICT (doc_id) DO UPDATE SET
#               organization_name = EXCLUDED.organization_name,
#               rfq_number = EXCLUDED.rfq_number,
#               rfq_title = EXCLUDED.rfq_title,
#               submission_deadline = EXCLUDED.submission_deadline,
#               country_or_region = EXCLUDED.country_or_region,
#               filename = EXCLUDED.filename;
#         """, (
#             data["id"],
#             data["organization_name"],
#             data["rfq_number"],
#             data["rfq_title"],
#             data["submission_deadline"],
#             data["country_or_region"],
#             data["filename"]
#         ))
#         conn.commit()
#     except Exception as e:
#         logging.info("❌ Error saving metadata: %s", e)
#         logging.info("Data: %s", data)
#     finally:
#         cursor.close()
#         conn.close()

# ----------------- Retrieve metadata -----------------
def fetch_metadata_from_db(db_user, db_name, db_password):
    conn = open_tenant_db_connection(db_user, db_name, db_password)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT rfq_id, document_name, organization_name, reference_no, title,
                   submission_deadline, country_or_region, filename, contact_email
            FROM rfqs
        """)
        rows = cursor.fetchall()
    except Exception as e:
        print(f"Error fetching metadata: {e}")
        rows = []
    finally:
        cursor.close()
        conn.close()

    metadata = []
    for row in rows:
        metadata.append({
            "rfq_id": row[0],
            "document_name": row[1],
            "organization_name": row[2],
            "reference_no": row[3],
            "title": row[4],
            "submission_deadline": str(row[5]),
            "country_or_region": row[6],
            "filename": row[7],
            "contact_email": row[8]
        })

    return metadata

# ----------------- Winning Proposals -----------------

# --- Get recent RFQs and Proposals ---
# def get_recent_activity(db_user: str, db_name: str, db_password: str, days: int = 30):
#     conn = open_tenant_db_connection(db_user, db_name, db_password)
#     cursor = conn.cursor()

#     cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

#     cursor.execute("""
#         SELECT * FROM rfqs WHERE created_at >= %s;
#     """, (cutoff_date,))
#     recent_rfqs = cursor.fetchall()

#     cursor.execute("""
#         SELECT * FROM proposals WHERE created_at >= %s;
#     """, (cutoff_date,))
#     recent_proposals = cursor.fetchall()

#     cursor.close()
#     conn.close()

#     return {
#         "rfqs": recent_rfqs,
#         "proposals": recent_proposals
#     }


def get_recent_activity(db_user, db_name, db_password):
    conn = open_tenant_db_connection(db_user, db_name, db_password)
    cursor = conn.cursor()

    # Fetch RFQs from last 30 days
    cursor.execute("""
        SELECT id, title, created_at
        FROM rfqs
        WHERE created_at >= NOW() - INTERVAL '30 days'
        ORDER BY created_at DESC
    """)
    rfq_rows = cursor.fetchall()

    # Build list of RFQs as dicts
    rfqs = [
        {
            "id": str(row[0]),
            "title": row[1],
            "created_at": row[2].isoformat() if row[2] else None,
        }
        for row in rfq_rows
    ]

    # Fetch proposals linked to those RFQs, also last 30 days
    cursor.execute("""
        SELECT id, rfq_id, title, content, is_winning, created_at
        FROM proposals
        WHERE created_at >= NOW() - INTERVAL '30 days'
          AND rfq_id IN (
              SELECT id FROM rfqs WHERE created_at >= NOW() - INTERVAL '30 days'
          )
        ORDER BY created_at DESC
    """)
    proposal_rows = cursor.fetchall()

    proposals = [
        {
            "id": str(row[0]),
            "rfq_id": str(row[1]),
            "title": row[2],
            "content": row[3],
            "is_winning": row[4],
            "created_at": row[5].isoformat() if row[5] else None,
        }
        for row in proposal_rows
    ]

    cursor.close()
    conn.close()

    return {"rfqs": rfqs, "proposals": proposals}


# --- Get Winning Proposals ---
def get_winning_proposals(db_user: str, db_name: str, db_password: str):
    conn = open_tenant_db_connection(db_user, db_name, db_password)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM proposals WHERE is_winning = TRUE;
    """)
    winning_proposals = cursor.fetchall()

    cursor.close()
    conn.close()
    return winning_proposals


async def extract_proposal_metadata_llm(proposal_text: str) -> dict:
    llm = OpenAI(temperature=0, openai_api_key=app_settings.openai_api_key)
    
    prompt = f"""
    <CONTEXT>
    You are a CDGA staff who specializes in giving titles to proposals. 
    Given this proposal:

    {proposal_text}

    Thoroughly go through it and give it a title that is very suitable to it.
    Understand the context in the proposal before giving it the title.

    Also generate a summarized text of the proposal using the main points.
    </CONTEXT>

    Return it as JSON with 'title' and 'summary'.
    """
    
    response = llm.invoke(prompt)
    try:
        return json.loads(response.strip())
    except Exception as e:
        print("JSON parse error:", e)
        return {"title": "Untitled Proposal", "summary": ""}

    

def store_proposal_to_db(db_user, db_name, db_password, rfq_id, title, content, summary, is_winning):
    conn = open_tenant_db_connection(db_user, db_name, db_password)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO proposals (rfq_id, proposal_title, proposal_content, summary, is_winning, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        rfq_id, title, content, summary, is_winning, datetime.now(timezone.utc)
    ))

    conn.commit()
    cursor.close()
    conn.close()
