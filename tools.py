import json
import traceback
from crewai.tools import tool  # type: ignore
from sqlalchemy import create_engine, inspect, text  # type: ignore
import pandas as pd  # type: ignore
from config import DATABASE_URI, JSON_DATA_PATH  # type: ignore
from pyspark.sql import SparkSession  # type: ignore

# Initialize Engine (leggero: non apre connessioni finché non viene usato)
engine = create_engine(DATABASE_URI)

# ---------------------------------------------------------------------------
# SparkSession lazy: viene creata solo alla prima chiamata a run_spark_analysis,
# non all'import del modulo. Così se Spark fallisce (es. bug di bind su Windows)
# il resto dell'API (chat, dashboard) continua a funzionare comunque.
# ---------------------------------------------------------------------------
_spark = None


def get_spark():
    global _spark
    if _spark is None:
        _spark = (
    SparkSession.builder
    .appName("EV_NEXUS_Spark")
    .master("local[*]")  # Usa tutti i core disponibili
    .config("spark.driver.memory", "4g")  # Evita OutOfMemory su repliche 10x/20x
    .config("spark.sql.shuffle.partitions", "4")  # Cruciale per dataset locali
    .config("spark.driver.bindAddress", "127.0.0.1")
    .config("spark.driver.host", "127.0.0.1")
    .getOrCreate()
)
        _spark.sparkContext.setLogLevel("ERROR")
    return _spark


@tool
def get_database_schema(dummy: str = "") -> str:
    """
    Returns the schema of the PostgreSQL database, including table names and their columns.
    Useful for understanding what data is available to query.
    """
    try:
        inspector = inspect(engine)
        schema_info = []
        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            col_info = []
            for col in columns:
                col_str = f"{col['name']} ({col['type']})"
                if col['name'] == 'clean_alternative_fuel_vehicle_cafv_eligibility':
                    col_str += " [Valid values: 'Clean Alternative Fuel Vehicle Eligible', 'Not eligible due to low battery range', 'Eligibility unknown...']"
                col_info.append(col_str)
                
            schema_info.append(f"Table: {table_name}\nColumns: {', '.join(col_info)}")
            
        for view_name in inspector.get_view_names():
            columns = inspector.get_columns(view_name)
            col_info = [f"{col['name']} ({col['type']})" for col in columns]
            schema_info.append(f"View: {view_name}\nColumns: {', '.join(col_info)}")
            
        return "\n\n".join(schema_info)
    except Exception as e:
        return f"Error retrieving schema: {str(e)}"


@tool
def execute_sql_query(query: str) -> str:
    """
    Executes a SELECT query on the PostgreSQL database and returns the results.
    Input must be a valid SQL query.
    """
    try:

        import re
        query = query.replace('"', "'")
      
        query = re.sub(r"=\s*'([^']+)'", r"ILIKE '\1'", query)
        
        
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
        if df.empty:
            return "Query executed successfully, but returned 0 rows."
       
        if len(df) > 100:
            return f"Query returned {len(df)} rows. Here are the first 100:\n{df.head(100).to_string(index=False)}"
        return df.to_string(index=False)
    except Exception as e:
        schema = get_database_schema.func()
        error_msg = str(e)
        hint = "\n\nHINT: Please check your query against the actual schema. If you used double quotes for a string (e.g., \"NISSAN\"), you MUST change them to single quotes ('NISSAN') in PostgreSQL!"
        return f"SQL Error: {error_msg}{hint}\n\nSchema:\n{schema}"


@tool
def read_json_data(dummy: str = "") -> str:
    """
    Reads the mock API data for charging stations from the JSON file.
    Returns a sample of the data and its structure.
    """
    try:
        with open(JSON_DATA_PATH, "r") as f:
            data = json.load(f)

        sample = data[:5] if len(data) > 5 else data
        return f"Total charging stations: {len(data)}. Sample data:\n{json.dumps(sample, indent=2)}"
    except Exception as e:
        return f"Error reading JSON: {str(e)}"


@tool
def get_charging_stations_stats(group_by_column: str) -> str:
    """
    Returns aggregated statistics about charging stations from the JSON file.
    Valid values for group_by_column are: 'city', 'state', 'zip', 'ev_network', 'facility_type'.
    """
    try:
        spark = get_spark()
        df = spark.read.option('multiline','true').json(JSON_DATA_PATH)
        import pyspark.sql.functions as F
        

        total_fast = df.select(F.sum(F.col("ev_dc_fast_count").cast("int"))).collect()[0][0] or 0
        total_stations = df.count()
        
        valid_columns = ['city', 'state', 'zip', 'ev_network', 'facility_type']
        if group_by_column not in valid_columns:
            return f"Warning: '{group_by_column}' is not a valid column. Valid columns are {valid_columns}.\nOverall Stats - Total Stations: {total_stations}, Total DC Fast Chargers: {total_fast}"
            
        df_grouped = df.groupBy(group_by_column).count().orderBy(F.desc('count')).limit(10)
        return f"Total DC Fast Chargers across all data: {total_fast}\nTop 10 by {group_by_column}:\n{str(df_grouped.collect())}"
    except Exception as e:
        return f"Error reading charging stations: {str(e)}\n{traceback.format_exc()}"