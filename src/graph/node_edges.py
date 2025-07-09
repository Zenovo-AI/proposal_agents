import logging
from langgraph.store.memory import InMemoryStore # type: ignore
from langgraph.checkpoint.memory import InMemorySaver # type: ignore
from langchain.embeddings import init_embeddings # type: ignore
from langgraph.graph import END, StateGraph # type: ignore
from reflexion_agent.state import State, Status
from intent_router.intent_router import route_intent, route_response_type 
from langchain_core.runnables import RunnableLambda # type: ignore

# Initialize semantic InMemoryStore
embeddings = init_embeddings("openai:text-embedding-3-small")
store = InMemoryStore(index={"embed": embeddings, "dims": 1536})

def control_edge(state: State):
    """Control flow for the graph based on state"""
    print("[control_edge] Current status:", state["status"])

    match state["status"]:
        case Status.APPROVED:
            print("-> Ending graph execution")
            return "call_model"
        case Status.NEEDS_REVISION:
            state["iteration"] += 1
            return "draft"
        case Status.IN_PROGRESS:
            return "human_interrupt"
        case _:
            return "human_interrupt"


def create_state_graph(
    State,
    intent_router_agent,
    response_type_router_agent,
    proposal_generate_draft,
    factual_generate_draft,
    structure_node,
    retrieve_examples,
    critic,
    human_node,
    control_edge,
    google_search_agent,
    route_message,
    call_model,
    store_memory,
    background_memory_saver
):
    builder = StateGraph(State)

    # ⚙️ Register nodes
    nodes = {
        "intent_router": intent_router_agent,
        "response_router": response_type_router_agent,
        "structure_node": structure_node,
        "retrieve": retrieve_examples,
        "proposal_draft": proposal_generate_draft,
        "factual_draft": factual_generate_draft,
        "critic": critic,
        "human_interrupt": human_node,
        "google_search": google_search_agent,
        "call_model": call_model,
        "store_memory": store_memory,
        "background_saver": background_memory_saver
    }
    for name, fn in nodes.items():
        builder.add_node(name, fn)

    logging.info("Registered nodes: %s", builder.nodes.keys())

    # 🎯 Entry point
    builder.set_entry_point("intent_router")

    # ➤ Intent-based routing: direct vs rag
    builder.add_conditional_edges(
        "intent_router",  # returns 'direct' or 'rag'
        lambda state: state["intent_route"],
        {
            "direct": "google_search",
            "rag": "response_router"
        }
    )
    logging.info("Intent routing configured")

    # ➤ Direct path: google search → respond
    builder.add_edge("google_search", "call_model")

    # ➤ RAG path: decide response type (factual vs proposal)
    builder.add_conditional_edges(
        "response_router",  # returns 'simple_answer' or 'full_proposal'
        lambda state: state["response_type"],
        {
            "simple_answer": "factual_draft",
            "full_proposal": "structure_node"
        }
    )
    logging.info("Response-type routing configured")

    # ➤ Factual path: factual draft → final (no human)
    builder.add_edge("factual_draft", END)
    logging.info("Factual path ends after draft")
    
    # ➤ Ensure factual_draft doesn't go to human_interrupt
    logging.info("Factual draft configured to end directly")

    # ➤ Proposal path: RAG pipeline with human feedback
    builder.add_edge("structure_node", "retrieve")
    builder.add_edge("retrieve", "proposal_draft")
    builder.add_edge("proposal_draft", "critic")
    builder.add_edge("critic", "human_interrupt")

    builder.add_conditional_edges(
        "human_interrupt",
        control_edge,
        {
            "proposal_draft": "proposal_draft",  # loop back for revision
            "human_interrupt": "human_interrupt",  # retry human feedback
            "call_model": "call_model"  # fallback or escalate
        }
    )

    # ➤ Post-call memory steps (shared by all paths)
    builder.add_conditional_edges(
        "call_model",
        route_message,
        {
            "store_memory": "store_memory",
            END: "background_saver"
        }
    )
    builder.add_edge("store_memory", "background_saver")
    builder.add_edge("background_saver", END)

    # 🔁 Compile
    app = builder.compile(store=store, checkpointer=InMemorySaver())
    return app