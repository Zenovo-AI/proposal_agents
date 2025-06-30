"""
Defines the State structure used in the agent workflow for proposal generation and critique.

Classes:
    - State: Tracks the current state of the agent, including:
        - candidate: The AI-generated proposal (AIMessage).
        - examples: Retrieved or few-shot examples used for context.
        - messages: Conversation history, compatible with LangGraph message flow.
        - runtime_limit: Execution time constraint for the agent.
        - status: Describes the current stage or condition of the workflow.

This state object is passed between agents to maintain consistency and support complex, multi-agent reasoning cycles.
"""


from enum import Enum
from typing import Annotated, List, Literal, Optional
from langchain_core.messages import BaseMessage  # type: ignore
from typing_extensions import TypedDict # type: ignore
from langgraph.graph.message import add_messages # type: ignore
from langchain_core.messages.ai import AIMessage # type: ignore
from datamodel import ProposalStructure # type: ignore


class Status(Enum):
    APPROVED = "approved"     # Final approval given by human
    NEEDS_REVISION = "revision"  # Changes requested by human
    IN_PROGRESS = "in_progress"  # Initial/ongoing state
    


class State(TypedDict):
    user_query: str
    candidate: AIMessage
    examples: str
    messages: Annotated[list[BaseMessage], add_messages]
    runtime_limit: int
    human_feedback: Annotated[List[str], add_messages]
    iteration: int
    status: Status
    rfq_id: str
    mode: str
    user_id: str
    structure: ProposalStructure      # <-- hold the dict here
    structure_message: AIMessage
    session_data: dict
    needs_clarification: bool
    intent_route: str
    should_save_memory: bool
    interrupt_type: Optional[Literal["clarification", "proposal_review"]]

