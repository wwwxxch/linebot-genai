import os
from dotenv import load_dotenv
import logging
from enum import Enum
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.prompts import ChatPromptTemplate

load_dotenv()


# LLM configuration
class LLMProvider(Enum):
    OPENAI = "openai"
    GEMINI = "gemini"


def llm_provider_factory():
    try:
        llm_provider = os.getenv("LLM_PROVIDER", LLMProvider.GEMINI.value)

        if llm_provider == LLMProvider.OPENAI.value:
            return ChatOpenAI(model="gpt-4o-mini")
        elif llm_provider == LLMProvider.GEMINI.value:
            return ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    except Exception as e:
        logging.error(f"Error creating LLM provider: {e}")
        raise e


def create_cat_health_chain(llm):
    cat_data = {
        "name": "花花",
        "birth_year": 2007,
        "sex": "male",
        "species": "cat",
        "breed": "feline domestic shorthair",
        "medical_history": [
            "Feline Hypertrophic Cardiomyopathy Phase IIb, examined on 2024 June",
            "Hyperthyroidism, but the unilateral total thyroid gland has been removed at end of 2023",
        ],
    }
    current_dt = datetime.now()
    current_y = current_dt.year
    system_prompt = f"""
    You are an AI assistant specialized in cat health care for {cat_data["name"]}

    Cat-Specific Information:
        - Name: {cat_data['name']}
        - Birth Year: {cat_data['birth_year']}
        - Basic Information: sex is {cat_data['sex']}, breed is {cat_data['breed']}
        - Medical History: {', '.join(cat_data['medical_history'])}

    Guidelines:
        - Only answer questions related to cats
        - For questions about {cat_data["name"]}, use his specific information to answer
        - Answer the questions in 繁體中文
        - If a question is not cat-related, respond: "這與貓咪照護無關，我無法回答"
    Current year is {current_y}
    """

    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", "{input}")])

    chain = prompt | llm

    return chain


def get_ai_response(user_input):
    try:
        llm = llm_provider_factory()
        cat_health_chain = create_cat_health_chain(llm)
        response = cat_health_chain.invoke({"input": user_input})

    except Exception as e:
        logging.error(f"Error processing query: {e}")
        return "Sorry, I am unable to process your query at the moment."

    return response.content
