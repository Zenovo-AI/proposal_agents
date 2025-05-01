import base64
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
import re
import sqlite3
import time
import traceback
import numpy as np
import streamlit as st
from constant import SECTION_KEYWORDS, select_section
from db_helper import check_if_file_exists_in_section, check_working_directory, delete_file, get_uploaded_sections, initialize_database
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from inference import process_files_and_links
from google_docs_helper import GoogleDocsHelper, GoogleDriveAPI
from auth import auth_flow, logout, validate_session
from utils import clean_text

auth_cache_dir = Path(__file__).parent / "auth_cache"

credentials_path = auth_cache_dir / "credentials.json"
auth_status_path = auth_cache_dir / "auth_success.txt"
    
    

def initialize_session_state():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "initialized" not in st.session_state:
        initialize_database()
        st.session_state.initialized = True
    if "proposal_text" not in st.session_state: 
        st.session_state.proposal_text = ""
    if "google_drive_authenticated" not in st.session_state:
        st.session_state.google_drive_authenticated = False
    if "show_gdrive_form" not in st.session_state:
        st.session_state.show_gdrive_form = False
    if "google_drive_link" not in st.session_state:
        st.session_state.google_drive_link = ""
    if "pdf_file_name" not in st.session_state:
        st.session_state.pdf_file_name = ""
    if "show_gdocs_form" not in st.session_state:
        st.session_state.show_gdocs_form = False
    if "doc_file_name" not in st.session_state:
        st.session_state.doc_file_name = ""
    if "proposal_text" not in st.session_state:
        st.session_state.proposal_text = ""
    if "upload_triggered" not in st.session_state:
        st.session_state.upload_triggered = False
    if "query_input" not in st.session_state:
        st.session_state.query_input = ""


# Initialize API key from secrets
if "openai_api_key" not in st.session_state:
    try:
        st.session_state.openai_api_key = st.secrets["OPENAI_API_KEY"]
    except KeyError:
        st.error("OpenAI API key not found in secrets.toml")



def main():
    # Check authentication
    credentials_exist = credentials_path.exists() and auth_status_path.exists()

    if not credentials_exist:
        credentials = auth_flow()  # Run authentication flow
        if not credentials:
            st.error("Please Authenticate, so you can use the App!...")
            return  # Stop execution if authentication fails

    st.title("Proposal and Chatbot System")
    st.write("Upload a document and ask questions based on structured knowledge retrieval.")
    
    initialize_session_state()
    validate_session()

    # List of sections
    sections = list(SECTION_KEYWORDS.values())

    # Ensure session state has a default section
    if "current_section" not in st.session_state:
        st.session_state.current_section = sections[0]

    # Sidebar: Select section
    selected_section = st.sidebar.selectbox(
        "Select a document section:", 
        options=sections, 
        key="main_nav", 
        index=sections.index(st.session_state.current_section)
    )
    st.session_state.current_section = selected_section

    # Get section and table name
    section, table_name = select_section(selected_section)

    # File uploader widget
    files = st.sidebar.file_uploader("Upload documents", accept_multiple_files=True, type=["pdf", "txt"])

    # Store uploaded file name in session state
    for file in files:
        st.session_state["file_name"] = file.name

    # Web links input
    web_links = st.sidebar.text_area("Enter web links (one per line)", key="web_links")

    # Ensure files_processed is in session state
    if "files_processed" not in st.session_state:
        st.session_state["files_processed"] = False


    # Process files and links if present
    if (files or web_links) and not st.session_state["files_processed"]:
        for file in files:
            file_name = file.name
    
    # if (files or web_links) and not st.session_state["files_processed"]:

            # Check if file exists in database or working directory
            file_in_db = check_if_file_exists_in_section(file_name, section)
            dir_exists = check_working_directory(file_name, section)

            if file_in_db and dir_exists:
                placeholder = st.empty()
                placeholder.warning(f"The file '{file_name}' has already been processed and exists in the '{section}' section.")
                time.sleep(5)
                placeholder.empty()
            else:
                placeholder = st.empty()
                placeholder.write("🔄 Processing files and links...")
                time.sleep(5)
                placeholder.empty()

                # Process the files and links
                process_files_and_links(files, web_links, section)  

                placeholder.write("✅ Files and links processed!")
                time.sleep(5)  
                placeholder.empty()


    # Reset processing state and delete working directory
    if st.sidebar.button("Reset Processing", key="reset"):
        delete_all()  # Remove from DigitalOcean
        # Clear session state except for initialized state
        keys_to_keep = {"initialized"}
        for key in list(st.session_state.keys()):
            if key not in keys_to_keep:
                del st.session_state[key]

        # Reset processing flag
        st.session_state["files_processed"] = False

        # Define the working directory
        working_dir = Path("./analysis_workspace")

        # Delete the working directory if it exists
        if working_dir.exists() and working_dir.is_dir():
            import shutil
            shutil.rmtree(working_dir)
            st.sidebar.success("Processing reset! The working directory has been deleted.")
            st.rerun()
        else:
            st.sidebar.warning("No working directory found to delete.")
    

    
    if st.sidebar.button("📝 Save Proposal to Google Drive"):
        if "drive_service" in st.session_state:
            del st.session_state.drive_service

        try:
            credentials = json.loads(credentials_path.read_text())  # Load main JSON

            # Decode the nested JSON inside "token"
            if isinstance(credentials.get("token"), str):
                credentials["token"] = json.loads(credentials["token"])

            # Ensure the required keys exist
            required_keys = {"client_id", "client_secret", "refresh_token"}
            if not isinstance(credentials["token"], dict) or not required_keys.issubset(credentials["token"].keys()):
                st.error("❗ Invalid credentials file. Please log in again.")
                st.stop()

            # ✅ Initialize services
            creds = Credentials.from_authorized_user_info(credentials['token'])
            docs_service = build("docs", "v1", credentials=creds)
            drive_service = build("drive", "v3", credentials=creds)
            drive_api = GoogleDriveAPI(drive_service)

            # ✅ Validate proposal content
            if not st.session_state.get("proposal_text"):
                st.error("❗ Generate a proposal before uploading!")
                time.sleep(2)
                st.rerun()

            # ✅ Retrieve the Google Docs template
            template_name = "ProposalTemplate"
            template_id = drive_api.get_template_id(template_name)
            if not template_id:
                raise ValueError(f"Error: Proposal template '{template_name}' not found in drive. Please verify the template exists.")

            # ✅ Organize Google Drive folders
            with st.spinner("Organizing Google Drive..."):
                proposals_folder_id = drive_api.create_folder("Proposals")
                date_folder_id = drive_api.create_folder(
                    datetime.now().strftime("%Y-%m-%d"),
                    parent_folder_id=proposals_folder_id
                )

            # ✅ Create a new document from the template
            with st.spinner("Generating professional document..."):
                docs_helper = GoogleDocsHelper(docs_service, drive_service)
                replacements = parse_proposal_content(st.session_state.proposal_text)
                print("🔍 DEBUG: Replacements Dictionary")
                for key, value in replacements.items():
                    print(f"{key}: {value[:100]}...")

                new_google_doc_id = docs_helper.create_from_template(
                    template_id=template_id,
                    replacements=replacements,
                    document_name=f"Proposal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )

            # ✅ Move the new document to the correct folder
            drive_service.files().update(
                fileId=new_google_doc_id,
                addParents=date_folder_id,
                removeParents='root'
            ).execute()

            
            st.sidebar.markdown(f"✅ Upload Successful! [View Document](https://docs.google.com/document/d/{new_google_doc_id}/view)")
            # time.sleep(10)

            # st.rerun()

        except Exception as e:
            st.error(f"🚨 Document creation failed: {str(e)}")
            st.error(traceback.format_exc())

        
            
    # Logout
    if st.sidebar.button("Logout", key="main_logout"):
        st.session_state.force_refresh = True
        logout()


    # Input field with automatic query execution on Enter
    st.text_input("Ask a question about the document:", key="query_input", on_change=generate_answer)

    # Display chat history
    for role, message in st.session_state.chat_history:
        with st.chat_message("user" if role == "You" else "assistant"):
            st.write(message)

    # Sidebar: Uploaded files display
    st.sidebar.write("### Uploaded Files")
    try:
        conn = sqlite3.connect("files.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute(f'SELECT file_name FROM "{table_name}";')
        uploaded_files_list = [file[0] for file in cursor.fetchall()]

        if uploaded_files_list:
            for file_name in uploaded_files_list:
                delete_key = f"delete_{table_name}_{file_name}"
                col1, col2 = st.sidebar.columns([3, 1])
                with col1:
                    st.sidebar.write(file_name)
                with col2:
                    if st.sidebar.button("Delete", key=delete_key):
                        try:
                            delete_file(file_name, table_name)
                            st.sidebar.success(f"File '{file_name}' deleted successfully!")
                        except Exception as e:
                            st.error(f"Failed to delete file '{file_name}': {e}")
        else:
            st.sidebar.info("No files uploaded for this section.")
    except Exception as e:
        st.sidebar.error(f"Failed to retrieve files: {e}")

    # Sidebar: Breadcrumb display
    uploaded_sections = get_uploaded_sections(SECTION_KEYWORDS)
    if "uploaded_sections" not in st.session_state:
        st.session_state.uploaded_sections = set()

    if files:
        st.session_state.uploaded_sections.add(section)

    if st.session_state.uploaded_sections:
        breadcrumb_text = " > ".join(sorted(st.session_state.uploaded_sections))
        st.sidebar.info(f"📂 Sections with uploads: {breadcrumb_text}")
        
if __name__ == "__main__":
    main()