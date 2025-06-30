import asyncio
import logging
from agent_memory import configuration, tools, utils
from datetime import datetime
from langchain.chat_models import init_chat_model # type: ignore
from langchain_core.runnables import RunnableConfig # type: ignore
from langgraph.store.base import BaseStore # type: ignore
from reflexion_agent.state import State as AgentState

llm = init_chat_model()

def ensure_runnable_config(config) -> RunnableConfig:
    if isinstance(config, dict):
        return RunnableConfig(
            recursion_limit=config.get("recursion_limit", 25),
            configurable=config.get("configurable", {})
        )
    return config

async def background_memory_saver(state: AgentState, config: RunnableConfig, *, store: BaseStore):
    logging.info("📥 Entering background_memory_saver")
    config = ensure_runnable_config(config)
    cfg_dict = config.get("configurable", {})

    convo = "\n".join(
        m.content for m in state["messages"]
        if getattr(m, "type", None) in ("human", "assistant")
    )
    prompt = f"Summarize the following conversation in concise bullet points:\n{convo}"

    model_config = RunnableConfig(configurable=utils.split_model_and_provider(cfg_dict.get("model", "openai:gpt-4.1")))
    logging.info(f"🧠 Summary prompt: {prompt}")
    logging.info(f"Model config: {model_config}")

    summary_msg = await llm.ainvoke([{"role": "user", "content": prompt}], model_config)
    summary = summary_msg.content
    logging.info(f"📝 Generated summary: {summary[:100]}...")

    await tools.upsert_memory(
        content=summary,
        context="background summary",
        config=config,
        store=store
    )


    # No update to messages, but still return full state
    return state

