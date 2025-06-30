# from langmem import create_manage_memory_tool, create_search_memory_tool # type: ignore

# # Semantic namespace
# upsert_semantic_memory = create_manage_memory_tool(namespace=("semantic", "{user_id}"))
# search_semantic_memory = create_search_memory_tool(namespace=("semantic", "{user_id}"))

# # Episodic namespace
# upsert_episodic_memory = create_manage_memory_tool(namespace=("episodic", "{user_id}"))
# search_episodic_memory = create_search_memory_tool(namespace=("episodic", "{user_id}"))

# # Procedural namespace
# upsert_procedural_memory = create_manage_memory_tool(namespace=("procedural", "{user_id}"))
# search_procedural_memory = create_search_memory_tool(namespace=("procedural", "{user_id}"))


from typing import Annotated, Optional
import uuid
from reflexion_agent.state import State
from config.appconfig import settings as app_settings
from langchain_core.tools import InjectedToolArg
from langgraph.store.base import BaseStore
from langchain_core.runnables import RunnableConfig
from agent_memory.configuration import Configuration


async def upsert_memory(
        content: str,
        context: str,
        *,
        memory_id: Optional[uuid.UUID] = None,
        # Hide these arguments from the model.
        config: Annotated[RunnableConfig, InjectedToolArg],
        store: Annotated[BaseStore, InjectedToolArg]
):
    """ Upsert a memory into the database.
    If a memory conflicts with an existing one, then just UPDATE the
    existing one by passing in memory_id - don't create two memories
    that are the same. If the user corrects a memory, UPDATE it.

    Args:
        content: The main content of the memory. For example:
            "User expressed interest in learning about French."
        context: Additional context for the memory. For example:
            "This was mentioned while discussing career options in Europe"
        memory_id: ONLY PROVIDE IF UPDATING AN EXISTING MEMORY.
        The memory to overwrite.
    """

    mem_id = memory_id or uuid.uuid4()
    user_id = Configuration.from_runnable_config(config).user_id
    await store.aput(
        ("memories", user_id),
        key=str(mem_id),
        value={"content": content, "context": context}
    )
    return f"Stored memory with ID {mem_id} for user {user_id}."