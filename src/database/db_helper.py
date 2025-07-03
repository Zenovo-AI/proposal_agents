"""
Handles the initialization and management of an SQLite database for storing document metadata and content across various sections.

Functions:
- `initialize_database`: Creates tables for each document section.
- `insert_file_metadata`: Inserts file metadata and content into the relevant section table.
- `delete_file`: Deletes a document by its file name from the section table.
- `get_uploaded_sections`: Retrieves sections with uploaded documents.
- `reload_session_state`: Reloads the session state with embeddings and documents from the database.
"""



from datetime import datetime, timezone
import json
import logging
import traceback
from typing import List
import psycopg2 # type: ignore
from openai import OpenAI  # type: ignore
from config.appconfig import settings as app_settings
import psycopg2 # type: ignore
from config.appconfig import settings as app_settings

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
            document_name TEXT PRIMARY KEY,
            file_name TEXT UNIQUE,
            file_content TEXT,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rfqs (
            rfq_id SERIAL PRIMARY KEY,
            document_name TEXT UNIQUE,
            organization_name TEXT,
            reference_no TEXT UNIQUE,
            title TEXT,
            submission_deadline DATE,
            country_or_region TEXT,
            file_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            contact_email TEXT,
            prompt_suggestions TEXT
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
    from langchain_openai import OpenAI # type: ignore
    llm = OpenAI(temperature = 0, openai_api_key=app_settings.openai_api_key)
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


# def extract_prompt_suggestions(text: str) -> List[str]:
#     client = OpenAI(api_key=app_settings.openai_api_key)
#     prompt = f"""
#     You are an assistant that ***STRICTLY*** generates insightful prompt suggestions based on RFQ documents.

#     Your task is to read the RFQ content below and generate exactly 4 advanced, domain-relevant questions that someone might ask when preparing a technical or proposal response.
#     Always generate prompt suggestions, NEVER LEAVE IT BLANK.
#     Make sure that each prompt suggestion doesn't exceed 10  to 15 words.
    

#     ⚠️ Strict Instructions:
#     - Format your response as a **valid JSON array of 4 strings**.
#     - Do NOT include any explanations, markdown, or extra text — just return the raw array.
#     - Example format:
#     [
#     "First question?",
#     "Second question?",
#     "Third question?",
#     "Fourth question?"
#     ]

#     RFQ Content:
#     {text}
#     """

#     response = client.chat.completions.create(
#         model="gpt-4o-2024-08-06",
#         messages=[{"role": "system", "content": prompt}],
#         response_format={"type": "json_object"},
#         temperature=0
#     )


#     logging.info("Prompt: %s", response)
#     try:
#         data = json.loads(response.choices[0].message.content)
#         suggestions = data.get("questions", [])
#         if isinstance(suggestions, list) and len(suggestions) == 4:
#             return suggestions
#         else:
#             logging.warning(f"Prompt suggestions not a list: {response}")
#             return []
#     except json.JSONDecodeError:
#         logging.error(f"Failed to parse prompt suggestions: {response}")
#         return []

def extract_prompt_suggestions(text: str) -> List[str]:
    client = OpenAI(api_key=app_settings.openai_api_key)

    prompt = f"""
    You are an assistant that ***STRICTLY*** generates insightful prompt suggestions based on RFQ documents.

    Your task is to read the RFQ content below and generate exactly 4 advanced, domain-relevant questions that someone might ask when preparing a technical or proposal response.
    Always generate prompt suggestions, NEVER LEAVE IT BLANK.
    Make sure that each prompt suggestion doesn't exceed 10 to 15 words.

    ⚠️ Strict Instructions:
    - Format your response as a **valid JSON array of 4 strings**.
    - Do NOT include any explanations, markdown, or extra text — just return the raw array.
    - Example format:
    [
        "First question?",
        "Second question?",
        "Third question?",
        "Fourth question?"
    ]

    RFQ Content:
    {text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[{"role": "system", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0,
        )

        logging.info("Prompt: %s", response)

        content = response.choices[0].message.content

        try:
            data = json.loads(content)

            # Try all known keys or fallback to list parsing
            for key in ["prompts", "questions", "suggestions"]:
                if key in data and isinstance(data[key], list):
                    return data[key]

            # If content is a list itself
            if isinstance(data, list):
                return data

            # Fallback: Try to parse the value of the only key as list
            if isinstance(data, dict) and len(data) == 1:
                only_val = next(iter(data.values()))
                if isinstance(only_val, list):
                    return only_val

            logging.warning("Prompt suggestions not a list or recognizable: %s", content)
            return []
        except json.JSONDecodeError:
            logging.error("Failed to parse response content as JSON: %s", content)
            return []

    except Exception as e:
        logging.exception("Error during prompt suggestion generation")
        return []





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


def save_metadata_to_db(data, prompt_suggestions, db_user, db_name, db_password):
    prompt_suggestions_str = json.dumps(prompt_suggestions)
    # logging.info("Prompt suggestions: %s", prompt_suggestions_str)

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
                file_name,
                contact_email,
                prompt_suggestions
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (document_name) DO UPDATE SET
                organization_name = EXCLUDED.organization_name,
                reference_no = EXCLUDED.reference_no,
                title = EXCLUDED.title,
                submission_deadline = EXCLUDED.submission_deadline,
                country_or_region = EXCLUDED.country_or_region,
                file_name = EXCLUDED.file_name,
                contact_email = EXCLUDED.contact_email,
                prompt_suggestions = EXCLUDED.prompt_suggestions;
        """, (
            data.get("document_name") or data.get("id") or data.get("file_name"),
            data.get("organization_name"),
            data.get("reference_no"),
            data.get("title"),
            data.get("submission_deadline"),
            data.get("country_or_region"),
            data.get("file_name"),
            data.get("contact_email"),
            prompt_suggestions_str
        ))

        conn.commit()
        logging.info(f"✅ RFQ metadata saved for {data.get('document_name')}")
    except Exception as e:
        logging.error("❌ Error saving RFQ metadata: %s\nData: %s", e, data)
        logging.error(traceback.format_exc())
    finally:
        cursor.close()
        conn.close()

# ----------------- Retrieve metadata -----------------
def fetch_metadata_from_db(db_user, db_name, db_password):
    conn = open_tenant_db_connection(db_user, db_name, db_password)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT rfq_id, document_name, organization_name, reference_no, title,
                   submission_deadline, country_or_region, file_name, contact_email
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
            "file_name": row[7],
            "contact_email": row[8]
        })

    return metadata

# ----------------- Winning Proposals -----------------


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
    from langchain_openai import OpenAI # type: ignore
    llm = OpenAI(temperature = 0, openai_api_key=app_settings.openai_api_key)
    
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
