from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, HumanMessage

from typing import Sequence
from typing_extensions import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.mongodb import MongoDBSaver

from src.genai.llm_config import llm_provider_factory
from src.db.mongo_client import MongoDBClient


# Initialize the LLM
llm = llm_provider_factory()

# Define the prompt template
system_prompt = """
    You are a helpful AI assistant. Respond to the user's messages in a natural and informative way.
"""

prompt = ChatPromptTemplate.from_messages(
    [("system", system_prompt), MessagesPlaceholder(variable_name="messages")]
)

runnable = prompt | llm


# Define the state for the graph
class ChatState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_id: str


# Define the function to call the model
def call_model(state: ChatState):
    messages = state["messages"]
    response = runnable.invoke({"messages": messages})
    return {"messages": [response]}


# Create the LangGraph
workflow = StateGraph(ChatState)

# Define nodes:
workflow.add_node("model", call_model)

# Define edges:
workflow.add_edge(START, "model")  # workflow.set_entry_point("model")
workflow.add_edge("model", END)  # Loop back for continuous conversation

# Compile the graph with MongoDB checkpointer
mongodb_client = MongoDBClient.get_instance()
checkpointer = MongoDBSaver(mongodb_client)
app = workflow.compile(checkpointer=checkpointer)


def run_chatbot():
    print("Welcome to the Chatbot! Enter Ctrl+C to exit.")
    while True:
        try:
            user_id = input("Enter your User ID: ")
            message = input("Your message: ")
            print("\n")

            config = {"configurable": {"thread_id": user_id}}
            input_dict = {"messages": [HumanMessage(content=message)], "user_id": user_id}

            output = app.invoke(input_dict, config)
            ai_response = output["messages"][-1]
            print("AI:", ai_response.content)
            print("\n")
        except KeyboardInterrupt:
            print("\nExiting chatbot. Your conversation history is saved.")
            mongodb_client.close()
            break
        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    run_chatbot()
