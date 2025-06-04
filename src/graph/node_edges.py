from langgraph.checkpoint.memory import InMemorySaver # type: ignore
from langgraph.graph import END, StateGraph, START # type: ignore
from reflexion_agent.state import State, Status


def control_edge(state: State):
    """Control flow for the graph based on state"""
    print("[control_edge] Current status:", state["status"])

    match state["status"]:
        case Status.APPROVED:
            print("-> Ending graph execution")
            return END
        case Status.NEEDS_REVISION:
            state["iteration"] += 1
            return "draft"
        case Status.IN_PROGRESS:
            return "human_interrupt"
        case _:
            return "human_interrupt"

        
        

def create_state_graph(State, structure_node, generate_draft, retrieve_examples, critic, human_node, control_edge):
    builder = StateGraph(State)

    builder.add_node("structure_generation", structure_node)
    builder.add_node("draft", generate_draft)
    builder.add_node("retrieve", retrieve_examples)
    builder.add_node("critic", critic)
    builder.add_node("human_interrupt", human_node)

    builder.set_entry_point("structure_generation")

    builder.add_edge(START, "structure_generation")
    builder.add_edge("structure_generation", "draft")
    builder.add_edge("draft", "retrieve")
    builder.add_edge("retrieve", "critic")
    builder.add_edge("critic", "human_interrupt")

    builder.add_conditional_edges(
        "human_interrupt",
        control_edge,
        {
            END: END,
            "draft": "draft",
            "human_interrupt": "human_interrupt"
        }
    )

    checkpointer = InMemorySaver()

    return builder.compile(checkpointer=checkpointer)


