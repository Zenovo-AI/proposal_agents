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


from langchain_community.document_loaders import PyPDFLoader # type: ignore
from langchain_core.runnables import RunnableConfig # type: ignore
from langchain_core.messages.ai import AIMessage # type: ignore
from langchain_community.retrievers import BM25Retriever # type: ignore
from src.reflexion_agent.state import State

loader = PyPDFLoader(r"C:\Users\Nigga-X\Authur\proposalGenerator_Agent\src\doc\ctbto_rfq_no._2024-0108_cdga_technical_proposal.pdf")
documents = loader.load_and_split()

retriever = BM25Retriever.from_documents(documents)

def retrieve_examples(state: State, config: RunnableConfig):
    top_k = config["configurable"].get("k") or 2
    ai_message: AIMessage = state["candidate"]

    query = ai_message.content.strip()
    if not query:
        raise ValueError("No candidate proposal to critique.")

    retrieved_docs = retriever.invoke(query)[:top_k]
    examples_str = "\n---\n".join(doc.page_content for doc in retrieved_docs)

    print("[retrieve_examples] Retrieved Examples Preview:", examples_str[:500])

    examples_str = f"""You previously wrote the following proposals:
    <RetrievedProposals>
    {examples_str}
    </RetrievedProposals>

    Critique the current proposal by comparing it to the above."""
    
    state["examples"] = examples_str
    state["status"] = "examples_retrieved"

    return state
