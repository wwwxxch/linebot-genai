import logging

from datetime import datetime

from langchain_core.messages import HumanMessage, RemoveMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.checkpoint.mongodb import MongoDBSaver

from src.genai.llm_config import llm_provider_factory
from src.db.mongo_client import MongoDBClient
from src.db.cat_data import cat_data


llm = llm_provider_factory()


class ChatState(MessagesState):
    user_id: str
    is_specific: bool
    summary: str


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
    # print("In call_model: len of msg: ", len(state["messages"]))
    is_specific = state["is_specific"]
    summary = state.get("summary", "")

    if summary:
        summary_message = f"Summary of conversation earlier: {summary}"
        messages = [SystemMessage(content=summary_message)] + state["messages"]
    else:
        messages = state["messages"]

    system_prompt = create_system_prompt(is_specific)

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), MessagesPlaceholder(variable_name="messages")]
    )
    runnable = prompt | llm
    response = runnable.invoke({"messages": messages})
    return {"messages": [response], "is_specific": is_specific}


def summarize_conversation(state: ChatState):
    is_specific = state["is_specific"]
    summary = state.get("summary", "")
    if summary:
        # print(f"xxxx - {summary}")
        summary_message = (
            f"This is summary of the converation to date: {summary} \n"
            "Extend the summary by taking into account the new messages above"
            "and ignore the content that is not realted to cat or cat care:"
        )
    else:
        summary_message = (
            "Create a summary of the conversation above,"
            "ignoring the content that is not related to cat or cat health care"
        )

    messages = state["messages"] + [HumanMessage(content=summary_message)]

    summary_res = llm.invoke(messages)
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    # print("In summarize_conversation: len of msg: ", len(state["messages"]))
    return {"summary": summary_res.content, "messages": delete_messages, "is_specific": is_specific}


def should_continue(state: ChatState):
    """Return the next node to execute."""

    messages = state["messages"]

    # If there are more than six messages, then we summarize the conversation
    if len(messages) > 6:
        return "summarize_conversation"

    # Otherwise we can just end
    return END


def create_chat_graph():
    # Create LangGraph
    workflow = StateGraph(ChatState)

    workflow.add_node("check_specific", check_specific)
    workflow.add_node("model", call_model)
    workflow.add_node(summarize_conversation)

    workflow.add_edge(START, "check_specific")
    workflow.add_edge("check_specific", "model")
    workflow.add_conditional_edges("model", should_continue)
    workflow.add_edge("summarize_conversation", END)

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
