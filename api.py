# pyrefly: ignore [missing-import]
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dashboard import get_dashboard_payload # type: ignore
from evaluation import run_scalability_benchmark, run_effectiveness_test # type: ignore
import uuid
import sqlite3
import datetime
from threading import Thread

from main import run_ev_nexus # type: ignore

app = FastAPI(title="EV Nexus API")




app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    report: str

tasks_status = {}

class AnalyzeStartResponse(BaseModel):
    task_id: str

@app.post("/api/analyze/start", response_model=AnalyzeStartResponse)
def start_analysis(request: QueryRequest):
    """
    Avvia l'analisi in background e restituisce il task_id per il polling.
    Utilizza SQLite per memorizzare nella cache le query già eseguite.
    """
    

    task_id = str(uuid.uuid4())
    tasks_status[task_id] = {
        "progress": 0,
        "message": "Initializing Big Data environment...",
        # Log live per agente: popolato dal Crew-level step_callback in main.py,
        # ad ogni pensiero/tool-call/osservazione, non solo a fine task.
        "agent_logs": {"architect": [], "sql": [], "analyst": [], "guardian": []},
        "report": None,
        "status": "running",
        "error": None
    }

    def update_status(progress, message):
        tasks_status[task_id]["progress"] = progress
        tasks_status[task_id]["message"] = message

    def update_step(agent_key, text):
        logs = tasks_status[task_id]["agent_logs"].setdefault(agent_key, [])
        # Evita righe duplicate consecutive (es. LLM che ripete lo stesso "Thought:")
        if not logs or logs[-1] != text:
            logs.append(text)
            # Tiene il buffer limitato per non far crescere indefinitamente la risposta JSON
            if len(logs) > 25:
                del logs[0]

    def run_task():
        try:
           
            final_report = run_ev_nexus(request.query, status_cb=update_status, step_cb=update_step)
            
          
            
            tasks_status[task_id]["progress"] = 100
            tasks_status[task_id]["status"] = "completed"
            tasks_status[task_id]["report"] = final_report
        except Exception as e:
            tasks_status[task_id]["status"] = "error"
            tasks_status[task_id]["error"] = str(e)
            
    Thread(target=run_task).start()
    return AnalyzeStartResponse(task_id=task_id)

@app.get("/api/analyze/status/{task_id}")
def get_status(task_id: str):
    """
    Restituisce lo stato attuale del task.
    """
    if task_id not in tasks_status:
        return {"status": "not_found"}
    return tasks_status[task_id]

# Endpoint legacy tenuto per retrocompatibilità o rimovibile
@app.post("/api/analyze", response_model=QueryResponse)
def analyze_query(request: QueryRequest):
    try:
        final_report = run_ev_nexus(request.query)
        return QueryResponse(report=final_report)
    except Exception as e:
        return QueryResponse(report=f"An error occurred during the analysis: {str(e)}")

@app.get("/api/dashboard")
def dashboard(include_charging: bool = False, include_income: bool = False):
    """
    Restituisce KPI e serie aggregate per la Dashboard:
    top marche, distribuzione autonomia, EV per contea,
    quota per network di ricarica, reddito vs adozione EV per ZIP.
    """
    try:
        return get_dashboard_payload(include_charging=include_charging, include_income=include_income)
    except Exception as e:
        return {"error": str(e)}

 
 
# --- Endpoint di valutazione sperimentale (chiamati on-demand dal frontend) ---
@app.get("/api/evaluation/scalability")
def evaluation_scalability():
    """Benchmark Pandas vs PySpark al variare del volume (replica dataset 1x/5x/10x)."""
    try:
        return {"results": run_scalability_benchmark(verbose=False)}
    except Exception as e:
        return {"error": str(e)}
 
 
@app.get("/api/evaluation/effectiveness")
def evaluation_effectiveness():
    """Accuratezza del Text-to-SQL su domande con risposta nota a priori."""
    try:
        return run_effectiveness_test()
    except Exception as e:
        return {"error": str(e)}
