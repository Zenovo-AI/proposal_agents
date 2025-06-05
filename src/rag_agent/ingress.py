"""
Ingests and processes document files or web links, extracting content and storing it in the database.

- `ingress_file_doc`: Main function to process files or web links, extract text, insert metadata into the database, and process data using RAG.
"""

from fastapi import HTTPException # type: ignore
from document_processor import DocumentProcessor
from database.db_helper import insert_file_metadata, open_tenant_db_connection
from cloud_storage.do_spaces import upload_file
from rag_agent.rag_instance import RAGManager
import traceback
import logging
from models.users_utilities import lookup_user_db_credentials

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger("pdfminer").setLevel(logging.ERROR)


process_document = DocumentProcessor()

# async def ingress_file_doc(file_name: str, file_path: str = None, web_links: list = None):
#     process_document = DocumentProcessor()

#     try:
#         # Connect to the database
#         conn = sqlite3.connect("files.db", check_same_thread=False)
#         cursor = conn.cursor()

#         # Check if file already exists in the database
#         if file_path:
#             cursor.execute("SELECT file_name FROM documents WHERE file_name = ?", (file_name,))
#             if cursor.fetchone():
#                 return {"error": f"File '{file_name}' already exists."}

#         # Check if web links already exist in the database
#         if web_links:
#             for link in web_links:
#                 cursor.execute("SELECT file_name FROM documents WHERE file_name = ?", (link,))
#                 if cursor.fetchone():
#                     return {"error": f"Web link '{link}' already exists."}

#         # Extract content
#         text_content = []

#         if file_path:
#             file_path_str = str(file_path)
#             if file_path_str.endswith(".pdf"):
#                 extracted_text = process_document.extract_text_and_tables_from_pdf(file_path_str)
#                 if extracted_text:
#                     text_content.append(extracted_text)
#             elif file_path_str.endswith(".txt"):
#                 text_content.append(process_document.extract_txt_content(file_path_str))
#             else:
#                 return {"error": "Unsupported file format."}

#         if web_links:
#             for link in web_links:
#                 web_content = process_document.process_webpage(link)
#                 if web_content:
#                     text_content.append(web_content)

#         if not text_content:
#             return {"error": "No valid content extracted from file or web links."}

#         # Insert into database
#         for content in text_content:
#             insert_file_metadata(file_name, content)

#         # RAG processing
#         working_dir = Path("./analysis_workspace")
#         working_dir.mkdir(parents=True, exist_ok=True)

#         rag = await RAGFactory.create_rag(str(working_dir))
#         await rag.ainsert(text_content)

        # for file_path in working_dir.glob("*"):
        #     if file_path.is_file():
        #         upload_file(file_path)

    #     print(f"File '{file_name}' processed and inserted successfully!")
    #     return {"success": True}

    # except Exception as e:
    #     traceback.print_exc()
    #     return {"error": str(e)}

    # finally:
    #     conn.close()


async def ingress_file_doc(file_name: str, file_path: str = None, web_links: list = None, overwrite: bool = False, session_data: dict = None):
    print("📥 Starting ingress_file_doc")
    try:
        process_document = DocumentProcessor()
        # Extract email from session data
        email = session_data.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Lookup DB credentials once
        db_user, db_name, db_password, working_dir = lookup_user_db_credentials(email)
        logging.info("Password for user %s: %s", db_user, db_password, db_name)
        with open_tenant_db_connection(db_user,db_name, db_password) as conn:
            if not conn:
                raise HTTPException(status_code=500, detail="Failed to connect to tenant database")
        logging.info("✅ Connection and processor created")
        cursor = conn.cursor()
    except Exception as e:
        traceback.print_exc()
        return {"error": f"Initialization failed: {str(e)}"}
    try:
        if file_path:
            print(f"🔎 Checking if file '{file_name}' exists in DB...")
            cursor.execute("SELECT file_name FROM documents WHERE file_name = %s", (file_name,))
            existing = cursor.fetchone()
            print(f"🧾 File exists in DB: {existing}")
            if existing and not overwrite:
                print(f"❌ File '{file_name}' already exists. Returning early.")
                return {"error": f"File '{file_name}' already exists."}
            elif existing and overwrite:
                print(f"♻️ Overwriting file '{file_name}' in DB.")
                cursor.execute("DELETE FROM documents WHERE file_name = %s", (file_name,))
                conn.commit()

        # Check if web links already exist in the database
        if web_links:
            for link in web_links:
                cursor.execute("SELECT file_name FROM documents WHERE file_name = %s", (link,))
                if cursor.fetchone():
                    return {"error": f"Web link '{link}' already exists."}

        text_content = []
        document_names = []

        if file_path:
            file_path_str = str(file_path)
            if file_path_str.endswith(".pdf"):
                extracted_text = process_document.extract_text_and_tables_from_pdf(file_path_str)
                if extracted_text:
                    text_content.append(extracted_text)
                    document_names.append(file_name)
            elif file_path_str.endswith(".txt"):
                extracted_text = process_document.extract_txt_content(file_path_str)
                if extracted_text:
                    text_content.append(extracted_text)
                    document_names.append(file_name)
            else:
                return {"error": "Unsupported file format."}

        if web_links:
            for link in web_links:
                web_content = process_document.process_webpage(link)
                if web_content:
                    text_content.append(web_content)
                    document_names.append(link)

        logging.debug("📝 Extracted document_names: %s", document_names)

        if not text_content:
            return {"error": "No valid content extracted from file or web links."}

        for i, content in enumerate(text_content):
            insert_file_metadata(document_names[i], file_name, content, db_user, db_name, db_password)
            print("📝 Extracted content (truncated):", [c[:100] for c in text_content])
            logging.debug("📝 Extracted content (truncated): %s", [c[:100] for c in text_content])


        rag = await RAGManager.get_or_create_rag(db_user, db_name, db_password, working_dir)

        if rag is None:
            raise RuntimeError("RAG not initialized.")
        
        rag.chunk_entity_relation_graph.embedding_func = rag.embedding_func
        await rag.ainsert(text_content, ids=document_names)

        print(f"File '{file_name}' processed and inserted successfully!")
        logging.info("File '%s' processed and inserted successfully!", file_name)
        return {"success": True}

    except Exception as e:
        traceback.print_exc()
        return {"error": f"Initialization failed: {str(e)}"}

    finally:
        if conn:
            conn.close()

# async def ingress_file_doc(file_name: str, file_path: str = None, web_links: list = None):
#     process_document = DocumentProcessor()

#     try:
#         # Connect to the database
#         conn = sqlite3.connect("files.db", check_same_thread=False)
#         cursor = conn.cursor()

#         # Check if file already exists in the database
#         if file_path:
#             cursor.execute("SELECT file_name FROM documents WHERE file_name = ?", (file_name,))
#             if cursor.fetchone():
#                 return {"error": f"File '{file_name}' already exists."}

#         # Check if web links already exist in the database
#         if web_links:
#             for link in web_links:
#                 cursor.execute("SELECT file_name FROM documents WHERE file_name = ?", (link,))
#                 if cursor.fetchone():
#                     return {"error": f"Web link '{link}' already exists."}

#         # Extract content and prepare document IDs
#         text_content = []
#         doc_ids = []

#         if file_path:
#             file_path_str = str(file_path)
#             if file_path_str.endswith(".pdf"):
#                 extracted_text = process_document.extract_text_and_tables_from_pdf(file_path_str)
#                 if extracted_text:
#                     text_content.append(extracted_text)
#                     doc_ids.append(file_name)  # Use file name as ID
#             elif file_path_str.endswith(".txt"):
#                 extracted_text = process_document.extract_txt_content(file_path_str)
#                 if extracted_text:
#                     text_content.append(extracted_text)
#                     doc_ids.append(file_name)
#             else:
#                 return {"error": "Unsupported file format."}

#         if web_links:
#             for link in web_links:
#                 web_content = process_document.process_webpage(link)
#                 if web_content:
#                     text_content.append(web_content)
#                     doc_ids.append(link)  # Use the link itself as ID

#         if not text_content:
#             return {"error": "No valid content extracted from file or web links."}

#         # Insert into database
#         for i, content in enumerate(text_content):
#             insert_file_metadata(doc_ids[i], file_name, content)

#         # RAG processing
#         working_dir = Path("./analysis_workspace")
#         working_dir.mkdir(parents=True, exist_ok=True)

#         rag = await RAGFactory.create_rag(str(working_dir))

#         # Insert into RAG with associated document IDs
#         await rag.ainsert(text_content, ids=doc_ids)

#         # Upload to remote (optional, based on original logic)
#         for file_path in working_dir.glob("*"):
#             if file_path.is_file():
#                 upload_file(file_path)

#         print(f"File '{file_name}' processed and inserted successfully!")
#         return {"success": True}

#     except Exception as e:
#         traceback.print_exc()
#         return {"error": str(e)}

#     finally:
#         conn.close()
