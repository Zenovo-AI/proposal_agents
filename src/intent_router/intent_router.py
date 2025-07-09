"""
Intent Router Module
This module defines the intent router that determines the next action based on the current state.
"""


from reflexion_agent.state import State
from langgraph.types import interrupt # type: ignore
import logging
from langchain_openai import ChatOpenAI # type: ignore
from langchain_core.messages import HumanMessage, SystemMessage # type: ignore
from reflexion_agent.state import State # type: ignore
from openai import AsyncOpenAI # type: ignore
from config.appconfig import settings as app_settings
import logging
from langchain_core.prompts import ChatPromptTemplate # type: ignore

llm = ChatOpenAI(model="gpt-4.1", openai_api_key=app_settings.openai_api_key, temperature=0)


async def intent_router_agent(state: State) -> State:
    query = state.get("user_query", "").strip()
    if not query:
        state["intent_route"] = "direct"
        return state

    # 🔍 Strong deterministic routing prompt
    system_prompt = f"""
    You are CDGA-AI, an intelligent intent classification agent.

    You must think deeply about user's query** and know that 99% of query** must be classify as **rag**

    You help route user queries to one of two processing pipelines:
    1. `direct`: for simple greetings or questions about you only.
    2. `rag`: for anything involving RFQs, proposals, CTBTO, CDGA, document-based knowledge, technical steps, warranties, or organizational experience.

    You must **critically analyze the user's query** and make a precise decision.
    This decision controls whether the system retrieves and reasons over uploaded documents.

    INSTRUCTIONS:
    - If the query involves CDGA, CTBTO, RFQs, uploaded documents, or technical/factual project details, respond with: **rag**
    - If the query is a greeting, or question about you, respond with: **direct**

    RULES:
    1. Always map queries involving:
    - keywords: **RFQ**, **proposal**, **CTBTO**, **CDGA experience**, **document**, **uploaded file**, **technical steps**, **warranty**, **steps in Lot**, etc.
    - deeper facts inside documents (e.g. “What are the steps proposed…”, “Summarize CDGA’s approach to…”, “Write a proposal against…”) → to **rag**.
    2. NEVER MAP TO DIRECT IF THE QUERY CONTAIN ANY OF THESE:
    - keywords: **RFQ**, **proposal**, **CTBTO**, **CDGA experience**, **document**, **uploaded file**, **technical steps**, **warranty**, **steps in Lot**, etc
    3. Never map to direct if the query contain some of these phrases:
    - What are the steps proposed…
    - Summarize CDGA’s approach to
    - Write a proposal against

    EXAMPLES:
    - "Hi there!" → direct
    - "Who are you?" → direct
    - "What experience does CDGA have working with CTBTO?" → rag
    - "Summarize warranty terms in the last RFQ response." → rag
    - "Can you write a proposal against the uploaded CTBTO RFQ?" → rag

    Now analyze this query:  
    **"{query}"**

    Respond only with one word: `direct` or `rag`
    """

    try:
        client = AsyncOpenAI(api_key=app_settings.openai_api_key)
        response = await client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.0
        )
        decision = response.choices[0].message.content.strip().lower()
    except Exception as e:
        logging.error(f"Routing failed: {e}")
        decision = "direct"

    #  Validate and assign
    if decision not in {"direct", "rag"}:
        decision = "direct"

    state["intent_route"] = decision
    logging.info("🚦 Routing decision: %s", decision)
    return state


async def response_type_router_agent(state: State) -> State:
    logging.info("Running response_type_router_agent with state")
    query = state.get("user_query", "").strip()
    if not query:
        state["response_type"] = "simple_answer"
        return state

    # System prompt for classification
    system_prompt = f"""
    You are CDGA-AI, a smart classification agent that routes a user query to either:
    
    1. `simple_answer`: for direct, short factual answers based on documents or common knowledge.
    2. `full_proposal`: for requests that involve writing structured responses such as proposals, drafts, or multi-step technical narratives.

    🔍 INSTRUCTIONS:
    Carefully analyze the user's query and determine the best response type.

    - If the query asks for:
        - a brief factual answer
        - quick technical clarification
        - summaries
        - definitions
      → classify as `simple_answer`

    - If the query asks for:
        - writing a proposal
        - preparing a draft
        - outlining a technical or organizational approach
        - generating responses to RFQs or CTBTO documents
      → classify as `full_proposal`

    ⚠️ RULES:
    - Always choose `full_proposal` if the query mentions "write a proposal", "draft", "prepare response", or is clearly seeking a formal or structured deliverable.
    - Do not choose `simple_answer` if the response would be reviewed by humans or sent to external partners.
    
    🔎 EXAMPLES:
    - "What is CDGA's role in the CTBTO RFQ?" → simple_answer
    - "Can you draft a proposal for the uploaded RFQ?" → full_proposal
    - "Summarize CDGA's past experience on borehole drilling." → simple_answer
    - "Write a full proposal for the CTBTO site inspection." → full_proposal

    Now analyze the following user query:

    **"{query}"**

    Respond with only one word: `simple_answer` or `full_proposal`
    """

    # Replace this with your actual LLM call
    response_type = await llm.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=query)
    ])
    response_type = response_type.content.strip().lower()

    if response_type not in {"simple_answer", "full_proposal"}:
        response_type = "simple_answer"

    state["response_type"] = response_type
    logging.info("🚦 Response type decision: %s", response_type)
    return state


def route_response_type(state: State) -> str:
    """
    Route based on the response type determined by the response_type_router_agent.
    """
    response_type = state.get("response_type", "").lower().strip()
    
    if response_type == "full_proposal":
        return "proposal_generate_draft"
    elif response_type == "simple_answer":
        return "factual_generate_draft"
    
    logging.warning(f"Unrecognized response type: {response_type}, defaulting to factual_generate_draft")
    return "factual_generate_draft"


def route_intent(state: State) -> str:
    route = state.get("intent_route", "").lower().strip()
    if route == "rag":
        return "structure_node"
    elif route == "direct":
        return "google_search_agent"
    else:
        logging.warning(f"Unrecognized route: {route}, defaulting to google_search_agent")
        return "google_search_agent"



def route_by_route_type(state: dict) -> str:
    route = state.get("route", "")
    needs_clarification = state.get("needs_clarification", "False")

    if route == "direct":
        if needs_clarification == "True":
            return "interrupt_for_clarification"
        else:
            return "google_search_agent"

    elif route == "rag":
        return "check_rag_clarification"

    return "fallback_handler"


def route_for_rag_clarification(state: dict) -> str:
    if state.get("needs_clarification") == "True":
        return "interrupt_for_clarification"
    else:
        return "structure_node"
    

def safe_route_for_rag_clarification(state: dict) -> str:
    route = None
    try:
        route = route_for_rag_clarification(state)
        logging.info("🔁 Routing from query_understanding_agent → %s", route)
        return route
    except Exception as e:
        logging.error(f"🔥 Error inside route_for_rag_clarification: {e}")
        logging.error(f"🔎 State at error: {state}")
        # This helps catch missing route mappings in your graph
        raise RuntimeError(f"Invalid route returned: '{route}' from route_for_rag_clarification")





async def interrupt_for_clarification(state: State, config) -> str:
    query = state.get("user_query", "")

    system_prompt = (
        "You are CDGA-AI, a professional assistant developed by CDGA — an Irish-based technical consultancy "
        "established in 1998 with over 25 years of global experience in engineering design, consultancy, and training. "
        "CDGA-AI supports users by answering technical and operational questions related to complex systems and workflows.\n\n"

        "The user has submitted a vague or ambiguous query. Your task is to ask the user to kindly clarify their question. "
        "In addition, provide 3–4 clearer and more specific reworded versions of their original query. These suggestions should be phrased in a way that helps the user express their intent more precisely and can be easily copied and pasted.\n\n"
        
        "Maintain a helpful, respectful, and professional tone in your response."
    )

    response = await llm.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=query)
    ])

    return interrupt(response.content)




def detect_intent(user_query) -> str:
    """
    Analyze user_query to determine intent: either "full_proposal" or "simple_answer".
    Uses GPT‑4.1—no additional logic or clarification.
    """

    prompt = ChatPromptTemplate.from_template(
        "You are an assistant for CDGA.\n"
        "Classify the following user query's intent as either "
        "'full_proposal' (they want a complete proposal) or 'simple_answer' "
        "(they want a brief informational response).\n\n"
        "User query:\n"
        "{user_query}\n\n"
        "Respond with exactly one word: full_proposal or simple_answer."
    )
    llm = ChatOpenAI(model="gpt-4.1", temperature=0.0)
    out = llm.invoke(prompt.format_prompt(user_query=user_query))
    query_intent = out.content.strip()
    if query_intent not in ("full_proposal", "simple_answer"):
        query_intent = "simple_answer"
    logging.info("User intent: %s", query_intent)

    return query_intent



def critic_route(state: dict) -> str:
    # If loop count is less than 2, go back to draft
    return "draft" if state.get("critic_loops", 0) < 2 else "human_interrupt"