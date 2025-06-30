import logging
import asyncio
from datetime import datetime
from langchain.chat_models import init_chat_model # type: ignore
from langchain_core.runnables import RunnableConfig # type: ignore
from langgraph.graph import END # type: ignore
from langgraph.store.base import BaseStore # type: ignore

from agent_memory import configuration, memory_storage, tools, utils
from agent_memory.background_mem import ensure_runnable_config
from reflexion_agent.state import State as AgentState

logger = logging.getLogger(__name__)

llm = init_chat_model("openai:gpt-4.1")

async def call_model(state: AgentState, config: RunnableConfig, *, store: BaseStore) -> dict:
    """"Extract the user's state from the conversation and update the memory"""
    configurable = configuration.Configuration.from_runnable_config(config)

    # Retrieve the most recent memories for context
    memories = await store.asearch(
        (configurable.user_id, "memories"),
        query=state["query"],
        limit=10,
    )

    # Format memories for inclusion in the prompt
    formatted = "\n".join(f"[{mem.key}]: {mem.value} (similarity: {mem.score})" for mem in memories)
    if formatted:
        formatted = f"""
<memories>
{formatted}
</memories>
"""
        
    # Prepare system prompt with user memories and current time
    # This helps the model understand the context and temporal relevance
    sys = configurable.system_prompt.format(
        user_info=formatted, time=datetime.now().isoformat()
    )

    # invoke the language model with the prepared prompt and tools
    # "bind_tools" gives the LLM the JSON schema for all tools in the list so it knows how to use them
    msg = await llm.bind_tools([tools.upsert_memory]).ainvoke(
        [{"role": "system", "content": sys}, *state.messages],
        {"configurable": utils.split_model_and_provider(configurable.model)},
    )
    return {"messages": [msg]}

