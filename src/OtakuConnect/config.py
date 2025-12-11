from dotenv import load_dotenv
import os


class Config:
    """Configuration class for OtakuConnect application."""
    
    # Load dotenv file
    load_dotenv()
    
    # DB Configuration
    DB_USERNAME = os.environ["DB_USERNAME"]
    DB_PASSWORD = os.environ["DB_PASSWORD"]
    DB_HOST = os.environ["DB_HOST"]
    DB_PORT = os.environ["DB_PORT"]
    DB_NAME = os.environ["DB_NAME"]
    
    # OpenAI Configuration
    OPENAI_ENDPOINT = os.environ["OPENAI_ENDPOINT"]
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
    OPENAI_API_VERSION = os.environ["OPENAI_API_VERSION"]