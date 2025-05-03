"""
FastAPI application for processing documents and retrieving information using RAG (Retrieval-Augmented Generation).

- `lifespan`: Context manager for initializing and cleaning up resources during the application's lifecycle.
- `index`: Health check endpoint returning application status.
- `health`: Endpoint to check the application's health.
- `ingress_file_doc`: Endpoint for saving and processing uploaded files.
- `retrieve_query`: Endpoint for retrieving information from stored files based on the provided query and section.

Also configures middleware for CORS, security, and handles different modes (development, production).
"""


from src.reflexion_agent.critic import critic
from src.reflexion_agent.evaluate import evaluate
from src.reflexion_agent.retriever import retrieve_examples
from src.reflexion_agent.state import State
from src.datamodel import RequestModel
from src.rag_agent.inference import generate_draft
from src.rag_agent.ingress import ingress_file_doc
from langgraph.checkpoint.memory import MemorySaver # type: ignore
from langgraph.graph import END, StateGraph, START # type: ignore
from langchain_openai import OpenAI # type: ignore
from src.db_helper import initialize_database
from contextlib import asynccontextmanager
from fastapi import FastAPI, status, Depends, HTTPException, UploadFile, File # type: ignore
import os, secrets, uvicorn # type: ignore
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware # type: ignore
from fastapi.security import HTTPBasic, HTTPBasicCredentials # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from fastapi.responses import JSONResponse # type: ignore
from src.config.settings import Settings, get_setting
from src.config.appconfig import settings as app_settings


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
    "*",
]

# Instantiate basicAuth
security = HTTPBasic()

# Add middleware to allow CORS requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
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

# Initialize the checkpointer
checkpointer = MemorySaver()

# Initialize the graph and state machine
builder = StateGraph(State)
builder.add_node("draft", generate_draft)
builder.add_edge(START, "draft")
builder.add_node("retrieve", retrieve_examples)
builder.add_node("critic", critic)
builder.add_node("evaluate", evaluate)

builder.add_edge("draft", "retrieve")
builder.add_edge("retrieve", "critic")
builder.add_edge("critic", "evaluate")

builder.add_conditional_edges("evaluate", lambda state: END if state.get("status") == "success" else "critic", {END: END, "critic": "critic"})

# Compile the graph with the checkpointer
graph = builder.compile(checkpointer=checkpointer)



@app.get("/health", status_code=status.HTTP_200_OK)
def health():
    return "healthy"

@app.post("/ingress-file")
async def ingress_file_doc(file: UploadFile = File(...)):
    try:
        file_path = f"src/doc/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(file.file.read())
            # return {"message": "File saved successfully"}
    except Exception as e:
        return {"message": e.args}
    return await ingress_file_doc(file.filename, file_path)

@app.post("/retrieve")
async def retrieve_query(requestModel: RequestModel, feedback: str = None):
    """
    Endpoint to handle retrieving information based on a user's query and optionally accept feedback.
    """
    initial_state = State(input=requestModel.user_query)
    
    # Run the graph and get the final state after processing
    for step in graph.stream(initial_state):
        if step.is_interrupt:
            if feedback:
                step.state["suggestions"] = step.state.get("suggestions", []) + [feedback]  # Save feedback
                
            # After processing feedback, continue the flow
            final_state = graph.resume(step.state, step.next)
            break
    
    # Retrieve the final response and feedback (if any)
    response = final_state.get("candidate").content if final_state else "No valid answer generated."
    suggestions = final_state.get("suggestions", [])
    
    # Returning both the response and suggestions
    return JSONResponse(content={
        "response": response,
        "suggestions": suggestions
    })


# @app.post("/retrieve")
# async def retrieve_query(requestModel: RequestModel):
#     """
#     Endpoint to handle retrieving information based on a user's query.
#     This integrates the state machine with the RAG process.
#     """
#     initial_state = State(input=requestModel.user_query)
    
#     # Run the graph and get the final state after processing
#     for step in graph.stream(initial_state):
#         if step.is_interrupt:
#             while True:
#                 user_input = input("Do you accept this proposal? (y/n): ").lower()
#                 if user_input == "y":
#                     step.state["status"] = "success"  # Proceed if the user accepts
#                     break
#                 elif user_input == "n":
#                     step.state["status"] = "retry"  # Mark as retry and ask for feedback
#                     feedback = input("Please provide feedback on why you rejected the proposal: ")
#                     step.state["suggestions"] = step.state.get("suggestions", []) + [feedback]  # Save feedback
#                     print(f"Feedback recorded: {feedback}. Processing your feedback...")
#                     break
#                 else:
#                     print("Invalid input. Please enter 'y' for accept or 'n' for reject.")
            
#             # Resume the flow after feedback is collected
#             final_state = graph.resume(step.state, step.next)
#             break
    
#     # Retrieve the final response and feedback (if any)
#     response = final_state.get("candidate").content if final_state else "No valid answer generated."
#     suggestions = final_state.get("suggestions", [])
    
#     # Returning both the response and suggestions
#     return JSONResponse(content={
#         "response": response,
#         "suggestions": suggestions
#     })
        
        
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
