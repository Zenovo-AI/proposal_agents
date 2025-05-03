"""
Ingests and processes document files or web links, extracting content and storing it in the database.

- `ingress_file_doc`: Main function to process files or web links, extract text, insert metadata into the database, and process data using RAG.
"""


from pathlib import Path
import sqlite3
from src.document_processor import DocumentProcessor
from src.db_helper import insert_file_metadata
from src.cloud_storage.do_spaces import upload_file
from src.rag_agent.lightrag_setup import RAGFactory
import traceback

process_document = DocumentProcessor()

async def ingress_file_doc(file_name: str, file_path: str = None, web_links: list = None):
    process_document = DocumentProcessor()

    try:
        # Connect to the database
        conn = sqlite3.connect("files.db", check_same_thread=False)
        cursor = conn.cursor()

        # Check if file already exists in the database
        if file_path:
            cursor.execute("SELECT file_name FROM documents WHERE file_name = ?", (file_name,))
            if cursor.fetchone():
                return {"error": f"File '{file_name}' already exists."}

        # Check if web links already exist in the database
        if web_links:
            for link in web_links:
                cursor.execute("SELECT file_name FROM documents WHERE file_name = ?", (link,))
                if cursor.fetchone():
                    return {"error": f"Web link '{link}' already exists."}

        # Extract content
        text_content = []

        if file_path:
            file_path_str = str(file_path)
            if file_path_str.endswith(".pdf"):
                extracted_text = process_document.extract_text_and_tables_from_pdf(file_path_str)
                if extracted_text:
                    text_content.append(extracted_text)
            elif file_path_str.endswith(".txt"):
                text_content.append(process_document.extract_txt_content(file_path_str))
            else:
                return {"error": "Unsupported file format."}

        if web_links:
            for link in web_links:
                web_content = process_document.process_webpage(link)
                if web_content:
                    text_content.append(web_content)

        if not text_content:
            return {"error": "No valid content extracted from file or web links."}

        # Insert into database
        for content in text_content:
            insert_file_metadata(file_name, content)

        # RAG processing
        working_dir = Path("./analysis_workspace")
        working_dir.mkdir(parents=True, exist_ok=True)

        rag = RAGFactory.create_rag(str(working_dir))
        rag.insert(text_content)

        for file_path in working_dir.glob("*"):
            if file_path.is_file():
                upload_file(file_path)

        print(f"File '{file_name}' processed and inserted successfully!")
        return {"success": True}

    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}

    finally:
        conn.close()
