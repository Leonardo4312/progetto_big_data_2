import pandas as pd # type: ignore
from sqlalchemy import create_engine # type: ignore
from config import DATABASE_URI # type: ignore

def analyze_database():
    engine = create_engine(DATABASE_URI)
    
    print("="*50)
    print("DATABASE HEALTH REPORT: ev_population")
    print("="*50)
    
    try:
        df = pd.read_sql("SELECT * FROM ev_population", engine)
        
        print(f"Totale Record: {len(df)}")
        print(f"Totale Colonne: {len(df.columns)}")
        print("-" * 30)
        
        
        null_counts = df.isnull().sum()
        null_cols = null_counts[null_counts > 0]
        if not null_cols.empty: # type: ignore
            print("VALORI NULLI TROVATI:")
            for col, count in null_cols.items(): # type: ignore
                print(f" - {col}: {count} valori nulli")
        else:
            print("Nessun valore nullo trovato nel database! 🎉")
            
        print("-" * 30)
        

        zero_range = len(df[df['electric_range'] == 0])
        print(f"ANOMALIE AUTONOMIA (Range = 0): {zero_range} veicoli")
        
        print("="*50)
        
    except Exception as e:
        print(f"Errore durante l'analisi: {e}")

if __name__ == "__main__":
    analyze_database()
