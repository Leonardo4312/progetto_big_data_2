import time
import os
import random
import pandas as pd
from sqlalchemy import create_engine, text
import matplotlib.pyplot as plt

# Per eseguire matplotlib senza interfaccia grafica
import matplotlib
matplotlib.use('Agg')

# Import specifici del progetto
from config import DATABASE_URI
from main import run_ev_nexus
from evaluation import GOLDEN_QUERIES

engine = create_engine(DATABASE_URI)

def run_benchmark():
    print("Starting EV-NEXUS Agentic Benchmark...\n")
    results = []
    
    # Prendi 3 query casuali da evaluation.py
    num_queries = min(3, len(GOLDEN_QUERIES))
    test_queries = random.sample(GOLDEN_QUERIES, num_queries)
    
    for idx, case in enumerate(test_queries):
        print(f"--- Query {idx+1}/{len(test_queries)} ---")
        print(f"Q: {case['question']}")
        
        # 1. Calcolo del Ground Truth (Valore Atteso) via SQL diretto
        expected_df = pd.read_sql(text(case["expected_sql"]), engine)
        expected_value = expected_df.iloc[0, 0]
        
        if pd.isna(expected_value):
            expected_str = "None"
        elif isinstance(expected_value, (int, float)):
           
            if expected_value == int(expected_value):
                expected_str = str(int(expected_value))
            else:
                expected_str = str(expected_value)
        else:
            expected_str = str(expected_value)
            
        print(f"Expected GT Value: {expected_str}")
        
        # 2. Esecuzione Multi-Agente e misurazione della Latenza
        start_time = time.time()
        try:
            import sys, io
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            
            report = run_ev_nexus(case["question"])
            
            
            sys.stdout = old_stdout
        except Exception as e:
        
            import sys
            if hasattr(sys, 'old_stdout'):
                sys.stdout = sys.old_stdout
            report = f"Error: {e}"
            
        latency = time.time() - start_time
        
        # 3. Verifica Accuratezza (Ricerca testuale grezza nel report generato dagli agenti, case-insensitive)
        is_correct = expected_str.lower() in report.lower()
        
        results.append({
            "question": case["question"],
            "expected": expected_str,
            "latency": latency,
            "correct": is_correct
        })
        
        print(f"Latency: {latency:.2f}s | Correct: {is_correct}\n")
    
    # Generazione dei report visivi (grafici)
    generate_charts(results)
    
    print("\nBenchmark completato. I grafici sono stati salvati nella directory corrente:")
    print("- accuracy_pie_chart.png")
    print("- latency_bar_chart.png")


def generate_charts(results):
    df = pd.DataFrame(results)
    
    # 1. Grafico a Torta dell'Accuratezza
    success_count = df['correct'].sum()
    fail_count = len(df) - success_count
    
    plt.figure(figsize=(6, 6))
    # Se fail_count è 0, mostra solo un colore
    if fail_count == 0:
        plt.pie([success_count], labels=['Success'], autopct='%1.1f%%', colors=['#4CAF50'], startangle=90)
    elif success_count == 0:
        plt.pie([fail_count], labels=['Failure/Hallucination'], autopct='%1.1f%%', colors=['#F44336'], startangle=90)
    else:
        plt.pie([success_count, fail_count], labels=['Success', 'Failure/Hallucination'], 
                autopct='%1.1f%%', colors=['#4CAF50', '#F44336'], startangle=90)
        
    plt.title('Agentic Retrieval Accuracy Rate')
    plt.savefig('accuracy_pie_chart.png', dpi=150)
    plt.close()
    
    # 2. Grafico a Barre della Latenza
    plt.figure(figsize=(8, 6))
    bars = plt.bar(df.index + 1, df['latency'], color='#2196F3', edgecolor='black')
    plt.xlabel('ID Query (Test Case)')
    plt.ylabel('Latenza Totale (Secondi)')
    plt.title('Latenza End-to-End per Query ($T_{tot}$)')
    plt.xticks(df.index + 1)
    
    # Aggiunge i valori sopra le barre
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + (yval * 0.02), f"{yval:.1f}s", ha='center', va='bottom')
        
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('latency_bar_chart.png', dpi=150)
    plt.close()


if __name__ == "__main__":
    run_benchmark()
