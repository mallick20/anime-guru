from db_utils import get_connection
from dotenv import load_dotenv
import os

# Import environment variables
load_dotenv()

# DB connection parameters
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

db_engine = get_connection(username, password, host, port, db_name)