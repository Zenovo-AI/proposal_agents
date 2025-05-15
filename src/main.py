"""
FastAPI application for processing documents and retrieving information using RAG (Retrieval-Augmented Generation).

- `lifespan`: Context manager for initializing and cleaning up resources during the application's lifecycle.
- `index`: Health check endpoint returning application status.
- `health`: Endpoint to check the application's health.
- `ingress_file_doc`: Endpoint for saving and processing uploaded files.
- `retrieve_query`: Endpoint for retrieving information from stored files based on the provided query and section.

Also configures middleware for CORS, security, and handles different modes (development, production).
"""


import logging
from src.reflexion_agent.end_process import end_node
from src.reflexion_agent.human_feedback import human_node
from src.graph.node_edges import control_edge, create_state_graph
from src.reflexion_agent.critic import critic
from src.reflexion_agent.evaluate import evaluate
from src.reflexion_agent.retriever import retrieve_examples
from src.reflexion_agent.state import State, Status
from src.datamodel import RequestModel
from src.rag_agent.inference import generate_draft
from src.rag_agent.ingress import ingress_file_doc
from langchain_core.runnables import RunnableConfig 
from langgraph.types import Command
from langchain_openai import OpenAI 
from src.db_helper import initialize_database
from contextlib import asynccontextmanager
from fastapi import FastAPI, status, Depends, HTTPException, UploadFile, File 
import os, secrets, uvicorn 
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials 
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.config.settings import Settings, get_setting
from src.config.appconfig import settings as app_settings
from functools import partial
from langchain_openai import ChatOpenAI 

MAX_ITERATIONS = 10

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

# Assuming you already initialized your llm like:
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0
)

# Wrap the critic function to always pass in the LLM
wrapped_critic = partial(critic, llm=llm)

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
async def ingress_file_doc(file: UploadFile = File(...)):
    try:
        file_path = f"src/doc/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(file.file.read())
            # return {"message": "File saved successfully"}
    except Exception as e:
        return {"message": e.args}
    return await ingress_file_doc(file.filename, file_path)


# @app.post("/retrieve")
# async def retrieve_query(requestModel: RequestModel, feedback: str = None):
#     """
#     Endpoint to handle retrieving information based on a user's query and optionally accept feedback.
#     """
#     initial_state = {
#         "user_query": requestModel.user_query,
#         "generated_post": [],
#         "examples": [],
#         "critic_feedback": [],
#         "evaluation_result": "",
#         "human_feedback": [],
#         "final_post": "",
#     }

#     graph = create_state_graph(State, generate_draft, retrieve_examples, wrapped_critic, evaluate, human_node, END)

#     config = RunnableConfig(
#         recursion_limit=10,
#         configurable={"thread_id": "1"},
#     )

#     # async for step in graph.astream(input_state, config=config):
#     #     # If it's an interrupt, optionally inject feedback and resume
#     #     if step.get("is_interrupt", False):
#     #         if feedback:
#     #             step["state"]["feedback"] = feedback  # Replace suggestions with feedback

#     #         # Resume and continue iteration
#     #         resumed = await graph.resume(step["state"], step["next"])
#     #         response = resumed.get("candidate", {}).get("content", response)
#     #         break
#     #     else:
#     #         # Save response from the last step in case it's the final one
#     #         state_candidate = step.get("state", {}).get("candidate", {})
#     #         if isinstance(state_candidate, dict):
#     #             response = state_candidate.get("content", response)

#     for chunk in graph.astream(initial_state, config=config):
#         for node_id, value in chunk.items():
#             #  If we reach an interrupt, continuously ask for human feedback

#             if(node_id == "__interrupt__"):
#                 while True: 
#                     user_feedback = input("Provide feedback (or type 'done' when finished): ")

#                     # Resume the graph execution with the user's feedback
#                     graph.invoke(Command(resume=user_feedback), config=config)

#                     # Exit loop if user says done
#                     if user_feedback.lower() == "done":
#                         break

#     return JSONResponse(content={
#         "response": response
#     })



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
            State, generate_draft, retrieve_examples, wrapped_critic, 
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
                case "draft":
                    last_response = value.get("candidate", {})
                    initial_state["candidate"] = last_response
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
            State, generate_draft, retrieve_examples, wrapped_critic,
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

            if node_id == "draft":
                proposal_content = value.get("candidate", {})

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







# @app.post("/retrieve")
# async def retrieve_query(requestModel: RequestModel, feedback: str = None):
#     """
#     Endpoint to retrieve a post based on a LinkedIn topic and handle human feedback during interruptions.
#     """
#     # Build initial state from the user query
#     initial_state = {
#         "user_query": requestModel.user_query,
#         "candidate": [],
#         "examples": [],
#         "critic_feedback": [],
#         "evaluation_result": "",
#         "human_feedback": [],
#         "final_post": "",
#         "iteration": 0,
#     }

#     # Create the state graph
#     graph = create_state_graph(State, generate_draft, retrieve_examples, wrapped_critic, evaluate, human_node, end_node)

#     config = RunnableConfig(
#         recursion_limit=10,
#         configurable={"thread_id": "1"},
#     )

#     response = ""

#     async for step in graph.astream(initial_state, config=config):
#         node_id = list(step.keys())[0]
#         value = step[node_id]

#         # If the graph is interrupted, collect feedback and resume
#         if node_id == "__interrupt__":
#             if feedback:
#                 step["state"]["feedback"] = feedback
#                 resumed = await graph.resume(step["state"], step["next"])
#                 response = resumed.get("candidate", {}).get("content", "")
#                 break
#             else:
#                 return JSONResponse(content={"error": "Feedback required to continue."}, status_code=400)
#         else:
#             # Save last response if it's a candidate
#             state_candidate = step.get("state", {}).get("candidate", {})
#             if isinstance(state_candidate, dict):
#                 response = state_candidate.get("content", response)

#     return JSONResponse(content={"response": response})

        
        
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
