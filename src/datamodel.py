"""
Defines a Pydantic model for handling requests with a query and optional section.

- `query`: The required search term.
- `section`: An optional string (defaults to "rfp_documents") specifying the data section to query.

This model ensures structured validation of incoming data for querying specific sections.
"""


from typing import List, Literal, TypedDict
from pydantic import BaseModel, Field # type: ignore
from enum import Enum

class RequestModel(BaseModel):
    user_query:str
    chat_history: str = Field(default=None, description="chat history for the user query")
    feedback: str | None = None


class Status(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class ProposalStructure(TypedDict):
    type: Literal["full_proposal", "partial_plan", "factual_query"]
    sections: List[str]
    subsections: List[str]
    lot_titles: List[str]
    attachments: bool

class QueryRequest(BaseModel):
    query: str

