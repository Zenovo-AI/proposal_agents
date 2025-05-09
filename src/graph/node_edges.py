from langgraph.checkpoint.memory import MemorySaver  # type: ignore
from langgraph.graph import END, StateGraph, START  # type: ignore
from src.reflexion_agent.state import State  # Assuming State is in the correct location

def control_edge(state: State):
    if state.get("status") == "success":
        return END
    return "draft"

def create_state_graph(State, generate_draft, retrieve_examples, critic, evaluate):
    # Initialize the graph builder
    builder = StateGraph(State)

    # Add the start node to initialize user_query
    # builder.add_node("start_node", start_node)

    # Build the state machine by adding nodes and edges
    builder.add_node("draft", generate_draft)
    builder.add_edge(START, "draft")
    builder.add_node("retrieve", retrieve_examples)
    builder.add_node("critic", critic)
    builder.add_node("evaluate", evaluate)

    # Add transitions (edges) between nodes
    builder.add_edge("draft", "retrieve")
    builder.add_edge("retrieve", "critic")
    builder.add_edge("critic", "evaluate")

    # Conditional edges from "evaluate"
    builder.add_conditional_edges("evaluate", control_edge, {END: END, "draft": "draft"})

    # Initialize the checkpointer
    checkpointer = MemorySaver()

    # Compile the graph with interrupt functionality
    graph = builder.compile(
        checkpointer=checkpointer,
        # Interrupt when the flow reaches the "evaluate" node
        interrupt_after=["evaluate"]
    )
    
    return graph
