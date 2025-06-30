import logging
from langgraph.store.memory import InMemoryStore # type: ignore
from langgraph.checkpoint.memory import InMemorySaver # type: ignore
from langchain.embeddings import init_embeddings # type: ignore
from langgraph.graph import END, StateGraph # type: ignore
from reflexion_agent.state import State, Status
from intent_router.intent_router import route_for_rag_clarification, route_intent, safe_route_for_rag_clarification 
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
    query_understanding_agent,
    structure_node,
    retrieve_examples,      
    generate_draft,         
    critic,
    human_node,
    control_edge,
    google_search_agent,
    interrupt_for_clarification,
    route_message,
    call_model,
    store_memory,
    background_memory_saver
):
    builder = StateGraph(State)
    for name, fn in [
        ("intent_router_agent", intent_router_agent),
        ("query_understanding_agent", query_understanding_agent),
        ("structure_node", structure_node),
        ("retrieve", retrieve_examples),
        ("draft", generate_draft),
        ("critic", critic),
        ("human_interrupt", human_node),
        ("interrupt_for_clarification", interrupt_for_clarification),
        ("google_search_agent", google_search_agent),
        ("call_model", call_model),
        ("store_memory", store_memory),
        ("background_memory_saver", background_memory_saver)
    ]:
        builder.add_node(name, fn)

    print("Registered nodes:", builder.nodes.keys())
    logging.info("🚦 Available nodes right before routing: %s", list(builder.nodes.keys()))


    # Start at intent router
    builder.set_entry_point("intent_router_agent")

    # ➤ Step 1: route intent
    builder.add_conditional_edges(
        "intent_router_agent",
        route_intent,
        {
            "google_search_agent": "google_search_agent",
            "query_understanding_agent": "query_understanding_agent"
        }
    )

    logging.info("Route Decided ⭐")

    # ➤ Step 2a: if general question → go to google_search_agent → call_model
    builder.add_edge("google_search_agent", "call_model")

    # ➤ Step 2b: if rag → go to query_agent → decide if ambiguous or not
    builder.add_conditional_edges(
        "query_understanding_agent",
        safe_route_for_rag_clarification,
        {
            "structure_node": "structure_node",  # Clear → RAG pipeline
            "interrupt_for_clarification": "interrupt_for_clarification"  # Ambiguous → ask user
        }
    )
    logging.info("Route Decided with understanding query⭐")
    # ➤ RAG pipeline
    builder.add_edge("structure_node", "retrieve")
    builder.add_edge("retrieve", "draft")
    builder.add_edge("draft", "critic")
    builder.add_edge("critic", "human_interrupt")

    # ➤ Human feedback control flow
    builder.add_conditional_edges(
        "human_interrupt",
        control_edge,
        {
            "draft": "draft",                         
            "human_interrupt": "human_interrupt",                    
            "call_model": "call_model"
        }
    )

    # ➤ call_model → store or background memory
    builder.add_conditional_edges(
        "call_model",
        route_message,
        {
            "store_memory": "store_memory",
            END: "background_memory_saver"
        }
    )
    builder.add_edge("store_memory", "background_memory_saver")

    # ➤ Final memory step
    builder.add_edge("background_memory_saver", END)

    # Compile
    app = builder.compile(store=store, checkpointer=InMemorySaver())
    return app