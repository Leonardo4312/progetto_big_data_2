import pandas as pd
import json
import random
import os
from sqlalchemy import create_engine, text
from config import DATABASE_URI, CSV_DATA_PATH, JSON_DATA_PATH, XLSX_DATA_PATH

def setup_database():
    print(f"Connecting to database at {DATABASE_URI}...")
    engine = create_engine(DATABASE_URI)

    # 1. Ingest Electric Vehicle Population Data
    if os.path.exists(CSV_DATA_PATH):
        print(f"Reading CSV data from {CSV_DATA_PATH}...")
        df = pd.read_csv(CSV_DATA_PATH)
        df.columns = [col.replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_").lower() for col in df.columns]

        print("Ingesting data into PostgreSQL table 'ev_population'...")
        df.to_sql("ev_population", engine, if_exists="replace", index=False)
        print(f"Successfully ingested {len(df)} records into 'ev_population'.")
        
        print("Creating pre-aggregated views for faster and safer LLM queries...")
        with engine.begin() as conn:
            conn.execute(text("CREATE OR REPLACE VIEW view_ev_count_by_city AS SELECT city, COUNT(*) as total_evs FROM ev_population GROUP BY city ORDER BY total_evs DESC;"))
            conn.execute(text("CREATE OR REPLACE VIEW view_ev_count_by_make AS SELECT make, COUNT(*) as total_evs FROM ev_population GROUP BY make ORDER BY total_evs DESC;"))
            conn.execute(text("CREATE OR REPLACE VIEW view_ev_count_by_county AS SELECT county, COUNT(*) as total_evs FROM ev_population GROUP BY county ORDER BY total_evs DESC;"))
            conn.execute(text("CREATE OR REPLACE VIEW view_ev_count_by_model AS SELECT make, model, COUNT(*) as total_evs FROM ev_population GROUP BY make, model ORDER BY total_evs DESC;"))
            conn.execute(text("CREATE OR REPLACE VIEW view_ev_count_by_city_and_make AS SELECT city, make, COUNT(*) as total_evs FROM ev_population GROUP BY city, make ORDER BY total_evs DESC;"))
        print("Pre-aggregated views created successfully.")
    else:
        print(f"Error: CSV file not found at {CSV_DATA_PATH}")

def extract_real_charging_stations():
    print(f"Extracting real charging station data from {XLSX_DATA_PATH}...")
    if not os.path.exists(XLSX_DATA_PATH):
        print(f"Error: Excel file not found at {XLSX_DATA_PATH}")
        return
        
    # Leggi l'Excel
    df = pd.read_excel(XLSX_DATA_PATH)
    
    # Filtra solo le stazioni dello Stato di Washington
    df = df[df['State'] == 'WA'].copy()
    
    # Rinomina e formatta le colonne in snake_case minuscolo
    df.columns = [col.replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_").lower() for col in df.columns]
    
    # Riempi i NaN con stringhe vuote o zeri per evitare errori in JSON/PySpark
    df = df.fillna("")
    
    # Esporta in formato JSON (lista di dizionari)
    stations = df.to_dict(orient="records") # type: ignore
    
    with open(JSON_DATA_PATH, "w") as f:
        json.dump(stations, f, indent=4)
        
    print(f"Successfully extracted and generated {len(stations)} real charging station records for WA at {JSON_DATA_PATH}")

if __name__ == "__main__":
    try:
        setup_database()
        extract_real_charging_stations()
        print("Setup completed successfully.")
    except Exception as e:
        print(f"An error occurred during setup: {e}")
