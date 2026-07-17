# EV-NEXUS: Sistema Multi-Agente per l'Analisi dei Dati sui Veicoli Elettrici

## 📖 Descrizione del Progetto

**EV-NEXUS** è una piattaforma analitica avanzata basata su un'architettura Multi-Agente (tramite CrewAI) progettata per estrarre insight e rispondere a domande complesse riguardanti il mercato dei veicoli elettrici (EV). 

Il sistema combina modelli di intelligenza artificiale (LLM) con strumenti di elaborazione dati tradizionali (PostgreSQL, PySpark) per analizzare simultaneamente dati strutturati (es. immatricolazioni) e semi-strutturati (es. stazioni di ricarica in formato JSON). La piattaforma include anche una dashboard frontend sviluppata in React per fornire un'esperienza utente interattiva e un monitoraggio in tempo reale del ragionamento degli agenti.

## 🚀 Riproducibilità del Codice (Setup e Avvio)


### 1. Pre-requisiti
- **Python**: 3.10 o superiore.
- **Node.js & npm**: Per avviare il frontend React.
- **PostgreSQL**: Installato e in esecuzione localmente (oppure tramite Docker usando il `docker-compose.yml` fornito).
- **Ollama**: (Opzionale, ma raccomandato) Per eseguire LLM in locale come `qwen2.5-coder:7b-instruct`.
- **Docker**: Per eseguire il container di PostgreSQL.

### 2. Configurazione dell'Ambiente e Dipendenze
Apri il terminale nella root del progetto e crea un ambiente virtuale:

```bash
# Crea l'ambiente virtuale
python -m venv venv_ev_nexus

# Attiva l'ambiente virtuale
# Su Windows:
.\venv_ev_nexus\Scripts\activate
# Su Mac/Linux:
source venv_ev_nexus/bin/activate

# Installa le dipendenze Python
pip install -r requirements.txt

# Crea l'ambiente virtuale
python -m venv venv_ev_nexus

# Attiva l'ambiente virtuale
# Su Windows:
.\venv_ev_nexus\Scripts\activate
# Su Mac/Linux:
source venv_ev_nexus/bin/activate

# Installa le dipendenze Python
pip install -r requirements.txt

# Avvia il container di PostgreSQL in background tramite Docker Compose
docker-compose up -d
```
### 3. Preparazione dei Dati e del Database
Assicurati che PostgreSQL sia attivo. Di default il sistema cerca un database chiamato `ev_database`. Puoi configurare le credenziali nel file `.env` (se presente) o nel file `config.py`.

Posiziona i dataset necessari (il CSV della popolazione EV e il JSON/Excel delle stazioni) nella cartella `data/`.

Esegui gli script di setup in ordine:
```bash
# Popola il database con i dati iniziali dal CSV
python database_setup.py

# Pulisce e normalizza i dati (gestione null, valori zero, ecc.)
python clean_db.py

# (Opzionale) Crea eventuali viste aggiuntive per semplificare le query
python create_view.py
```

### 4. Avvio dell'Applicazione
Il progetto è dotato di script che automatizzano l'avvio simultaneo del backend FastAPI e del frontend React.

**Su Windows:**
```cmd
.\run_windows.bat
```

**Su Mac/Linux:**
```bash
./run_mac.sh
```

---

## 📂 Struttura del Progetto

Di seguito è riportata la spiegazione di tutti i file principali che compongono l'infrastruttura EV-NEXUS:

### Core Multi-Agente
- **`main.py`**: È il cuore dell'architettura Multi-Agente. Qui vengono definiti i Task (obiettivi), configurata la "Crew" e avviato il flusso di esecuzione sequenziale.
- **`agents.py`**: Contiene la definizione e i prompt di sistema dei vari agenti AI operanti nel progetto (*Architect*, *SQL Engineer*, *Data Analyst*, *Guardian*).
- **`tools.py`**: Definisce gli strumenti operativi che gli agenti possono utilizzare autonomamente (es. funzioni per eseguire query SQL su Postgres, o per analizzare JSON tramite PySpark).

### Backend e API
- **`api.py`**: Implementa il server backend utilizzando FastAPI. Espone gli endpoint necessari al frontend per avviare le analisi, recuperare i risultati in streaming e consultare la cache.
- **`config.py`**: Centralizza tutte le variabili di configurazione dell'ambiente, come la stringa di connessione al database, le API Key e il modello LLM in uso.

### Gestione Dati e Database
- **`database_setup.py`**: Script per l'ingestion iniziale; legge il dataset CSV e crea le tabelle base in PostgreSQL.
- **`clean_db.py`**: Si occupa del preprocessing e della pulizia del dato (imputazione di valori mancanti, rimozione di outlier), garantendo l'integrità per l'LLM.
- **`create_view.py`**: Utility per creare tabelle virtuali o viste che facilitano il compito di interrogazione da parte degli agenti.
- **`data_analysis.py`**: Uno script di esplorazione statistica utile in fase di sviluppo per comprendere anomalie nei dati e decidere come strutturare le logiche di pulizia.

### Valutazione e Benchmark
- **`evaluation.py`**: Contiene un set di query "Golden" (con relative risposte attese) utilizzate per valutare le performance e l'efficacia del sistema.
- **`benchmark.py`**: Script che esegue i test in blocco, calcola l'accuratezza e le latenze di risposta del sistema Multi-Agente, generando grafici riepilogativi.

### Interfaccia Utente e Utility
- **`frontend/`**: Directory contenente l'intera codebase dell'applicazione web React (Vite) per l'interfaccia utente.
- **`run_mac.sh` / `run_windows.bat`**: Script shell/batch comodi per l'avvio congiunto dei servizi frontend e backend.
- **`translate_app.py`**: Utility script per automatizzare sostituzioni di stringhe di testo nel frontend, utile per internazionalizzazione rapida (es. da ITA a ENG).
- **`docker-compose.yml`**: Configurazione Docker pronta all'uso per far ruotare un'istanza PostgreSQL isolata se non se ne possiede una installata globalmente.

### Dataset e Risorse
Il sistema EV-NEXUS necessita di due dataset principali per funzionare correttamente:

Dataset dei veicoli elettrici (formato CSV): contiene le informazioni demografiche e tecniche dei veicoli immatricolati (es. marca, modello, anno, contea, autonomia, ecc.).

Dataset delle infrastrutture di ricarica (formato JSON o Excel): elenco delle stazioni di ricarica con dettagli su posizione, tipo di connettore, potenza erogata e operatore.

Entrambi i dataset sono disponibili per il download nella seguente cartella condivisa su Google Drive:

[Cartella Dataset EV-Nexus (Google Drive)](https://drive.google.com/drive/folders/1XJFGHNOyFYMDM-pEZcivBbpG0aSPisU1?usp=sharing)

Dopo aver scaricato i file, copiali nella cartella data/ (se non esiste, creala nella root del progetto) prima di eseguire gli script di setup del database, come descritto nella Sezione 3.

Nota: Assicurati che i nomi dei file corrispondano a quelli attesi dagli script (database_setup.py e tools.py). Se i nomi differiscono, aggiorna i percorsi nei file di configurazione o rinomina i file scaricati di conseguenza.