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


from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages # type: ignore
from langchain_core.messages.ai import AIMessage # type: ignore


class State(TypedDict):
    user_query: str
    # NEW! Candidate for retrieval + formatted fetched examples as "memory"
    candidate: AIMessage
    examples: str
    # Repeated from Part 1
    messages: Annotated[list[AnyMessage], add_messages]
    runtime_limit: int
    status: str
    iteration: str