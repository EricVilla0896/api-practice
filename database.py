import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    connection=psycopg.connect(
        user=os.getenv("DB_USER"),
        host="localhost",
        port=5432,
        dbname=os.getenv("DB_NAME"),
        password=os.getenv("DB_PASSWORD")
    )
    return connection