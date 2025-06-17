"""
FastAPI application for processing documents and retrieving information using RAG (Retrieval-Augmented Generation).

- `lifespan`: Context manager for initializing and cleaning up resources during the application's lifecycle.
- `index`: Health check endpoint returning application status.
- `health`: Endpoint to check the application's health.
- `ingress_file_doc`: Endpoint for saving and processing uploaded files.
- `retrieve_query`: Endpoint for retrieving information from stored files based on the provided query and section.

Also configures middleware for CORS, security, and handles different modes (development, production).
"""


from datetime import datetime
import json
from typing import List
import requests # type: ignore
import logging
import traceback
from urllib.parse import urlencode
from sqlalchemy import create_engine# type: ignore
import uuid
from document_processor import DocumentProcessor
from googleapiclient.discovery import build # type: ignore
from google.oauth2.credentials import Credentials # type: ignore
import httpx # type: ignore
from google_doc_integration.google_docs_helper import GoogleDocsHelper
from google_doc_integration.google_drive_helper import GoogleDriveAPI
from rag_agent.rag_instance import RAGManager
from reflexion_agent.human_feedback import human_node
from graph.node_edges import control_edge, create_state_graph
from reflexion_agent.critic import critic
from reflexion_agent.retriever import retrieve_examples
from reflexion_agent.state import State, Status
from datamodel import PromptRequest, QueryRequest, RequestModel
from rag_agent.inference import generate_draft
from rag_agent.ingress import ingress_file_doc
from database.db_helper import extract_prompt_suggestions, extract_proposal_metadata_llm, get_recent_activity, insert_document, open_tenant_db_connection, save_metadata_to_db, extract_metadata_with_llm, store_proposal_to_db
from models.models import metadata
from langchain_core.runnables import RunnableConfig # type: ignore
from langchain_openai import OpenAI # type: ignore
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, Request, status, HTTPException, UploadFile, File, Form, Depends # type: ignore
from models.users_utilities import get_user_session, lookup_user_db_credentials
from utils import sql_expert_prompt
from structure_agent.structureAgent import structure_node
import os, uvicorn # type: ignore
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware # type: ignore
from fastapi.security import HTTPBasic # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from starlette.middleware.sessions import SessionMiddleware # type: ignore
from itsdangerous import URLSafeTimedSerializer # type: ignore
from starlette.config import Config # type: ignore
from authlib.integrations.starlette_client import OAuth, OAuthError # type: ignore
from fastapi.responses import JSONResponse, RedirectResponse # type: ignore
from langchain_experimental.sql import SQLDatabaseChain #type: ignore
from langchain_community.utilities import SQLDatabase # type: ignore
from config.settings import get_setting
from multi_tenant.onboard_user import onboard_user
from config.appconfig import settings as app_settings
from functools import partial
import logging
from langchain_openai import ChatOpenAI # type: ignore
from fastapi.exceptions import RequestValidationError # type: ignore
from fastapi.exception_handlers import request_validation_exception_handler # type: ignore


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
# Get application settings from the settings module
settings = get_setting()
# Description for API documentation
description = f"""
{settings.API_STR} helps you do awesome stuff. 🚀
"""

master_engine = create_engine(app_settings.master_db_url)


# Define a context manager for the application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for application lifespan.
    This function initializes and cleans up resources during the application's lifecycle.
    """
    # STARTUP Call Check routine
    print(running_mode)
    logger.info("Master database url: %s", app_settings.master_db_url)
    master_engine = create_engine(app_settings.master_db_url)
    metadata.create_all(master_engine)

    # Configure OpenAI API
    OpenAI.api_key = app_settings.openai_api_key
    
    print(" ⚡️🚀 RAG Server::Started")
    yield

# Create FastAPI app instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=description,
    openapi_url=f"{settings.API_STR}/openapi.json",
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    contact={
        "name": "example",
        "url": "https://www.example.com/",
        "email": "hello@example.com",
    },
    lifespan=lifespan,
)
# Configure for development or production mode
if app_settings.environment in ["production", "staging"]:
    running_mode = f"  👩‍💻 🛠️  Running in::{app_settings.environment} mode"
else:
    app.add_middleware(HTTPSRedirectMiddleware)
    running_mode = "  🏭 ☁  Running in::production mode"

# Define allowed origins for CORS
origins = [
    "https://cdga-proposal-agent-r2v7y.ondigitalocean.app",
]

# Instantiate basicAuth
security = HTTPBasic()

serializer = URLSafeTimedSerializer(app_settings.session_secret_key)
# Add CORS middleware first
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add Session middleware AFTER CORS
app.add_middleware(
    SessionMiddleware,
    secret_key=serializer.secret_key,
    session_cookie="session",
    same_site="none",         # or "none" if using HTTPS
    https_only=True,        # ✅ False for local dev
)

extract_metadata = DocumentProcessor()

oauth = OAuth(Config(environ={
    'GOOGLE_CLIENT_ID': app_settings.client_id,
    'GOOGLE_CLIENT_SECRET': app_settings.client_secret,
}))

oauth.register(
    name='google',
    client_id=app_settings.client_id,
    client_secret=app_settings.client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/documents',
    }
)


# Assuming you already initialized your llm like:
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0
)

# Wrap the critic function to always pass in the LLM
wrapped_critic = partial(critic, llm=llm)

   
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print("Validation error:", exc.errors())
    return await request_validation_exception_handler(request, exc)

@app.get("/api/login")
async def login():
    query_params = {
        "client_id": app_settings.client_id,
        "redirect_uri": app_settings.redirect_uri_1,
        "response_type": "code",
        "scope": "openid email profile https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/documents",
        "access_type": "offline",
        "prompt": "consent",
    }
    url = f"{app_settings.google_auth_endpoint}?{urlencode(query_params)}"
    return RedirectResponse(url)



@app.get("/api/auth")
async def auth(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    # Exchange code for token
    data = {
        "code": code,
        "client_id": app_settings.client_id,
        "client_secret": app_settings.client_secret,
        "redirect_uri": app_settings.redirect_uri_1,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(app_settings.google_token_endpoint, data=data)
        token_data = response.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to obtain access token")

        # Fetch user info
        headers = {"Authorization": f"Bearer {access_token}"}
        userinfo_response = await client.get(app_settings.google_userinfo_endpoint, headers=headers)
        userinfo = userinfo_response.json()

        email = userinfo["email"]
        name = userinfo["name"]
        user = name.replace(" ", "_").lower()
        picture = userinfo["picture"]

        # Prepare connection info
        pg_super_conn_info = {
            "host": app_settings.host,
            "port": app_settings.port_db,
            "user": app_settings.user,
            "database": app_settings.db_name,
            "password": app_settings.password
        }

        logging.info(("DEBUG: pg_super_conn_info = %s", pg_super_conn_info))
        result = onboard_user(user, email, pg_super_conn_info, master_engine)
        print("onboard_user result:", result)
        # Onboard the user (create DB, working dir, and register in master DB)
        tenant_username, tenant_db_name, tenant_db_conn_str, working_dir, user_password = onboard_user(user, email, pg_super_conn_info, master_engine)

         # Serialize user DB info into cookie
        session_data = {
            "email": email,
            "db_user": tenant_username,
            "database_name": tenant_db_name,
            "db_conn_str": tenant_db_conn_str,
            "working_dir": working_dir,
            "password": user_password
        }

        signed_data = serializer.dumps(session_data)
        # token = request.cookies.get("session_token")


        # Redirect to frontend (or success page)
        response =  RedirectResponse(
            f"{app_settings.redirect_uri_2}/profile"
            f"?name={name}"
            f"&email={email}"
            f"&picture={picture}"
            f"&access_token={access_token}"
            f"&refresh_token={refresh_token or ''}"
        )

        # Set user session cookie
        response.set_cookie(
            key="user_session",
            value=signed_data,          # or signed_data if that's your token
            httponly=False,
            samesite="none",       # capitalized is fine, case-insensitive
            secure=True          # False if localhost; True in production HTTPS
        )

        return response
    


@app.get("/api/logout") 
async def logout():
    # No server-side data to clear; just redirect to login page
    return RedirectResponse(url=app_settings.redirect_uri_3)


@app.get("/api/me")
async def me(request: Request):
    user_info = request.query_params
    name = user_info.get("name")
    email = user_info.get("email")
    picture = user_info.get("picture")

    return {
        "user" : {
            "name": name,
            "email": email,
            "picture": picture
        }
    }
    


# Define a health check endpoint
@app.get("/api/", status_code=status.HTTP_200_OK)
def index(response_class=JSONResponse):
    return {
        "ApplicationName": "Proposal Generator Agent", 
        "ApplicationOwner": "Zenovo-AI",
        "ApplicationVersion": "0.1.0",
        "ApplicationEngineer": "CertifiedAuthur",
        "ApplicationStatus": "running...",
    }


@app.get("/api/health", status_code=status.HTTP_200_OK)
def health():
    return "healthy"


@app.post("/api/ingress-file")
async def upload_files_and_links(
    files: List[UploadFile] = File([]),
    web_links: List[str] = Form([]),
    session_data: dict = Depends(get_user_session)
):
    try:
        email = session_data.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="User not authenticated")

        db_user, db_name, db_password, working_dir = lookup_user_db_credentials(email)
        logger.info("User, Database Name, Database Password: %s: %s: %s", db_user, db_name, db_password)

        results = []

        # Handle multiple file uploads
        for file in files:
            file_path = os.path.join(working_dir, file.filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(await file.read())

            text = extract_metadata.extract_text_from_pdf(file_path)
            metadata = extract_metadata_with_llm(text)
            prompt_suggestions = extract_prompt_suggestions(text)
            logging.info("Suggested Prompts: %s", prompt_suggestions)

            document_name = file.filename
            metadata.update({"id": document_name, "file_name": file.filename})

            insert_document(document_name, file.filename, text, db_user, db_name, db_password)
            save_metadata_to_db(metadata, prompt_suggestions, db_user, db_name, db_password)

            logging.info(f"✅ Inserted and saved metadata for document {document_name}")
            logging.info("📥 Calling ingress_file_doc...")

            result = await ingress_file_doc(
                file_name=file.filename,
                file_path=file_path,
                overwrite=True,
                session_data=session_data
            )
            results.append(result)

        # Handle multiple web links
        for link in web_links:
            link = link.strip()
            if not link:
                continue

            response = requests.get(link)
            if response.status_code != 200:
                logging.warning(f"❌ Failed to fetch {link}")
                continue

            filename = f"web_{uuid.uuid4().hex[:8]}.pdf"
            file_path = os.path.join(working_dir, file.filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(response.content)

            text = extract_metadata.extract_text_from_pdf(file_path)
            metadata = extract_metadata_with_llm(text)
            prompt_suggestions = extract_prompt_suggestions(text)
            logging.info("Suggested Prompts: %s", prompt_suggestions)

            document_name = str(uuid.uuid4())
            metadata.update({
                "id": document_name,
                "file_name": filename,
                "source": link
            })

            insert_document(document_name, filename, text, db_user, db_name, db_password)
            save_metadata_to_db(metadata, prompt_suggestions, db_user, db_name, db_password)

            logging.info(f"✅ Saved metadata for web link {link}")
            logging.info("📥 Calling ingress_file_doc...")

            result = await ingress_file_doc(
                file_name=link,
                web_links=[link],
                overwrite=True,
                session_data=session_data
            )
            results.append(result)

        if not results:
            raise HTTPException(status_code=400, detail="No valid files or web links processed.")

        return {"message": "Upload completed.", "details": results}

    except Exception as e:
        logging.error("Unhandled error in /ingress-file route", exc_info=True)
        return {"message": f"An error occurred: {str(e)}"}


@app.post("/api/retrieve")
async def retrieve_query(requestModel: RequestModel, session_data: dict = Depends(get_user_session)):
    print("Received data:", requestModel.model_dump())
    initial_state = {
        "user_query": requestModel.user_query,
        "candidate": None,
        "examples": [],
        "human_feedback": [],
        "critic_feedback": "",
        "status": Status.IN_PROGRESS,
        "rfq_id": requestModel.rfq_id,
        "mode": requestModel.mode,
        "iteration": 0,
        "session_data": session_data,
    }

    try:
                # Create graph
        graph = create_state_graph(
            State, structure_node, generate_draft, retrieve_examples, wrapped_critic, 
            human_node, control_edge
        )
        
        last_response = None
        config = RunnableConfig(
            recursion_limit=10,
            configurable={
                "thread_id": f"{session_data['email']}_thread1",
                "session_data": session_data,
            }
        )
        
        interrupt_reached = False

        async for step in graph.astream(initial_state, config=config):
            node_id = list(step.keys())[0]
            value = step[node_id]

            print(f"Current node: {node_id}")  # Debug print

            match node_id:
                case "draft":
                    ai_message = value.get("candidate", {})
                    content_str = ai_message.content if hasattr(ai_message, "content") else str(ai_message)
                    last_response = content_str
                    initial_state["candidate"] = content_str 
                    continue
                    
                case "retrieve":
                    initial_state["examples"] = value.get("examples", [])
                    continue
                    
                case "critic":
                    initial_state["critic_feedback"] = value.get("critique", "")
                    continue
                    
                case "__interrupt__":
                    interrupt_reached = True

                    proposal_content = last_response
                    
                    if not proposal_content:
                        return JSONResponse(
                            content={"error": "No proposal content generated"},
                            status_code=500
                        )

                    # Safely convert Enum to string
                    serializable_state = {
                        **initial_state,
                        "status": initial_state["status"].value
                    }

                    response_payload = {
                        "interrupt": True,
                        "message": "Please review the draft and provide your feedback.",
                        "proposal": proposal_content,
                        "feedback_options": [
                            "approve - if the proposal is satisfactory",
                            "revise - if changes are needed (please specify what to improve)"
                        ],
                        "state": serializable_state
                    }

                    # Log response
                    logging.info("Returning response: %s", response_payload)

                    return JSONResponse(content=response_payload, status_code=200)

        # If no interrupt reached
        if not interrupt_reached:
            return JSONResponse(
                content={"error": "Graph completed without reaching interrupt"},
                status_code=500
            )

    except Exception as e:
        logging.error("Error in retrieve_query: %s", str(e))
        return JSONResponse(
            content={"error": f"An error occurred: {str(e)}"},
            status_code=500
        )


@app.post("/api/resume")
async def resume_graph(payload: dict):
    try:
        state_data = payload["state"]
        feedback = payload.get("feedback", "").lower()
        print("incoming payload", payload)

        raw_status = state_data.get("status", "in_progress").lower()
        current_status = Status(raw_status) if raw_status in Status._value2member_map_ else Status.IN_PROGRESS

        state = State(state_data)
        state["human_feedback"].append(feedback)

        # Update status based on feedback
        if "approve" in feedback:
            state["status"] = Status.APPROVED
            return JSONResponse(
                content={
                    "response": "Proposal approved. Process complete.",
                    "status": Status.APPROVED.value
                },
                status_code=200
            )
        elif "revise" in feedback:
            state["status"] = Status.NEEDS_REVISION
        else:
            state["status"] = Status.IN_PROGRESS

        # Re-create the graph
        graph = create_state_graph(
            State, structure_node, generate_draft, retrieve_examples, wrapped_critic,
            human_node, control_edge
        )

        # Apply feedback to config
        base_config = RunnableConfig(recursion_limit=10, configurable={"thread_id": "1"})
        updated_config = graph.update_state(
            base_config,
            values={"messages": [("user", feedback)]}
        )

        proposal_content = None
        async for step in graph.astream(state, config=updated_config):
            node_id = list(step.keys())[0]
            value = step[node_id]

            print(f"Processing node: {node_id}")

            # if node_id == "draft":
            #     ai_message = value.get("candidate", {})
            #     proposal_content = ai_message.content if hasattr(proposal_content, "content") else str(proposal_content)

            if node_id == "draft":
                ai_message = value.get("candidate")
                if ai_message and hasattr(ai_message, "content"):
                    proposal_content = ai_message.content
                elif isinstance(ai_message, str):
                    proposal_content = ai_message

                

        if proposal_content:
            # Return proposal and updated state
            serializable_state = {
                **state,
                "status": state["status"].value
            }

            return JSONResponse(
                content={
                    "interrupt": True,
                    "message": "Here is the revised proposal. Please review and provide feedback.",
                    "proposal": proposal_content,
                    "feedback_options": [
                        "approve - if the proposal is satisfactory",
                        "revise - if changes are needed (please specify what to improve)"
                    ],
                    "state": serializable_state
                },
                status_code=200
            )
        else:
            return JSONResponse(
                content={
                    "response": "No proposal generated during resume.",
                    "status": state["status"].value
                },
                status_code=500
            )

    except Exception as e:
        logging.error(f"Resume error: {str(e)}")
        return JSONResponse(
            content={"error": f"Failed to resume graph: {str(e)}"},
            status_code=500
        )


@app.get("/api/recent-rfqs")
def get_recent_rfqs(session_data: dict = Depends(get_user_session)):
    logger.info("📥 Incoming request to /recent-rfqs")

    email = session_data.get("email")
    if not email:
        logger.warning("❌ No email found in session data — user not authenticated")
        raise HTTPException(status_code=401, detail="User not authenticated")

    logger.info(f"🔐 Session found for email: {email}")

    try:
        db_user, db_name,  db_password, _ = lookup_user_db_credentials(email)
        logger.info(f" Password: {db_password}")
        logger.info(f"✅ DB credentials resolved for email: {email} -> DB: {db_name}")
    except Exception as e:
        logger.exception("❌ Failed to lookup DB credentials")
        raise HTTPException(status_code=500, detail="Error retrieving database credentials")

    try:
        conn = open_tenant_db_connection(db_user, db_name, db_password)
        logger.info("🔗 DB connection established")
    except Exception as e:
        logger.exception("❌ Failed to connect to the tenant DB")
        raise HTTPException(status_code=500, detail="Database connection error")

    try:
        cursor = conn.cursor()
        logger.info("📄 Executing SQL query for recent RFQs")

        cursor.execute("""
            SELECT m.file_name, m.organization_name, m.title, m.submission_deadline
            FROM rfqs m
            JOIN documents d ON m.file_name = d.document_name
            ORDER BY d.upload_time DESC
        """)

        rows = cursor.fetchall()
        logger.info(f"📦 Retrieved {len(rows)} rows from the database")

        result = [
            {
                "document_name": row[0],
                "organization": row[1],
                "title": row[2],
                "deadline": row[3].isoformat() if row[3] else None
            }
            for row in rows
        ]
        logger.info("📄 RFQ Result: %s", result)
        return {"rfqs": result}

    except Exception as e:
        logger.exception("❌ Error while querying or processing RFQs")
        raise HTTPException(status_code=500, detail="Internal error retrieving RFQs")
    finally:
        conn.close()
        logger.info("🔒 DB connection closed")


@app.post("/api/search-rfqs")
def search_rfqs(query_data: QueryRequest, session_data: dict = Depends(get_user_session)):
    email = session_data.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="User not authenticated")

    # Lookup DB credentials once
    db_user, db_name, db_password, _ = lookup_user_db_credentials(email)
    conn = open_tenant_db_connection(db_user, db_name, db_password)
    try:
        db = SQLDatabase(conn)
        llm = OpenAI(temperature=0, openai_api_key=app_settings.openai_api_key, prompt=sql_expert_prompt())
        db_chain = SQLDatabaseChain(llm=llm, database=db, verbose=True)
        response = db_chain.run(query_data.query)
        return {"results": response}
    finally:
        conn.close()


@app.post("/api/save-to-drive")
async def save_to_google_drive(payload: dict, session_data: dict = Depends(get_user_session)):
    try:
        print("Incoming payload:", payload)
        state = payload.get("state")
        if not state:
            raise HTTPException(status_code=400, detail="State missing from payload.")

        messages = state.get("messages", [])
        if not messages:
            raise HTTPException(status_code=400, detail="No messages found in state.")


        # Define the target substring to search for (lowercase for case-insensitive matching)
        target_substring = "✅ proposal approved. you can now upload it to google docs."

        last_approval_index = None
        # Iterate over messages to find all assistant messages containing the target substring
        for index, message in enumerate(messages):
            if message.get("role") == "assistant":
                content = message.get("content", "")
                if content and target_substring in content.lower():
                    last_approval_index = index

        # If no approval message was found, raise an error
        if last_approval_index is None:
            raise HTTPException(status_code=404, detail="No approval message found in the conversation.")
        
        # Search backwards from the approval message for the immediately preceding assistant message
        for prev_index in range(last_approval_index - 1, -1, -1):
            prev_message = messages[prev_index]
            if prev_message.get("role") == "assistant":
                proposal_text = prev_message.get("content", "")
                break



        # === Google Drive Logic ===
        token_info = {
            "client_id": app_settings.client_id,
            "client_secret": app_settings.client_secret,
            "refresh_token": payload["refresh_token"],
            "token_uri": app_settings.google_token_endpoint,
        }

        creds = Credentials.from_authorized_user_info(token_info)
        docs_service = build("docs", "v1", credentials=creds)
        drive_service = build("drive", "v3", credentials=creds)

        drive_api = GoogleDriveAPI(drive_service)

        TEMPLATE_NAME = "ProposalTemplate"
        template_id = drive_api.get_template_id(TEMPLATE_NAME)
        if not template_id:
            raise HTTPException(status_code=404, detail=f"Template '{TEMPLATE_NAME}' not found")

        proposals_folder_id = drive_api.create_folder("Proposals")
        date_folder_id = drive_api.create_folder(datetime.now().strftime("%Y-%m-%d"), parent_folder_id=proposals_folder_id)

        docs_helper = GoogleDocsHelper(docs_service, drive_service)
        # replacements = parse_proposal_content(proposal_text)
        doc_name = f"Proposal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        new_doc_id = docs_helper.copy_template(template_id, doc_name)
        docs_helper.replace_placeholder(new_doc_id, "{BODY}", proposal_text)
        

        drive_service.files().update(
            fileId=new_doc_id,
            addParents=date_folder_id,
            removeParents='root'
        ).execute()

        view_link = docs_helper.generate_view_link(new_doc_id)

        # === Extract metadata ===
        metadata = await extract_proposal_metadata_llm(proposal_text)
        logging.info("Proposal: %s", proposal_text)
        title = metadata.get("title")
        logging.info(f"Extracted title: {title}")
        summary = metadata.get("summary")
        logging.info(f"Extracted summary: {summary}")

        # === Save to DB ===
        email = session_data.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="User not authenticated")
        # Lookup DB credentials once
        db_user, db_name, db_password, _ = lookup_user_db_credentials(email)
        rfq_id = payload.get("rfq_id") or "unknown"
        try:
            rfq_id = int(rfq_id) if rfq_id not in [None, "unknown", ""] else None
        except ValueError:
            rfq_id = None
        is_winning = payload.get("is_winning", False)
        

        store_proposal_to_db(db_user, db_name, db_password, rfq_id, title, proposal_text, summary, is_winning)


        return JSONResponse(content={"message": "Upload successful", "view_link": view_link})

    except Exception as e:
        logging.error("Failed to save proposal to Google Drive", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "traceback": traceback.format_exc()}
        )


# @app.get("/prompt-suggestions")
# async def get_prompt_suggestions(session_data: dict = Depends(get_user_session)):
#     email = session_data.get("email")
#     if not email:
#         raise HTTPException(status_code=401, detail="User not authenticated")
    
#     db_user, db_name, db_password, _ = lookup_user_db_credentials(email)
#     conn = open_tenant_db_connection(db_user, db_name, db_password)
#     cursor = conn.cursor()

#     cursor.execute("""
#         SELECT prompt_suggestions FROM rfqs
#         ORDER BY created_at DESC
#         LIMIT 1
#     """)
#     result = cursor.fetchone()
#     conn.close()

#     if not result or not result[0]:
#         logging.info("Prompts: %s", result)
#         return {"prompts": []}

#     try:
#         # 👇 double parse due to double encoding
#         parsed = json.loads(result[0])
#         if isinstance(parsed, str):
#             parsed = json.loads(parsed)
#         return {"prompts": parsed}
#     except Exception as e:
#         logging.error("Failed to parse prompt suggestions: %s", e)
#         return {"prompts": []}

@app.post("/api/prompt-suggestions")
async def get_prompt_suggestions(
    payload: PromptRequest,
    session_data: dict = Depends(get_user_session)
):
    print("Received data:", payload)
    rfq_id = payload.rfq_id

    email = session_data.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="User not authenticated")

    db_user, db_name, db_password, _ = lookup_user_db_credentials(email)
    conn = open_tenant_db_connection(db_user, db_name, db_password)
    cursor = conn.cursor()

    if rfq_id:
        logging.info("Selected RFQ: %s", rfq_id)
        cursor.execute(
            "SELECT prompt_suggestions FROM rfqs WHERE document_name = %s",
            (rfq_id,)
        )
    else:
        cursor.execute("""
            SELECT prompt_suggestions
            FROM rfqs
            ORDER BY created_at DESC
            LIMIT 1
        """)

    result = cursor.fetchone()
    conn.close()

    if not result or not result[0]:
        return {"prompts": []}

    try:
        prompts = json.loads(result[0])
        if isinstance(prompts, str):
            prompts = json.loads(prompts)
        return {"prompts": prompts}
    except Exception as e:
        logging.error("Failed to parse prompt suggestions: %s", e)
        return {"prompts": []}



@app.get("/api/recent-activity")
def recent_activity(session_data: dict= Depends(get_user_session)):
    email = session_data.get("email")
    db_user, db_name, db_password, _ = lookup_user_db_credentials(email)
    activity = get_recent_activity(db_user, db_name, db_password)

    logging.info("Proposals returned: %s", activity.get("proposals", []))
    return activity

@app.get("/api/winning-proposals")
def winning_proposals(session_data: dict = Depends(get_user_session)):
    email = session_data.get("email")
    db_user, db_name, db_password, _ = lookup_user_db_credentials(email)

    conn = open_tenant_db_connection(db_user, db_name, db_password)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT proposal_id, proposal_title, proposal_content, created_at
        FROM proposals
        WHERE is_winning = TRUE
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    proposals = [
        {
            "proposal_id": str(row[0]),
            "proposal_title": row[1],
            "proposal_content": row[2],
            "created_at": row[3].isoformat() if row[3] else None,
        }
        for row in rows
    ]

    return {"proposals": proposals}

        
        
if __name__ == "__main__":
    # Retrieve environment variables for host, port, and timeout
    timeout_keep_alive = int(os.getenv("YOUR_TIMEOUT_IN_SECONDS", 6000))

    # Run the application with the specified host, port, and timeout
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(app_settings.port),
        timeout_keep_alive=timeout_keep_alive,
    )
