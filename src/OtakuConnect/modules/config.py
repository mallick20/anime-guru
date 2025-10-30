from db_utils import get_connection
from dotenv import load_dotenv
import os
from openai import AzureOpenAI


# Import environment variables
load_dotenv()

# DB connection parameters
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

db_engine = get_connection(username, password, host, port, db_name)


# OpenAI Client
azure_openai_api_key = os.getenv("OPENAI_API_KEY")
azure_openai_endpoint = os.getenv("OPENAI_ENDPOINT")
azure_openai_api_version = os.getenv("OPENAI_API_VERSION")