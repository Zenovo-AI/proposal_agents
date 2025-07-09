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

import json
import logging
from pathlib import Path
import traceback

from fastapi import HTTPException # type: ignore
from rag_agent.rag_instance import RAGManager
from cloud_storage.do_spaces import download_all_files
from database.db_helper import fetch_metadata_from_db
from rag_agent.lightrag_setup import RAGFactory
from langchain_openai import OpenAI # type: ignore
from config.appconfig import settings as app_settings
from rag_agent.ingress import ingress_file_doc
from lightrag import QueryParam # type: ignore
from models.users_utilities import lookup_user_db_credentials
from utils import clean_text, factual_prompt, generate_explicit_query, proposal_prompt, query_expansion
from langchain_core.messages import AIMessage # type: ignore
from reflexion_agent.state import State
from langgraph.graph.message import add_messages # type: ignore
from structure_agent.defined_proposal_strucutre import proposal_structure

async def proposal_generate_draft(state: dict, config: dict) -> dict:
    user_query = state["user_query"]
    logging.info("User query: %s", user_query)
    rfq_id = state["rfq_id"]
    logging.info("RFQ file %s", rfq_id)
    mode = state["mode"]
    logging.info("Mode selected %s", mode)
    retrieved_docs = state["examples"]
    
    structure_proposal = proposal_structure()  # Ensure this is a ProposalStructure instance, not a dict

    feedback = state.get("human_feedback", ["No Feedback yet"])

    # Step 1: Expand query using structured context
    expanded_queries = generate_explicit_query(user_query, structure_proposal)
    print("[generate_draft] Expanded Queries:", expanded_queries)

    # Step 2: Build the full prompt
    if feedback:
        full_prompt = (
            f"{proposal_prompt(user_query, structure_proposal, retrieved_docs)}\n\n"
            f"User Query: {expanded_queries}\n\n"
            f"Previous Feedback to Improve: {feedback}\n\n"
            f"Please incorporate this feedback into the proposal."
        )
    else:
        full_prompt = (
            f"{proposal_prompt(user_query, structure_proposal, retrieved_docs)}\n\n"
            f"User Query: {expanded_queries}"
        )

    # Step 3: Create RAG instance using config file (PostgreSQL)
    session_data = state.get("session_data")
    if not session_data or "email" not in session_data:
        raise HTTPException(status_code=401, detail="User not authenticated")

    email = session_data.get("email")
    print("[generate_draft] session_data received:", session_data)
    if not email:
        raise HTTPException(status_code=401, detail="User not authenticated")

    # Lookup DB credentials once
    db_user, db_name, db_password, working_dir = lookup_user_db_credentials(email)
    rag = await RAGManager.get_or_create_rag(db_user, db_name, db_password, working_dir)
    rag.chunk_entity_relation_graph.embedding_func = rag.embedding_func
    param = QueryParam(mode=mode,
                       ids=[rfq_id] if mode == "local" and rfq_id else None,
                       user_prompt=full_prompt,
                       conversation_history=[],
                       history_turns=5)

    full_response_text = await rag.aquery(full_prompt, param)
    cleaned_response = clean_text(full_response_text)

    print("[generate_draft] RAG Response Preview:", cleaned_response[:500])

    # Step 6: Save result to state
    candidate_text = cleaned_response
    ai_msg = AIMessage(content=candidate_text)
    state["candidate"] = ai_msg
    state["messages"] = add_messages(state.get("messages", []), [ai_msg])
    # state["source_documents"] = unique_sources

    return state


async def factual_generate_draft(state: dict, config: dict) -> dict:
    user_query = state["user_query"]
    logging.info("User query: %s", user_query)
    rfq_id = state["rfq_id"]
    logging.info("RFQ file %s", rfq_id)
    mode = state["mode"]
    logging.info("Mode selected %s", mode)

    # Step 1: Expand query using structured context
    expanded_queries = query_expansion(user_query)
    print("[generate_draft] Expanded Queries:", expanded_queries)

    # Step 2: Build the full prompt
    full_prompt = (
        f"{factual_prompt(user_query)}\n\n"
        f"User Query: {expanded_queries}"
    )

    # Step 3: Create RAG instance using config file (PostgreSQL)
    session_data = state.get("session_data")
    if not session_data or "email" not in session_data:
        raise HTTPException(status_code=401, detail="User not authenticated")

    email = session_data.get("email")
    print("[generate_draft] session_data received:", session_data)
    if not email:
        raise HTTPException(status_code=401, detail="User not authenticated")

    # Lookup DB credentials once
    db_user, db_name, db_password, working_dir = lookup_user_db_credentials(email)
    rag = await RAGManager.get_or_create_rag(db_user, db_name, db_password, working_dir)
    rag.chunk_entity_relation_graph.embedding_func = rag.embedding_func
    param = QueryParam(mode=mode,
                       ids=[rfq_id] if mode == "local" and rfq_id else None,
                       user_prompt=full_prompt,
                       conversation_history=[],
                       history_turns=5)

    full_response_text = await rag.aquery(full_prompt, param)
    cleaned_response = clean_text(full_response_text)

    print("[generate_draft] RAG Response Preview:", cleaned_response[:500])

    # Step 6: Save result to state
    candidate_text = cleaned_response
    ai_msg = AIMessage(content=candidate_text)
    state["candidate"] = ai_msg
    state["messages"] = add_messages(state.get("messages", []), [ai_msg])
    # state["source_documents"] = unique_sources

    return state



async def process_files_and_links(files, web_links, section):
    results = []
    for uploaded_file in files:
        result = await process_file(uploaded_file, section, web_links)
        results.append(result)
    return {"files_processed": True, "results": results}


import asyncio

async def process_file(file_name, file_content_bytes, web_links=None):
    """Processes a file and optional web links for ingestion."""

    try:
        # Save file to temporary location
        temp_dir = Path("./temp_files")
        temp_dir.mkdir(parents=True, exist_ok=True)
        file_path = temp_dir / file_name
        with open(file_path, "wb") as f:
            f.write(file_content_bytes)

        # Ingest file and links
        if asyncio.iscoroutinefunction(ingress_file_doc):
            response = await ingress_file_doc(file_name, file_path=str(file_path), web_links=web_links or [])
        else:
            response = ingress_file_doc(file_name, file_path=str(file_path), web_links=web_links or [])

        if "error" in response:
            return f"File processing error: {response['error']}"
        else:
            return f"File '{file_name}' processed successfully!"

    except Exception as e:
        traceback.print_exc()
        return f"Unexpected error during processing: {str(e)}"
