from langgraph.checkpoint.memory import MemorySaver # type: ignore
from langgraph.graph import END, StateGraph, START # type: ignore
from src.reflexion_agent.evaluate import evaluate
from src.rag_agent.inference import generate_draft
from src.reflexion_agent.critic import critic
from src.reflexion_agent.retriever import retrieve_examples
from src.reflexion_agent.state import State

builder = StateGraph(State)
builder.add_node("draft", generate_draft)
builder.add_edge(START, "draft")
builder.add_node("retrieve", retrieve_examples)
builder.add_node("critic", critic)
builder.add_node("evaluate", evaluate)
# Add connectivity
builder.add_edge("draft", "retrieve")
builder.add_edge("retrieve", "critic")
builder.add_edge("critic", "evaluate")


def control_edge(state: State):
    if state.get("status") == "success":
        return END
    return "critic"


builder.add_conditional_edges("evaluate", control_edge, {END: END, "critic": "critic"})


checkpointer = MemorySaver()
graph = builder.compile(
    checkpointer=checkpointer,
    # New: this tells the graph to break any time it goes to the "human" node
    interrupt_after=["evaluate"],
)