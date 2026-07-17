import os
from dotenv import load_dotenv


load_dotenv()


if "JAVA_HOME" not in os.environ and os.path.exists("/opt/homebrew/opt/openjdk@17"):
    os.environ["JAVA_HOME"] = "/opt/homebrew/opt/openjdk@17"


DB_USER = os.getenv("DB_USER", "ev_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "ev_password")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5434")
DB_NAME = os.getenv("DB_NAME", "ev_nexus_db")

DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5-coder:7b-instruct")




DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CSV_DATA_PATH = os.path.join(DATA_DIR, "Electric_Vehicle_Population_Data.csv")
XLSX_DATA_PATH = os.path.join(DATA_DIR, "EV_Charging_Stations_Feb82024.xlsx")
JSON_DATA_PATH = os.path.join(DATA_DIR, "charging_stations.json")
