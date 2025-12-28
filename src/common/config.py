from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
CLIENT_ID = os.environ.get("CLIENT_ID")
REDIRECT_URL = os.environ.get("REDIRECT_URL")

DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
REDIS_URL = os.environ.get("REDIS_URL")

RMQ_USER = os.environ.get("RMQ_USER")
RMQ_PASSWORD = os.environ.get("RMQ_PASSWORD")
RMQ_HOST = os.environ.get("RMQ_HOST")
RMQ_PORT = os.environ.get("RMQ_PORT")
RMQ_VHOST = os.environ.get("RMQ_VHOST")
RMQ_QUEUE = os.environ.get("RMQ_QUEUE")
