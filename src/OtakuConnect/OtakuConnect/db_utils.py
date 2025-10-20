import pandas as pd
from sqlalchemy import create_engine

def get_connection(user, password, host, port, db):
    connection_uri = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    return create_engine(connection_uri)

def load_table_as_df(engine, table_name):
    return pd.read_sql(f"SELECT * FROM {table_name};", engine)

