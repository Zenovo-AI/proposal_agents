"""
This module loads a PDF document and sets up a retriever to find similar examples from it.

- It uses `PyPDFLoader` to read and split a PDF into separate text chunks (documents).
- Then it creates a `BM25Retriever`, which is a simple text search engine that ranks documents based on keyword relevance.
- The `retrieve_examples` function takes in the current application state and a configuration object:
    - It extracts the user's current proposal (from state).
    - It searches for the top `k` most relevant past examples from the PDF.
    - It returns these examples wrapped in tags, ready to be used for comparison or critique.

This is helpful for applications where a user writes proposals, and you want to fetch past examples to improve or critique the new one.
"""

import os
from langchain_community.document_loaders import PyPDFLoader # type: ignore
from langchain_unstructured import UnstructuredLoader # type: ignore
from langchain_core.runnables import RunnableConfig # type: ignore
from langchain_core.messages.ai import AIMessage # type: ignore
from langchain_community.retrievers import BM25Retriever # type: ignore
from reflexion_agent.state import State

# Go up one level from reflexion_agent to src
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file_path = os.path.join(base_dir, "doc", "ctbto_rfq_no._2024-0108_cdga_technical_proposal.pdf")


# Load PDF
if os.path.exists(file_path):
    print(f"Loading PDF: {file_path}")
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    print(f"Successfully loaded {len(documents)} pages.")
else:
    raise FileNotFoundError(f"The file was not found at: {file_path}")


retriever = BM25Retriever.from_documents(documents)


# def retrieve_examples(state: State, config: RunnableConfig):
#     top_k = config["configurable"].get("k") or 2
#     query = state["candidate"].content.strip()  # it's just a string now

#     if not query:
#         raise ValueError("No candidate proposal to critique.")

#     retrieved_docs = retriever.invoke(query)[:top_k]
#     examples_str = "\n---\n".join(doc.page_content for doc in retrieved_docs)

#     print("[retrieve_examples] Retrieved Examples Preview:", examples_str[:500])

#     examples_str = f"""You previously wrote the following proposals:
#     <RetrievedProposals>
#     {examples_str}
#     </RetrievedProposals>
    
#     Critique the current proposal by comparing it to the above."""

#     state["examples"] = examples_str
#     state["status"] = "examples_retrieved"

#     return state

async def retrieve_examples(state: State, config: RunnableConfig) -> dict:
    # Perform retrieval
    query = state["user_query"].strip()
    if not query:
        raise ValueError("No user query provided for retrieval.")

    docs = retriever.invoke(query)  # fetch all relevant docs

    # Store complete documents for later use
    state["retrieved_docs"] = docs

    # For critique/comparison contexts, concatenate full content
    examples_str = "\n---\n".join(doc.page_content for doc in docs)
    print("[retrieve_examples] Retrieved examples preview:", examples_str[:500])

    state["examples"] = examples_str
    state["status"] = "examples_retrieved"

    return state
