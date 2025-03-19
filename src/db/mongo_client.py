import os
from dotenv import load_dotenv
from pymongo import MongoClient


class MongoDBClient:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            load_dotenv()
            mongodb_uri = os.getenv("MONGODB_URI")
            if not mongodb_uri:
                raise ValueError("Error: MONGODB_URI not found in environment variables. Please set it.")
            cls._instance = MongoClient(mongodb_uri)
        return cls._instance

    @classmethod
    def close(cls):
        if cls._instance:
            cls._instance.close()
            cls._instance = None
