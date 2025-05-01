"""
Handles the initialization and management of an SQLite database for storing document metadata and content across various sections.

Functions:
- `initialize_database`: Creates tables for each document section.
- `insert_file_metadata`: Inserts file metadata and content into the relevant section table.
- `delete_file`: Deletes a document by its file name from the section table.
- `get_uploaded_sections`: Retrieves sections with uploaded documents.
- `reload_session_state`: Reloads the session state with embeddings and documents from the database.
"""


import sqlite3
from pathlib import Path


# Initialize single table
def initialize_database():
    conn = sqlite3.connect("files.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY,
            file_name TEXT UNIQUE,
            file_content TEXT,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()

# Insert file content
def insert_file_metadata(file_name, file_content):
    conn = sqlite3.connect("files.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO documents (file_name, file_content)
            VALUES (?, ?);
        """, (file_name, file_content))
        print(f"File content inserted: {file_name}")
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"File {file_name} already exists in the database.")
    except Exception as e:
        print(f"Error inserting file metadata: {e}")
    finally:
        conn.close()

# Delete file
def delete_file(file_name):
    conn = sqlite3.connect("files.db")
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM documents WHERE file_name = ?", (file_name,))
        conn.commit()
        print(f"File {file_name} deleted.")
    except Exception as e:
        print(f"Error deleting file: {e}")
    finally:
        conn.close()

# Check if file exists
def check_if_file_exists(file_name):
    conn = sqlite3.connect("files.db")
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM documents WHERE file_name = ?", (file_name,))
    result = cursor.fetchone()
    conn.close()
    return result is not None




def check_working_directory(file_name, section):
    """
    Check if the corresponding working directory exists for the processed file.

    :param file_name: The name of the file to check.
    :param section: The selected section.
    :return: True if the working directory exists, False otherwise.
    """
    working_dir = Path(f"./analysis_workspace/{section}/{file_name.split('.')[0]}")
    return working_dir.exists() and working_dir.is_dir()  # Returns True if the directory exists
