"""
Defines a Pydantic model for handling requests with a query and optional section.

- `query`: The required search term.
- `section`: An optional string (defaults to "rfp_documents") specifying the data section to query.

This model ensures structured validation of incoming data for querying specific sections.
"""


from pydantic import BaseModel, Field

class RequestModel(BaseModel):
    user_query:str
    chat_history: str = Field(default=None, description="chat history for the user query")