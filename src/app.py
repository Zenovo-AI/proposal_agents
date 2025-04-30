import base64
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
import re
import sqlite3
import gcsfs
from google.oauth2 import service_account
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
        st.stop()


# Helper Function to Clean and Parse JSON
def clean_and_parse_json(raw_json):
    try:
        fixed_json = raw_json.replace("{{", "{").replace("}}", "}")
        return json.loads(fixed_json)
    except json.JSONDecodeError as e:
        logging.error(f"JSON parsing error: {e}. Raw data: {raw_json}")
        return None


def extract_section(proposal_text, section_name):
    """Robust section extraction with subsections handling"""
    lines = proposal_text.split('\n')
    content = []
    capture = False
    subsection_pattern = re.compile(r'^\s*(LOT \d+:|•|\d+\.)\s*', re.IGNORECASE)
    
    # Define section names that mark the end of the current section
    end_sections = ['Project Scope', 'Exclusions', 'Deliverables', 'Commercial', 'Schedule', 'Compliance Section', 'Experience & Qualifications', 'Additional Documents Required', 'Conclusion', 'Yours Sincerely']
    # Build regex pattern to match any of these sections at line start
    end_pattern = re.compile(
        r'^\s*({})\b.*'.format(  # \b ensures whole word match
            '|'.join(re.escape(section) for section in end_sections)
        ),
        re.IGNORECASE
    )

    for line in lines:
        # Normalize line for matching
        clean_line = line.strip().lower().replace('_', ' ').replace('/', ' ')
        
        # Start capturing at target section (exact match check)
        if section_name.lower() == clean_line and not capture:
            capture = True
            continue  # Skip the section header line itself
            
        if capture:
            # Stop at next main section (using original line for pattern matching)
            if end_pattern.match(line.strip()):
                break
                
            # Preserve subsections and lists with proper formatting
            if subsection_pattern.match(line):
                content.append('\n' + line.strip())
            elif line.strip():
                content.append(line.strip())

    return '\n'.join(content).strip()

    

# Parse generated content into template structure
def parse_proposal_content(proposal_text):
    """Extracts proposal sections with proper placeholder keys"""
    parsed_data = {
        "INTRODUCTION_CONTENT": extract_section(proposal_text, "Introduction"),
        "PROJECT_SCOPE_CONTENT": extract_section(proposal_text, "Project Scope"),
        "EXCLUSIONS_CONTENT": extract_section(proposal_text, "Exclusions"),
        "DELIVERABLES_CONTENT": extract_section(proposal_text, "Deliverables"),
        "COMMERCIAL_CONTENT": extract_section(proposal_text, "Commercial"),
        "SCHEDULE_CONTENT": extract_section(proposal_text, "Schedule"),
        "COMPLIANCE_CONTENT": extract_section(proposal_text, "Compliance Section"),
        "EXPERIENCE_CONTENT": extract_section(proposal_text, "Experience & Qualifications"),
        "ADDITIONAL_DOCUMENTS_CONTENT": extract_section(proposal_text, "Additional Documents Required"),
        "CONCLUSION_CONTENT": extract_section(proposal_text, "Conclusion"),
        "SIGN_OFF_CONTENT": extract_section(proposal_text, "Yours Sincerely,")    
    }

    # 🔍 DEBUG: Log extracted content before sending it for replacement
    print("\n--- 🔍 DEBUG: Parsed Proposal Content ---")
    for key, value in parsed_data.items():
        print(f"{key}: {value[200:]}...")  # Print first 200 characters for preview
    print("--- 🔍 End of Parsed Content ---\n")

    return parsed_data


def sync_gcs_to_local(gcs_fs, gcs_bucket, gcs_prefix):
    """Ensure all files from GCS are downloaded to 'analysis_workspace'"""
    local_cache = Path("./analysis_workspace")
    gcs_path = f"{gcs_bucket}/{gcs_prefix}".rstrip("/")

    # Ensure the local directory exists
    local_cache.mkdir(parents=True, exist_ok=True)

    try:
        gcs_files = gcs_fs.ls(gcs_path)
        print(f"\n🔍 Found {len(gcs_files)} files in GCS: {gcs_files}")  # Debugging

        if not gcs_files:
            raise FileNotFoundError(f"GCS path '{gcs_path}' is empty")

    except Exception as e:
        raise FileNotFoundError(f"Error accessing GCS path '{gcs_path}': {e}")

    print(f"\n🔍 Found {len(gcs_files)} files in GCS:")
    for f in gcs_files:
        print(f"   - {f}")

    print("\n🔄 Checking local sync...\n")

    downloaded_files = []

    for blob_path in gcs_files:
        # Skip directories
        if blob_path.endswith("/"):
            print(f"⏩ Skipping directory: {blob_path}")
            continue  # Skip to the next file

        local_path = local_cache / Path(blob_path).name
        try:
            # Always download if the local folder is empty
            if not any(local_cache.iterdir()):
                download = True
            else:
                # Check timestamps
                blob_info = gcs_fs.info(blob_path)
                gcs_last_modified = datetime.fromisoformat(blob_info["updated"]).astimezone(timezone.utc)

                if local_path.exists():
                    local_last_modified = datetime.fromtimestamp(local_path.stat().st_mtime, tz=timezone.utc)
                    download = local_last_modified < gcs_last_modified
                else:
                    download = True

            if download:
                # Delete the existing file before writing new content
                if local_path.exists():
                    local_path.unlink()

                with gcs_fs.open(blob_path, "rb") as remote_file:
                    content = remote_file.read()
                    local_path.write_bytes(content)
                    downloaded_files.append(local_path)
                    print(f"✅ Downloaded: {local_path} ({len(content)} bytes)")
                    time.sleep(1)  # Reduce throttling

            else:
                print(f"⏩ Skipping (up-to-date): {blob_path}")

        except Exception as e:
            print(f"❌ Error downloading {blob_path}: {e}")

    # Print local folder content
    local_files = list(local_cache.glob("*"))
    print(f"\n📂 Local 'analysis_workspace' now contains {len(local_files)} files:")
    for f in local_files:
        print(f"   - {f.name}")

    if len(downloaded_files) == len(gcs_files) - 1:  # Subtract 1 because we skip the directory
        print("\n✅ All files downloaded successfully.\n")
    else:
        print("\n⚠️ Some files are missing! Check logs.\n")

    return local_cache


# Authenticate with GCS
def get_gcs_fs():
    """Ensure GCS authentication is working"""
    try:
        service_account_b64 = st.secrets.gcs.service_account_b64
        service_account_info = json.loads(base64.b64decode(service_account_b64).decode())

        # Create credentials
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=[
                "https://www.googleapis.com/auth/devstorage.full_control",
                "https://www.googleapis.com/auth/cloud-platform"
            ]
        )

        gcs_fs = gcsfs.GCSFileSystem(token=credentials)
        return gcs_fs
    except Exception as e:
        st.error(f"GCS Authentication Failed: {str(e)}")
        st.stop()



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