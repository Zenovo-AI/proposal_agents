import json
import logging
from langchain_community.tools.tavily_search import TavilySearchResults # type: ignore
from langgraph.prebuilt.tool_node import ToolNode # type: ignore
from langchain_openai import ChatOpenAI # type: ignore
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage # type: ignore
from langchain_core.utils.function_calling import convert_to_openai_function # type: ignore
from reflexion_agent.state import State # type: ignore
from config.appconfig import settings as app_settings
from langgraph.store.base import BaseStore # type: ignore
from langchain_core.runnables import RunnableConfig # type: ignore
from agent_memory import utils # type: ignore

logging.basicConfig(level=logging.INFO)

tools = [TavilySearchResults(tavilyApiKey=app_settings.tavily_api_key, max_results=1)]
tool_executor = ToolNode(tools)

llm = ChatOpenAI(model="gpt-4.1", temperature=0)
functions = [convert_to_openai_function(t) for t in tools]
model = llm.bind_tools(functions)

async def google_search_agent(state: State, config, store: BaseStore) -> State:
    logging.info("🚦 google_search_agent start; message count=%d", len(state["messages"]))

    cfg = config.get("configurable", {})
    model_name = cfg.get("model", "gpt-4o-search-preview")  # supports web search

    # 1️⃣ Append the user's question
    user_msg = HumanMessage(content=state["user_query"])
    state["messages"].append(user_msg)
    logging.info("➡️ User query: %s", state["user_query"])

    # 2️⃣ Call LLM with built-in `web_search` tool enabled
    msg: AIMessage = await llm.ainvoke(
        state["messages"],
        {
          "configurable": utils.split_model_and_provider(
            RunnableConfig(configurable={
              "model": model_name,
              "tools": [{"type": "web_search"}]
            })
          )
        }
    )
    logging.info("LLM replied; tool_calls=%s", getattr(msg, "tool_calls", None))

    new_msgs = [msg]
    state["generated_response"] = msg.content or ""

    # 3️⃣ If LLM issued tool_calls, execute them
    for call in getattr(msg, "tool_calls", []) or []:
        if call["name"] == "web_search":
            call_id = call["id"]
            query = call["args"]["query"]
            logging.info("📡 Performing web_search for: %s", query)

            result = await llm.call_tool({
              "tool": "web_search",
              "arguments": {"query": query}
            })

            tool_msg = ToolMessage(
                content=json.dumps(result),
                name="web_search",
                tool_call_id=call_id
            )
            new_msgs.append(tool_msg)
            logging.info("🔧 Appended Web Search ToolMessage with call_id=%s", call_id)

    # 4️⃣ If we ran web_search, get final answer
    if len(new_msgs) > 1:
        follow_up: AIMessage = await llm.ainvoke(
            new_msgs + state["messages"],
            {
              "configurable": utils.split_model_and_provider(
                RunnableConfig(configurable={"model": model_name})
              )
            }
        )
        new_msgs.append(follow_up)
        state["generated_response"] = follow_up.content
        logging.info("🤖 Follow-up response: %s", follow_up.content)

    return {"messages": new_msgs, "generated_response": state["generated_response"]}


# def google_search_agent(state: State, *, store: BaseStore) -> State:
#     """Agent that optionally searches the web and responds."""
#     logging.info("🚦 Starting google_search_agent; messages count = %d", len(state["messages"]))

#     # Add user's query to the messages
#     state["messages"].append(HumanMessage(content=state["user_query"]))
#     logging.info("➡️ Appended HumanMessage: %s", state["user_query"])

#     # First LLM call to check for tool calls
#     response: AIMessage = model.invoke(state["messages"])
#     logging.info("LLM response received: %s", response.content)

#     # Append assistant response (which may contain tool_calls)
#     state["messages"].append(response)
#     logging.info("Assistant response %s", state.get("messages"))
#     new_messages = [response]
#     state["generated_response"] = response.content

#     # Process tool calls if any
#     tool_calls = getattr(response, "tool_calls", None)
#     logging.info("Detected tool_calls: %s", tool_calls)

#     if tool_calls:
#         tool_outputs = []

#         for tool_call in tool_calls:
#             logging.info("🔧 Processing tool call: %s", tool_call)

#             try:
#                 # Execute the tool (passing the tool_call properly)
#                 executor_input = {"messages": state["messages"]}
#                 result = tool_executor.invoke(executor_input)
#                 logging.info("Tool output: %s", result)

#                 for tm in result.get("messages", []):
#                     # Append ToolMessage to both state and output
#                     state["messages"].append(tm)
#                     tool_outputs.append(tm)

#             except Exception:
#                 logging.exception("Error invoking tool: %s", tool_call)

#         # Second LLM call with all tool responses included
#         followup: AIMessage = model.invoke(state["messages"])
#         logging.info("Follow-up LLM response: %s", followup.content)

#         state["messages"].append(followup)
#         new_messages.extend(tool_outputs)
#         new_messages.append(followup)
#         state["generated_response"] = followup.content

#     return {
#         "messages": new_messages,
#         "generated_response": state["generated_response"]
#     }
