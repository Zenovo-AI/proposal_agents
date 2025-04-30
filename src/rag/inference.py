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
import time
import streamlit as st
from rag.do_spaces import download_all_files
from rag.lightrag_setup import RAGFactory
from src.ingress import ingress_file_doc
from do_spaces import download_all_files
from lightrag import QueryParam
from langchain_openai import OpenAI



def generate_explicit_query(query):
    """Expands the user query and merges expanded queries into a single, explicit query."""
    llm = OpenAI(temperature=0, openai_api_key=st.session_state.openai_api_key)

    prompt = f"""
    Given the following vague query:

    '{query}'

    Expand this query into **seven structured subqueries** that break down the proposal into detailed components.
    Ensure that the query includes **specific details** such as:
    - The sender's company name, address, email, and phone number.
    - The recipient’s name, position, organization, and address.
    - A structured breakdown of the proposal, including scope of work, compliance, pricing, experience, and additional documents.

    Example:

    **Original Query:** "Can you write a proposal based on the requirements in the RFQ?"

    **Expanded Queries:**
    1. "Provide a formal header section with the sender's full company details (name, address, email, phone) and the recipient's details (name, position, organization, address)."
    2. "Write a professional opening paragraph that introduces the company and states the purpose of the proposal."
    3. "Describe the scope of work, breaking it into detailed sections for each service category (e.g., borehole rehabilitation and new drilling)."
    4. "Provide a clear breakdown of pricing, including cost per lot and total project cost, specifying currency and payment terms."
    5. "Outline a detailed project plan and timeline, including key milestones and deliverables."
    6. "List all required compliance details, including adherence to RFQ terms, delivery timelines, insurance coverage, and taxation requirements."
    7. "Outline the company's experience and qualifications, listing past projects, certifications, and key personnel expertise."
    8. "List all necessary additional documents, such as bidder’s statement, vendor profile form, and statement of confirmation, etc."

    **Final Explicit Query:**  
    "Can you write a proposal based on the requirements in the RFQ, including:  
    (1) A formal header with sender and recipient details,  
    (2) An introduction stating the company’s expertise and purpose of the proposal,  
    (3) A detailed scope of work for each service component,  
    (4) A structured pricing breakdown with currency and payment terms,  
    (5) A detailed project plan and timeline with milestones, and
    (6) A section on compliance, including delivery, insurance, and taxation,  
    (7) A section on experience and qualifications, highlighting past projects and key personnel, and  
    (8) A section listing all required additional documents."

    Now, generate an explicit query for:

    '{query}'
    """

    response = llm.invoke(prompt)
    return response.strip()


proposal_prompt = """
You are an expert proposal assistant. Generate a comprehensive proposal using ONLY information from these sources:
---Knowledge Base---
{context_data}

---Response Rules---
1. Do NOT use Markdown or special characters like `**`, `#`, or `-`. Use plain text formatting only.
2. Structure the proposal with clear section titles, separated by newlines.
3. NO placeholders like [Company Name]; use real data from the knowledge base or note it as missing if not found.
4. Use a professional tone.
5. SKIP COMPLIMENTARY CLOSINGS OR VALEDICTIONS
6. SKIP SALUTATION

---Proposal Structure---
LETTERHEAD &  
- Display brand name, reg/vat numbers, and contact info  

INTRODUCTION 
- Greet the recipient briefly and outline purpose

PROJECT SCOPE  
- Detailed scope from the knowledge base  

EXCLUSIONS  
- List any out-of-scope items if mentioned  

DELIVERABLES  
- Clearly outline what will be delivered  

COMMERCIAL 
- Provide cost breakdown and payment terms in a tabular form  

SCHEDULE  
- Timeline or milestone details 

COMPLIANCE SECTION
- List all required compliance details, including adherence to RFQ terms, delivery timelines, insurance coverage, and taxation requirements.


EXPERIENCE & QUALIFICATIONS
- Outline the company's experience and qualifications, listing past projects, certifications, and key personnel expertise.

ADDITIONAL DOCUMENTS REQUIRED 
- List all necessary additional documents, such as bidder’s statement, vendor profile form, and statement of confirmation, etc.

CONCLUSION
- Summarize key points   

Yours Sincerely,
- Provide sign-off lines referencing Directors or authorized persons.

Current RFQ Requirements: {query}
"""


custom_prompt = """
You are an **expert assistant specializing in proposal writing** for procurement bids. Your role is to **generate professional, structured, and detailed proposals**. 

**IMPORTANT RULES:**  
- **DO NOT HALLUCINATE**: Only use the provided RFQ details and relevant organizational data.  
- **IF INFORMATION IS MISSING**: Clearly state "Information not available in the RFQ document."  
- **ENSURE A FORMAL & PROFESSIONAL TONE.**  

**PROPOSAL STRUCTURE:**  


    - Include **company name, address, contact details, date, and RFQ reference number**.  
    - Include the **recipient’s name, organization, and address**.  

    **Executive Summary**  
    - Provide a brief **introduction** about the company.  
    - Summarize the **key services offered** in response to the RFQ.  

    **Scope of Work**  
    - Outline **each deliverable** as specified in the RFQ.  
    - Provide **technical details, compliance requirements, and execution strategy**.  

    **Technical Approach & Methodology**  
    - Describe the **step-by-step process** for project execution.  
    - Highlight **tools, technologies, and quality assurance methods**.  

    **Project Plan & Timeline**  
    - Include a **table of milestones** with estimated completion dates.  
    - Ensure alignment with **RFQ deadlines and compliance requirements**.  

    **Pricing & Payment Terms**  
    - Provide a structured **cost breakdown per project phase**.  
    - Outline **payment terms, tax exemptions, and invoicing policies**.  

    **Company Experience & Past Performance**  
    - Showcase **previous projects, certifications, and industry expertise**.  
    - List **relevant clients, testimonials, and references**.  

    **Compliance & Certifications**  
    - Confirm **adherence to procurement regulations, environmental standards, and safety policies**.  
    - Attach **insurance documentation, licensing, and regulatory approvals**.  

    **Attachments & Supporting Documents**  
    - Ensure **all required forms, legal documents, and compliance matrices** are attached.   
---  

Now, generate a **full proposal** using the structured format above, ensuring precision, professionalism, and clarity.
"""


@st.cache_resource
def get_db_connection():
    return sqlite3.connect("files.db", check_same_thread=False)

def generate_answer():
    """Generates an answer when the user enters a query and presses Enter."""
    query = st.session_state.query_input
    conn = get_db_connection()  # Get user query from session state
    if not query:
        return  # Do nothing if query is empty

    with st.spinner("Expanding query..."):
        expanded_queries = generate_explicit_query(query)
        full_prompt = f"{proposal_prompt}\n\nUser Query: {expanded_queries}"

    with st.spinner("Generating answer..."):
        try:
            working_dir = Path("./analysis_workspace")
            # working_dir.mkdir(parents=True, exist_ok=True)

            download_all_files(working_dir)

            rag = RAGFactory.create_rag(str(working_dir))  
            # ✅ Authenticate and initialize GCS
            # gcs_fs = get_gcs_fs()
            # print("Service Account Authenticated")

            # # ✅ Define bucket and sync files
            # bucket_name = "lightrag-bucket"
            # prefix = "analysis_workspace"
            # local_dir = sync_gcs_to_local(gcs_fs, bucket_name, prefix)
            # print(f"Files synced to {local_dir}")

            # rag = RAGFactory.create_rag(str(local_dir))

            # Send combined query to RAG
            response = rag.query(full_prompt, QueryParam(mode="hybrid"))

            # Store in chat history
            st.session_state.chat_history.append(("You", query))
            st.session_state.chat_history.append(("Bot", response))
            
            # Store response as proposal text
            cleaned_response = clean_text(response)
            st.session_state.proposal_text = cleaned_response
            
        except Exception as e:
            st.error(f"Error retrieving response: {e}")

    # Reset query input to allow further queries
    st.session_state.query_input = ""


def process_files_and_links(files, web_links, section):
    with st.spinner("Processing..."):
        for uploaded_file in files:
            process_file(uploaded_file, section, web_links)  # ✅ Call function directly
    st.session_state["files_processed"] = True

def process_file(uploaded_file, section, web_links):
    try:
        file_name = uploaded_file.name
        st.session_state["file_name"] = file_name
        # Use pathlib to define the file path
        temp_dir = Path("./temp_files")
        temp_dir.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists
        
        # Define the file path
        file_path = temp_dir / file_name  # Concatenate the directory path and file name

        # Save file locally for processing
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())

        # Call the function with correct arguments
        try:
            response = ingress_file_doc(file_name, file_path, web_links or [], section)
            if "error" in response:
                st.error(f"File processing error: {response['error']}")
            else:
                placeholder = st.empty()
                placeholder.success(f"File '{file_name}' processed successfully!")
                time.sleep(5)
                placeholder.empty()
        except Exception as e:
            st.error(f"Unexpected error: {e}")

    except Exception as e:
        st.error(f"Connection error: {e}")

