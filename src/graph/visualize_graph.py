from reflexion_agent.human_feedback import human_node
from rag_agent.inference import generate_draft
from reflexion_agent.critic import critic as wrapped_critic
from agent_memory.langMem import google_search_agent
from intent_router.intent_router import intent_router_agent
from agent_memory.background_mem import background_memory_saver
from agent_memory.memory_storage import call_model, route_message, store_memory
from structure_agent.query_agent import query_understanding_agent
from structure_agent.structure_agent import structure_node
from reflexion_agent.retriever import retrieve_examples
from reflexion_agent.state import State
from graph.node_edges import control_edge, create_state_graph


graph = create_state_graph(
            State,
            intent_router_agent,
            structure_node, generate_draft, retrieve_examples,
            wrapped_critic, human_node, control_edge, google_search_agent,
            route_message, call_model,
            store_memory, background_memory_saver
        )

try:
    img_data = graph.get_graph().draw_mermaid_png(max_retries=5, retry_delay=2.0)
    with open("graph_output.png", "wb") as f:
        f.write(img_data)
    print("Graph saved as graph_output.png")
except Exception as e:
    print(f"Failed to save graph image: {e}")

