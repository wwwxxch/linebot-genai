import logging

from datetime import datetime
from typing import Sequence
from typing_extensions import Annotated, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.mongodb import MongoDBSaver

from src.genai.llm_config import llm_provider_factory
from src.db.mongo_client import MongoDBClient
from src.db.cat_data import cat_data


llm = llm_provider_factory()


class ChatState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_id: str
    is_specific: bool


# Get system prompt
def create_system_prompt(specific):
    current_dt = datetime.now()
    current_y = current_dt.year

    # System prompt
    if specific:
        system_prompt = f"""
            You are an AI assistant specialized in cat health care for {cat_data["name"]}
            Cat-Specific Information:
                - Name: {cat_data['name']}
                - Birth Year: {cat_data['birth_year']}
                - Basic Information: sex is {cat_data['sex']}, breed is {cat_data['breed']}
                - Medical History: {', '.join(cat_data['medical_history'])}
            Guidelines:
                - Identify whether the question is related to cat and is related to the specific
                    cat {cat_data["name"]}, if no, answer as a general cat health expert without
                    mentioning specific cats.
                - For questions about {cat_data["name"]}, use his specific information to answer
                - If you don't have some information about {cat_data["name"]},
                    you can directly answer you don't have the information
                - Answer the questions in 繁體中文
                - If a question is not cat-related, respond: "這與貓咪照護無關，我無法回答"
            Current year is {current_y}
        """
    else:
        system_prompt = """
            You are an AI assistant specialized in cat health care
            Guidelines:
                - Only answer questions related to cats
                - Answer the questions in 繁體中文
                - If a question is not cat-related, respond: "這與貓咪照護無關，我無法回答"
        """

    return system_prompt


def check_specific(state: ChatState):
    messages = state["messages"]
    current_message = messages[-1]

    is_specific = "花花" in current_message.content
    state["is_specific"] = is_specific

    return state


def call_model(state: ChatState):
    messages = state["messages"]
    is_specific = state["is_specific"]

    system_prompt = create_system_prompt(is_specific)

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), MessagesPlaceholder(variable_name="messages")]
    )
    runnable = prompt | llm
    response = runnable.invoke({"messages": messages})
    return {"messages": [response], "is_specific": is_specific}


def create_chat_graph():
    # Create LangGraph
    workflow = StateGraph(ChatState)

    workflow.add_node("check_specific", check_specific)
    workflow.add_node("model", call_model)

    workflow.add_edge(START, "check_specific")
    workflow.add_edge("check_specific", "model")
    workflow.add_edge("model", END)

    # Compile the graph with MongoDB checkpointer
    mongodb_client = MongoDBClient.get_instance()
    checkpointer = MongoDBSaver(mongodb_client)

    return workflow.compile(checkpointer=checkpointer)


def get_ai_response(user_input, user_id):
    try:

        config = {"configurable": {"thread_id": user_id}}
        input_dict = {
            "messages": [HumanMessage(content=user_input)],
            "user_id": user_id,
            "is_specific": False,
        }
        chat_graph = create_chat_graph()
        output = chat_graph.invoke(input_dict, config)
        response = output["messages"][-1]

    except Exception as e:
        logging.error(f"Error processing query: {e}")
        return "Sorry, I am unable to process your query at the moment."

    return response.content
