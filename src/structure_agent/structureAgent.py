from typing import TypedDict, List, Literal
from datamodel import ProposalStructure
from langchain_core.runnables import Runnable  # type: ignore
from langchain_openai import ChatOpenAI # type: ignore
from langchain_core.messages import AIMessage # type: ignore
from langchain_core.prompts import ChatPromptTemplate # type: ignore
from reflexion_agent.state import State
from structure_agent.defined_proposal_strucutre import proposal_structure


def create_structure_agent() -> Runnable:
    structure_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a smart technical proposal structuring agent. Based on the user query below, determine:
            - The request type: full_proposal, partial_plan, factual_query
            - The appropriate section structure (titles and subsections) for a proposal, if applicable
            - Any LOT (work phase) titles
            - Whether attachments are required

            ONLY use information implied by the query or explicitly stated. NEVER guess or hallucinate details.

            Return result in this JSON format:
            {{
            "type": "<full_proposal|partial_plan|factual_query>",
            "sections": ["<section names>"],
            "subsections": ["<subsection names>"],
            "lot_titles": ["<lot name 1>", "<lot name 2>"],
            "attachments": true|false
            }}

            User Query:
            \"\"\"{query}\"\"\"
            """
        ),
    ])


    llm = ChatOpenAI(model="gpt-4o-2024-08-06", temperature=0)
    return structure_prompt | llm.with_structured_output(schema=ProposalStructure)


structure_agent = create_structure_agent()


def structure_node(state: State) -> State:
    query = state["user_query"]
    structure_generation = structure_agent.invoke({"query": query})
    # Override structure with client-defined structure if it's a full proposal
    if structure_generation["type"] == "full_proposal":
        defined_structure = proposal_structure()
    # Store the structure both as dict (for use) and as AIMessage (for LangChain message tracking)
    structure_message = AIMessage(content=str(structure_generation))
    state["structure"] = structure_message
    return state

