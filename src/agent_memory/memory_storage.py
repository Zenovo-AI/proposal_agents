from datetime import datetime
import logging
from agent_memory import configuration, memory_storage, tools, utils
from langchain.chat_models import init_chat_model # type: ignore
from reflexion_agent.state import State
from langchain_core.runnables import RunnableConfig  # type: ignore
from langgraph.graph import END # type: ignore
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage  # type: ignore
from langgraph.store.base import BaseStore  # type: ignore

logger = logging.getLogger(__name__)

def sanitize_user_id(user_id: str) -> str:
    return user_id.replace(".", "_").replace("@", "_at_")

DEFAULT_SYSTEM_PROMPT = "You are CDGA-AI, a memory-savvy assistant. Use the provided memories and context to help the user."
EXTRACT_FACTS_PROMPT = "Extract any personal info or preferences in this text, return only the fact"

# initialize language model that will be used for memory extraction
llm = init_chat_model("openai:gpt-4.1")

async def call_model(state: State, config: RunnableConfig, *, store: BaseStore) -> dict:
    """"Extract the user's state from the conversation and update the memory"""
    logging.info("📥 Entering call_model")
    cfg_dict = config.get("configurable", {})
    user_id = cfg_dict.get("user_id")
    if not user_id:
        raise ValueError("Missing 'user_id' in config.configurable")
    
    system_prompt_tmpl = cfg_dict.get(
    "system_prompt",
    """You are a Junify-AI assistant using memory.
    If a user says anything about their name, preferences, goals, or important facts,
    store them using the correct memory tool.
    Use semantic memory for self-related facts like names.
    {user_info}
    """
    )

    model = cfg_dict.get("model", "openai:gpt-4.1")

    # Retrieve the most recent memories for context
    logging.info("📆 Retrieving recent memories...")
    memories = await store.asearch(
        (user_id, "memories"),
        query=state["user_query"],
        limit=10,
    )

    logging.info(f"🧠 Retrieved {len(memories)} memories: {[m.value for m in memories]}")

    # Format memories for inclusion in the prompt
    formatted = "\n".join(f"[{mem.key}]: {mem.value} (similarity: {mem.score})" for mem in memories)
    if formatted:
        formatted = f"""
<memories>
{formatted}
</memories>
"""
        logging.info(f"Formatted memories:\n{formatted}")
        
    # Prepare system prompt with user memories and current time
    # This helps the model understand the context and temporal relevance
    sys_msg = system_prompt_tmpl.format(user_info=formatted, time=datetime.now().isoformat())
    logging.info(f"System prompt to be used:\n{sys_msg}")
    model_config = RunnableConfig(configurable={"model": model})
    user_msgs = state.get("messages", [])

    # invoke the language model with the prepared prompt and tools
    # "bind_tools" gives the LLM the JSON schema for all tools in the list so it knows how to use them
    msg = await llm.bind_tools([tools.upsert_memory]).ainvoke(
        [{"role": "system", "content": sys_msg}, *user_msgs],
        {"configurable": utils.split_model_and_provider(model_config)},
    )

    # llm_msg = await llm.bind_tools([tools.upsert_memory]).ainvoke(
    #     [{"role": "system", "content": sys_prompt}] + user_msgs,
    #     {"configurable": utils.split_model_and_provider(model_cfg)}
    # )

    # Handle tool calls
    content = msg.content or ""
    if getattr(msg, "tool_calls", None):
        for tc in msg.tool_calls:
            await tools.upsert_memory(
                content=tc["args"]["content"],
                context=tc["args"]["context"],
                config=config,
                store=store
            )

    logging.info("✅ LLM returned a message via bind_tools")

    extracted_msg = await llm.ainvoke([
        {"role": "system", "content": "Extract any personal info or preferences in this text, return only the fact"},
        *user_msgs  # include user messages so the model has context
    ], {"configurable": utils.split_model_and_provider(config)})

    extracted = extracted_msg.content if extracted_msg else None

    if extracted:
        await tools.upsert_memory(
            content=extracted,
            context="Extracted automatically",
            config=config,
            store=store
        )
        logging.info(f"👉 Stored memory automatically: {extracted}")

    
    # ✅ Preserve full state and add response
    assistant_msg = {"role": "assistant", "content": content}
    state["should_save_memory"] = True
    state["messages"].append(assistant_msg)
    # Only set generated_response if the message has actual content (not just tool calls)
    if msg.content:
        state["generated_response"] = msg.content
    else:
        # Optionally keep the previous response or leave it unchanged
        logging.info("⚠️ Tool call message had no content; preserving previous response.")

    

    logging.info("[call_model] state now: %s", {k: v for k, v in state.items() if k != "messages"})

    logging.info("[call_model] Output: %s", state)
    return state


async def store_memory(state: State, config: RunnableConfig, *, store: BaseStore):
    logging.info("📥 Entering store_memory")
    cfg = configuration.Configuration.from_runnable_config(config)
    user_id = cfg.user_id

    # Save explicit memories from prior step
    for mem in state.get("memories_to_save", []):
        await tools.upsert_memory(
            user_id=user_id,
            content=mem,
            context="document_route",
            config=config,
            store=store
        )
        logging.info(f"✅ Saved explicit memory: {mem!r}")

    # Save from tool_calls in last assistant message
    last_msg = state.get("messages", [])[-1] if state.get("messages") else None
    for tc in getattr(last_msg, "tool_calls", []) or []:
        args = tc.get("args", {})
        await tools.upsert_memory(
            user_id=user_id,
            content=args.get("content", ""),
            context=args.get("context", ""),
            config=config,
            store=store
        )
        logging.info(f"✅ Saved memory from tool_call: {args.get('content')!r}")

    return state


def route_message(state: State):
    """Route the message based on the state."""
    return "store_memory" if state["should_save_memory"] else END