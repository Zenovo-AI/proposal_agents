"""
This module handles file processing in a Streamlit application, where users can upload files
and links for processing. It processes the files by saving them locally and passing them to
another function (`ingress_file_doc`) that handles the business logic for each file.

Key Features:
- Uploading and saving files locally in a temporary directory.
- Calling an external function (`ingress_file_doc`) to process each uploaded file.
- Handling multiple files at once, as well as accompanying web links, to process them in the 
  specified section.
- Error handling to catch and display both known and unexpected errors during file processing.
- Providing user feedback via Streamlit’s spinner and success/error messages to guide users.

The module uses `pathlib` to manage file paths and `time.sleep` for handling short delays to
provide feedback to the user. File names and paths are stored in `st.session_state` for reference 
across Streamlit sessions.

Note:
- `process_files_and_links` iterates through the list of uploaded files and web links, invoking
  the `process_file` function for each file.
- The `process_file` function saves the file locally, calls `ingress_file_doc` for processing,
  and handles any errors that occur during the process.
- Temporary files are stored in the `./temp_files` directory, which is created if it doesn't exist.

Ensure that `ingress_file_doc` is correctly defined and handles the file processing logic. This
module provides a structured approach for handling file uploads and processing them in a web
application environment.
"""


from pathlib import Path
import traceback
from src.cloud_storage.do_spaces import download_all_files
from src.rag.lightrag_setup import RAGFactory
from src.rag.ingress import ingress_file_doc
from lightrag import QueryParam
from src.utils import clean_text, generate_explicit_query, proposal_prompt


def generate_answer(user_query, chat_history=None):
    """Generates an answer from the chatbot based on user input."""

    if not user_query:
        return None

    try:
        # Step 1: Expand the query
        expanded_queries = generate_explicit_query(user_query)
        full_prompt = f"{proposal_prompt()}\n\nUser Query: {expanded_queries}"

        # Step 2: Setup working directory and download files
        working_dir = Path("./analysis_workspace")
        download_all_files(working_dir)

        # Step 3: Query RAG
        rag = RAGFactory.create_rag(str(working_dir))
        response = rag.query(full_prompt, QueryParam(mode="hybrid"))

        # Step 4: Store chat history (if provided)
        if chat_history is not None:
            chat_history.append(("You", user_query))
            chat_history.append(("Bot", response))

        # Step 5: Clean response and return
        return clean_text(response)

    except Exception as e:
        traceback.print_exc()
        return f"Error retrieving response: {e}"



def process_files_and_links(files, web_links, section):
    results = []
    for uploaded_file in files:
        result = process_file(uploaded_file, section, web_links)
        results.append(result)
    return {"files_processed": True, "results": results}


def process_file(file_name, file_content_bytes, web_links=None):
    """Processes a file and optional web links for ingestion."""

    try:
        # Save file to temporary location
        temp_dir = Path("./temp_files")
        temp_dir.mkdir(parents=True, exist_ok=True)
        file_path = temp_dir / file_name
        with open(file_path, "wb") as f:
            f.write(file_content_bytes)

        # Ingest file and links
        response = ingress_file_doc(file_name, file_path=str(file_path), web_links=web_links or [])

        if "error" in response:
            return f"File processing error: {response['error']}"
        else:
            return f"File '{file_name}' processed successfully!"

    except Exception as e:
        traceback.print_exc()
        return f"Unexpected error during processing: {str(e)}"
