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
import logging
import traceback
from urllib.parse import urlencode
from googleapiclient.discovery import build # type: ignore
from google.oauth2.credentials import Credentials # type: ignore
import httpx # type: ignore
from src.google_doc_integration.google_docs_helper import GoogleDocsHelper
from src.google_doc_integration.google_drive_helper import GoogleDriveAPI
from src.google_doc_integration.parse_proposal import parse_proposal_content
from src.reflexion_agent.end_process import end_node
from src.reflexion_agent.human_feedback import human_node
from src.graph.node_edges import control_edge, create_state_graph
from src.reflexion_agent.critic import critic
from src.reflexion_agent.retriever import retrieve_examples
from src.reflexion_agent.state import State, Status
from src.datamodel import RequestModel
from src.rag_agent.inference import generate_draft
from src.rag_agent.ingress import ingress_file_doc
from langchain_core.runnables import RunnableConfig # type: ignore
from langchain_openai import OpenAI # type: ignore
from src.db_helper import initialize_database
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException, UploadFile, File # type: ignore
from src.structure_agent.structureAgent import structure_node
import os, uvicorn # type: ignore
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware # type: ignore
from fastapi.security import HTTPBasic # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from starlette.middleware.sessions import SessionMiddleware # type: ignore
from itsdangerous import URLSafeTimedSerializer # type: ignore
from starlette.config import Config # type: ignore
from authlib.integrations.starlette_client import OAuth, OAuthError # type: ignore
from fastapi.responses import JSONResponse, RedirectResponse # type: ignore
from src.config.settings import get_setting
from src.config.appconfig import settings as app_settings
from functools import partial
from langchain_openai import ChatOpenAI # type: ignore
from authlib.integrations.starlette_client.apps import StarletteOAuth2App # type: ignore
from fastapi.exceptions import RequestValidationError # type: ignore
from fastapi.exception_handlers import request_validation_exception_handler # type: ignore

# Get application settings from the settings module
settings = get_setting()
# Description for API documentation
description = f"""
{settings.API_STR} helps you do awesome stuff. 🚀
"""

# Define a context manager for the application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for application lifespan.
    This function initializes and cleans up resources during the application's lifecycle.
    """
    # STARTUP Call Check routine
    print(running_mode)
    print()
    
    # Configure OpenAI API
    OpenAI.api_key = app_settings.openai_api_key
    
    # Initialize database
    initialize_database()
    
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
if app_settings.environment in ["development", "staging"]:
    running_mode = f"  👩‍💻 🛠️  Running in::{app_settings.environment} mode"
else:
    app.add_middleware(HTTPSRedirectMiddleware)
    running_mode = "  🏭 ☁  Running in::production mode"

# Define allowed origins for CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Instantiate basicAuth
security = HTTPBasic()

serializer = URLSafeTimedSerializer(app_settings.session_secret_key)
# Add CORS middleware first
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # 🔥 Necessary to allow cookies
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add Session middleware AFTER CORS
app.add_middleware(
    SessionMiddleware,
    secret_key=serializer.secret_key,
    session_cookie="session",
    same_site="lax",         # or "none" if using HTTPS
    https_only=False,        # ✅ False for local dev
)



# Get the directory of the current file
base_dir = os.path.dirname(os.path.abspath(__file__))

# Define the auth cache directory
auth_cache_dir = os.path.join(base_dir, "auth_cache")

# Create full paths for the credentials and status file
credentials_path = os.path.join(auth_cache_dir, "credentials.json")
auth_status_path = os.path.join(auth_cache_dir, "auth_success.txt")
state_path = os.path.join(auth_cache_dir, "oauth_state.txt")

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

@app.get("/login")
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



@app.get("/auth")
async def auth(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    
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
        
        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        userinfo_response = await client.get(app_settings.google_userinfo_endpoint, headers=headers)
        userinfo = userinfo_response.json()

        return RedirectResponse(
            f"{app_settings.redirect_uri_2}/profile"
            f"?name={userinfo['name']}"
            f"&email={userinfo['email']}"
            f"&picture={userinfo['picture']}"
            f"&access_token={access_token}"
            f"&refresh_token={refresh_token or ''}"
        )


@app.get("/logout")
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
@app.get("/", status_code=status.HTTP_200_OK)
def index(response_class=JSONResponse):
    return {
        "ApplicationName": "Health Policy Chatbot",
        "ApplicationOwner": "Your Company",
        "ApplicationVersion": "0.1.0",
        "ApplicationEngineer": "Your name",
        "ApplicationStatus": "running...",
    }


@app.get("/health", status_code=status.HTTP_200_OK)
def health():
    return "healthy"

@app.post("/ingress-file")
async def uploadFile(file: UploadFile = File(...)):
    try:
        file_path = f"src/doc/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(file.file.read())
            # return {"message": "File saved successfully"}
    except Exception as e:
        return {"message": e.args}
    return await ingress_file_doc(file.filename, file_path)



@app.post("/retrieve")
async def retrieve_query(requestModel: RequestModel):
    initial_state = {
        "user_query": requestModel.user_query,
        "candidate": None,
        "examples": [],
        "human_feedback": [],
        "critic_feedback": "",
        "status": Status.IN_PROGRESS,
        "iteration": 0,
    }

    try:
        # Create graph
        graph = create_state_graph(
            State, structure_node, generate_draft, retrieve_examples, wrapped_critic, 
            human_node, control_edge
        )
        
        last_response = None
        config = RunnableConfig(recursion_limit=10, configurable={"thread_id": "1"})
        interrupt_reached = False

        async for step in graph.astream(initial_state, config=config):
            node_id = list(step.keys())[0]
            value = step[node_id]

            print(f"Current node: {node_id}")  # Debug print

            match node_id:
                # case "draft":
                #     last_response = value.get("candidate", {})
                #     initial_state["candidate"] = last_response
                #     continue
                case "draft":
                    ai_message = value.get("candidate", {})
                    content_str = ai_message.content if hasattr(ai_message, "content") else str(ai_message)
                    last_response = content_str
                    initial_state["candidate"] = content_str  # ✅ now it's JSON serializable
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



@app.post("/resume")
async def resume_graph(payload: dict):
    try:
        state_data = payload["state"]
        feedback = payload.get("feedback", "").lower()

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


@app.post("/save-to-drive")
async def save_to_google_drive(payload: dict):
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

        return JSONResponse(content={"message": "Upload successful", "view_link": view_link})

    except Exception as e:
        logging.error("Failed to save proposal to Google Drive", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "traceback": traceback.format_exc()}
        )


        
        
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
