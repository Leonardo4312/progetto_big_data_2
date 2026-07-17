import pandas as pd # type: ignore
import numpy as np # type: ignore
from sqlalchemy import create_engine # type: ignore
from config import DATABASE_URI # type: ignore

def clean_database():
    print("Iniziando il processo di Data Cleaning sul database PostgreSQL...")
    engine = create_engine(DATABASE_URI)
    
    # 1. Carica il dataset
    print("Estrazione dati in corso...")
    df = pd.read_sql("SELECT * FROM ev_population", engine)
    initial_rows = len(df)
    
    # 2. Gestione Valori Nulli
    print("Sostituzione dei valori nulli con 'Sconosciuto'...")
    text_columns = ['model', 'legislative_district', 'vehicle_location', 'electric_utility']
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].fillna('Sconosciuto')
            
    # 3. Imputazione Zeri in electric_range
    print("Applicazione tecnica di Imputazione sulle autonomie pari a 0...")
    # Creiamo una copia dove gli zeri sono NaN per ignorarli nel calcolo della media
    temp_df = df.copy()
    temp_df['electric_range'] = temp_df['electric_range'].replace(0, np.nan)
    
    # Calcoliamo la media per ogni Make (Marca) e Model (Modello)
    mean_by_make_model = temp_df.groupby(['make', 'model'])['electric_range'].transform('mean')
    # Calcoliamo il fallback (media solo per Marca)
    mean_by_make = temp_df.groupby('make')['electric_range'].transform('mean')
    
    # Riempiamo gli zeri originali (che ora sono NaN)
    # Prima proviamo con la media del modello esatto
    temp_df['electric_range'] = temp_df['electric_range'].fillna(mean_by_make_model)
    # Se il modello aveva solo zeri e quindi è ancora NaN, proviamo con la media della marca
    temp_df['electric_range'] = temp_df['electric_range'].fillna(mean_by_make)
    # Se per assurdo la marca ha solo zeri (es. non ci sono dati reali), imputiamo un valore standard di 200
    temp_df['electric_range'] = temp_df['electric_range'].fillna(200)
    
    # Arrotondiamo all'intero più vicino
    df['electric_range'] = temp_df['electric_range'].round().astype(int)
    
    # 4. Ricarica su PostgreSQL
    print("Salvataggio del database pulito su PostgreSQL...")
    df.to_sql("ev_population", engine, if_exists="replace", index=False)
    
    print("="*50)
    print(f"PULIZIA COMPLETATA! {initial_rows} record elaborati.")
    print("Ora l'IA e Ollama lavoreranno su dati perfetti.")
    print("="*50)

if __name__ == "__main__":
    clean_database()
