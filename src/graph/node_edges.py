from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph, START
from src.reflexion_agent.state import State, Status


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

        
        

def create_state_graph(State, generate_draft, retrieve_examples, critic, human_node, control_edge):
    builder = StateGraph(State)

    builder.add_node("draft", generate_draft)
    builder.add_node("retrieve", retrieve_examples)
    builder.add_node("critic", critic)
    builder.add_node("human_interrupt", human_node)

    builder.set_entry_point("draft")

    builder.add_edge(START, "draft")
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

    checkpointer = MemorySaver()

    return builder.compile(checkpointer=checkpointer)



# def control_edge(state: State):
#     """Control flow for the graph based on state"""
    
#     # Check status
#     if state["status"] == Status.APPROVED:
#         return END
#     elif state["status"] == Status.NEEDS_REVISION:
#         state["iteration"] += 1
#         return "draft"
    
#     # Default to continuing the draft process
#     return "draft"

# def create_state_graph(State, generate_draft, retrieve_examples, critic, human_node, control_edge):
#     # Initialize the graph builder
#     builder = StateGraph(State)

#     # Build the state machine by adding nodes and edges
#     builder.add_node("draft", generate_draft)
#     builder.add_node("retrieve", retrieve_examples)
#     builder.add_node("critic", critic)
#     # builder.add_node("evaluate", evaluate)
#     builder.add_node("human_interrupt", human_node)
#     # builder.add_node("end_node", end_node)

#     builder.set_entry_point("draft")


#     # Add transitions (edges) between nodes
#     builder.add_edge(START, "draft")
#     builder.add_edge("draft", "retrieve")
#     builder.add_edge("retrieve", "critic")
#     builder.add_edge("critic", "human_interrupt")
#     # builder.add_edge("evaluate", "human_interrupt")
#     # builder.add_edge("human_interrupt", control_edge)


# #     builder.add_conditional_edges(
# #     "evaluate",
# #     lambda state: "draft" if state["iteration"] < 2 else "human_interrupt",
# #     {
# #         "draft": "draft",
# #         "human_interrupt": "human_interrupt",
# #     }
# # )

#     # builder.set_finish_point("end_node")

#     # Conditional edges from "evaluate"
#     builder.add_conditional_edges("human_interrupt", control_edge, {END: END, "draft": "draft"})

#     # Initialize the checkpointer
#     checkpointer = MemorySaver()

#     # Compile the graph with interrupt functionality
#     graph = builder.compile(
#         checkpointer=checkpointer,
#     )
    
#     return graph


