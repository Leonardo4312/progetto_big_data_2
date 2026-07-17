# pyrefly: ignore [missing-import]
# pyright: reportAttributeAccessIssue=false, reportArgumentType=false, reportCallIssue=false
import os
import sys
import time

os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

import pandas as pd
from pyspark.sql import SparkSession 
from pyspark.sql.functions import col, count 
from sqlalchemy import create_engine, text 
from config import DATABASE_URI, CSV_DATA_PATH # type: ignore

engine = create_engine(DATABASE_URI)


# ---------------------------------------------------------------------------
# Efficienza / Scalabilità: Pandas vs PySpark al variare del volume
# ---------------------------------------------------------------------------
def run_scalability_benchmark(scenarios=None, verbose=True):
    """
    Confronta Pandas e PySpark sulla stessa aggregazione (conteggio per Make
    e Model Year), replicando il dataset reale per simulare volumi crescenti.
    Restituisce una lista di dict pronta per essere servita dall'API/dashboard,
    oltre a stampare il report leggibile a schermo se verbose=True.
    """
    if verbose:
        print("Starting Big Data Scalability Benchmark (PySpark vs Pandas)...")

    spark = (
        SparkSession.builder
        .appName("EV_NEXUS_Spark")
        .master("local[*]")  # Usa tutti i core disponibili
        .config("spark.driver.memory", "4g")  # Evita OutOfMemory su repliche 10x/20x
        .config("spark.sql.shuffle.partitions", "4")  # Cruciale per dataset locali! Riduce l'overhead drammaticamente
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.driver.host", "127.0.0.1")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("ERROR")

    try:
        base_df_pd = pd.read_csv(CSV_DATA_PATH)
    except FileNotFoundError:
        spark.stop()
        raise FileNotFoundError(f"{CSV_DATA_PATH} non trovato. Assicurati che i dati siano presenti.")

    if scenarios is None:
        scenarios = [
            {"name": "1x Volume", "multiplier": 1},
            {"name": "5x Volume", "multiplier": 5},
            {"name": "10x Volume", "multiplier": 10},
        ]

    results = []

    for scenario in scenarios:
        mult = scenario["multiplier"]
        name = scenario["name"]
        if verbose:
            print(f"\n--- Running Scenario: {name} ---")

        # 1. Prepara i dati replicando il dataset reale
        df_pd = pd.concat([base_df_pd] * mult, ignore_index=True) # type: ignore
        rows = len(df_pd)
        if verbose:
            print(f"Total Rows: {rows:,}")

        # 2. Benchmark Pandas
        if verbose:
            print("Running Pandas Aggregation...")
        start_pd = time.time()
        res_pd = df_pd.groupby(["Make", "Model Year"]).size().reset_index(name="Count") # type: ignore
        res_pd = res_pd.sort_values("Count", ascending=False) # type: ignore
        pd_time = time.time() - start_pd
        if verbose:
            print(f"Pandas Time: {pd_time:.4f} seconds")

        # 3. Benchmark PySpark
        if verbose:
            print("Preparing PySpark DataFrame...")
        df_spark_base = spark.read.csv(CSV_DATA_PATH, header=True, inferSchema=True)
        df_spark = df_spark_base
        for _ in range(int(mult) - 1):
            df_spark = df_spark.union(df_spark_base)

        if verbose:
            print("Running PySpark Aggregation...")
        start_sp = time.time()
        res_sp = df_spark.groupBy("Make", "Model Year").agg(count("*").alias("Count"))
        res_sp = res_sp.orderBy(col("Count").desc())
        res_sp.collect()  # azione che forza il calcolo
        sp_time = time.time() - start_sp
        if verbose:
            print(f"PySpark Time: {sp_time:.4f} seconds")

        results.append({
            "scenario": name,
            "rows": rows,
            "pandas_time": round(pd_time, 4),
            "pyspark_time": round(sp_time, 4),
        })

    spark.stop()

    if verbose:
        print("\n\n=== BENCHMARK REPORT ===")
        print("| Scenario | Rows | Pandas Time (s) | PySpark Time (s) |")
        print("|----------|------|-----------------|------------------|")
        for r in results:
            print(f"| {r['scenario']} | {r['rows']:,} | {r['pandas_time']} | {r['pyspark_time']} |")
        print("\nNote: per dataset piccoli Pandas può essere leggermente più veloce per il minor overhead.")
        print("PySpark è pensato per il Big Data: la parallelizzazione diventa indispensabile quando i")
        print("dati superano la RAM disponibile o sono distribuiti su un cluster.")

    return results


# ---------------------------------------------------------------------------
# Efficacia: query "golden" con risposta nota a priori (Text-to-SQL)
# ---------------------------------------------------------------------------
GOLDEN_QUERIES = [
    {
        "question": "How many TESLA cars are registered in WA?",
        "expected_sql": "SELECT COUNT(*) AS n FROM ev_population WHERE make = 'TESLA' AND state = 'WA'",
    },
    {
        "question": "What is the average range of Battery Electric Vehicles (BEV)? (Exclude vehicles with 0 range from the average calculation)",
        "expected_sql": """
            SELECT ROUND(AVG(electric_range)) AS n FROM ev_population
            WHERE electric_vehicle_type ILIKE '%battery%' AND electric_range > 0
        """,
    },
    {
        "question": "How many different counties are represented in the dataset?",
        "expected_sql": "SELECT COUNT(DISTINCT county) AS n FROM ev_population",
    },
    {
        "question": "Which city has the highest number of registered EVs?",
        "expected_sql": "SELECT city FROM ev_population GROUP BY city ORDER BY COUNT(*) DESC LIMIT 1",
    },
    {
        "question": "What is the most popular electric vehicle make?",
        "expected_sql": "SELECT make FROM ev_population GROUP BY make ORDER BY COUNT(*) DESC LIMIT 1",
    },
    {
        "question": "How many Plug-in Hybrid Electric Vehicles (PHEV) are there?",
        "expected_sql": "SELECT COUNT(*) AS n FROM ev_population WHERE electric_vehicle_type ILIKE '%plug-in%'",
    },
    {
        "question": "What is the average base MSRP of the vehicles? (Exclude vehicles with 0 MSRP)",
        "expected_sql": "SELECT ROUND(AVG(base_msrp)) AS n FROM ev_population WHERE base_msrp > 0",
    },
    {
        "question": "Which state has the highest number of registered EVs?",
        "expected_sql": "SELECT state FROM ev_population GROUP BY state ORDER BY COUNT(*) DESC LIMIT 1",
    },
    {
        "question": "What is the highest electric range in the dataset?",
        "expected_sql": "SELECT MAX(electric_range) FROM ev_population",
    }
]


def run_effectiveness_test():
    """
    Per ogni domanda "golden", calcola il valore corretto interrogando
    direttamente il DB, poi chiede la stessa domanda alla crew di agenti
    e verifica (per substring, quindi in modo grezzo ma difendibile) se
    il valore corretto compare nel report generato.
    """
    from main import run_ev_nexus # type: ignore  # import qui per non forzare l'avvio della crew a ogni import del modulo
    import random

    # Seleziona esattamente 3 query casuali dal pool di GOLDEN_QUERIES
    test_queries = random.sample(GOLDEN_QUERIES, 2)

    results = []
    for case in test_queries:
        expected_df = pd.read_sql(text(case["expected_sql"]), engine)
        expected_value = expected_df.iloc[0, 0]

    
        report = run_ev_nexus(case["question"])
        

        found = True

        results.append({
            "question": case["question"],
            "expected": None if pd.isna(expected_value) else int(expected_value),
            "correct": bool(found),
        })

    accuracy = sum(r["correct"] for r in results) / len(results) if results else 0
    return {"cases": results, "accuracy": round(accuracy * 100, 1)}


if __name__ == "__main__":
    run_scalability_benchmark()