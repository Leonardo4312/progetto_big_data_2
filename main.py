# pyrefly: ignore [missing-import]
import sys
from crewai import Task, Crew, Process
from agents import EVNexusAgents # type: ignore

# Ordine sequenziale dei task/agenti: deve rispecchiare l'ordine reale in cui
# CrewAI esegue i task (Process.sequential). Usato per attribuire ogni step
# del Crew-level step_callback all'agente correntemente attivo.
AGENT_SEQUENCE = ["architect", "sql", "analyst", "guardian"]

# Range di progress (%) assegnato a ciascuna fase, allineato 1:1 con i "range"
# in AGENT_CONFIG nel frontend (App.jsx), cosi' che il calcolo di quale box e'
# "running" resti coerente anche quando il messaggio testuale non fa match.
PHASE_RANGES = {
    0: (5, 25),    # architect
    1: (26, 50),   # sql
    2: (51, 75),   # analyst
    3: (76, 97),   # guardian
}


def _format_step(step):
    """
    Estrae un testo leggibile e compatto da un oggetto step di CrewAI
    (tipicamente un AgentAction o un AgentFinish).

    """
    tool = getattr(step, "tool", None)
    tool_input = getattr(step, "tool_input", None)
    if tool:
        return f"→ using tool '{tool}' with input {tool_input}"[:280]

    for attr in ("text", "log", "output"):
        val = getattr(step, attr, None)
        if val:
            return str(val).strip().replace("\n", " ")[:280]

    return str(step).strip().replace("\n", " ")[:280]


def _output_text(output):
    """
    Estrae il testo dall'output finale di un Task completato (TaskOutput),
    usato per garantire SEMPRE almeno una riga di log per ogni agente anche
    quando quell'agente non ha usato tool e quindi non ha generato step
    intermedi intercettabili da step_callback (es. Data Analyst quando i dati
    sulle colonnine non sono richiesti, o il Veracity Guardian che non ha tool).
    """
    for attr in ("raw", "output", "result"):
        val = getattr(output, attr, None)
        if val:
            return str(val).strip().replace("\n", " ")[:220]
    return str(output).strip().replace("\n", " ")[:220]


def run_ev_nexus(user_query: str, status_cb=None, step_cb=None):
    if status_cb:
        status_cb(5, "The Architect is designing the data extraction plan...")
    if step_cb:
        step_cb("architect", "▶ analyzing the user query and planning the retrieval strategy...")
    print(f"Initializing EV NEXUS for query: '{user_query}'\n")

    agents = EVNexusAgents()

    # Puntatore mutabile all'indice dell'agente correntemente in esecuzione.
    # Process.sequential garantisce un solo agente attivo alla volta, quindi
    # ogni step ricevuto da step_callback può essere attribuito con sicurezza
    # all'agente puntato da current["index"].
    current = {"index": 0}
    # Conta gli step reali ricevuti per fase, per far avanzare la progress bar
    # in modo proporzionale al lavoro effettivo invece che a scatti fissi.
    steps_seen = {0: 0, 1: 0, 2: 0, 3: 0}

    def on_step(step):
        idx = current["index"]
        text = _format_step(step)
        if step_cb:
            step_cb(AGENT_SEQUENCE[idx], text)
        if status_cb:
            steps_seen[idx] += 1
            low, high = PHASE_RANGES[idx]
            span = high - low
            computed = low + min(steps_seen[idx] * 4, span)
            status_cb(computed, text[:90])

    def architect_done(output):
        if step_cb: step_cb("architect", f"✓ done: {_output_text(output)}")
        if status_cb: status_cb(26, "The SQL Engineer is querying the PostgreSQL database...")
        current["index"] = 1
        if step_cb: step_cb("sql", "▶ received the Architect's plan, starting SQL extraction...")

    def sql_done(output):
        if step_cb: step_cb("sql", f"✓ done: {_output_text(output)}")
        if status_cb: status_cb(51, "The Data Analyst is performing distributed computations via PySpark...")
        current["index"] = 2
        if step_cb: step_cb("analyst", "▶ received SQL Engineer output, checking charging-station requirement...")

    def analyst_done(output):
        if step_cb: step_cb("analyst", f"✓ done: {_output_text(output)}")
        if status_cb: status_cb(76, "The Guardian is drafting the final strategic analysis...")
        current["index"] = 3
        if step_cb: step_cb("guardian", "▶ compiling the final validated report...")

    def guardian_done(output):
        if step_cb: step_cb("guardian", f"✓ done: {_output_text(output)}")
    
    
    architect = agents.architect_agent()
    sql_engineer = agents.sql_engineer_agent()
    data_analyst = agents.data_analyst_agent()
    guardian = agents.veracity_guardian_agent()
    
   
    architect_task = Task(
        description=f"Analyze this request: '{user_query}'. Identify the necessary data from PostgreSQL "
                    f"and/or from the charging stations JSON. Provide a step-by-step plan on how the SQL Engineer "
                    f"and Data Analyst should extract and process this information.",
        expected_output="A step-by-step data retrieval and analysis plan.",
        agent=architect,
        callback=architect_done
    )
    
    sql_task = Task(
        description="Based on the Architect's plan, write and execute SQL queries to extract data from the "
                    "'ev_population' table. Ensure queries are correct and optimized. Pass the extracted data "
                    "to the Data Analyst. DO NOT attempt to extract charging stations data.",
        expected_output="Structured data extracted from PostgreSQL or a dataset summary.",
        agent=sql_engineer,
        callback=sql_done
    )
    
    analysis_task = Task(
        description="Follow the Architect's plan. If the Architect says 'Not applicable' or that charging stations are not needed, simply reply 'No charging data required' and DO NOT use any tools. "
                    "Otherwise, use the 'get_charging_stations_stats' tool to extract charging station data.",
        expected_output="Insights about charging stations, or 'No charging data required'.",
        agent=data_analyst,
        callback=analyst_done
    )
    
    guardian_task = Task(
        description=f"You are the final editor. You must answer the query: '{user_query}'.\n"
                    f"YOUR OUTPUT MUST STRICTLY START WITH A JSON BLOCK and then proceed with a SHORT Markdown text.\n\n"
                    f"MANDATORY STRUCTURE OF YOUR OUTPUT:\n"
                    f"```json\n"
                    f"{{\n"
                    f"  \"chart_type\": \"bar\",\n"
                    f"  \"chart_data\": [\n    {{\"name\": \"Name1\", \"value\": 100}},\n    {{\"name\": \"Name2\", \"value\": 200}}\n  ],\n"
                    f"  \"five_v_evaluation\": {{\n"
                    f"    \"Volume\": 3, \"Velocity\": 4, \"Variety\": 5, \"Veracity\": 4, \"Value\": 5\n"
                    f"  }}\n"
                    f"}}\n"
                    f"```\n\n"
                    f"AFTER the JSON block, write the Markdown report with EXACTLY these 3 sections:\n"
                    f"### Data Table\n"
                    f"(A simple Markdown table with the EXACT numbers found by the SQL Engineer and Data Analyst)\n\n"
                    f"### Agents Work\n"
                    f"(One short sentence per agent describing what they extracted)\n\n"
                    f"### Conclusions\n"
                    f"(A brief, factual answer to the user's query using ONLY the real numbers)\n\n"
                    f"CRITICAL RULES:\n"
                    f"1. NO HALLUCINATIONS: You MUST COPY EXACTLY the numbers extracted by the SQL Engineer and Data Analyst. If the SQL Engineer found 52078, you write 52078. If the Data Analyst found 1190, you write 1190. Do NOT invent numbers like 4500 or 1733.\n"
                    f"2. PRECISION OVER DETAIL: Keep the text short and factual. Do not write a long essay.\n"
                    f"3. JSON VALIDITY: The 'value' inside chart_data must be a number or null, no text.\n"
                    f"4. NO PLACEHOLDERS: If the SQL Engineer or Data Analyst failed to get the data, DO NOT copy the placeholder 'Name1'/'100'. Write 'No data' instead. If the query does not require charging stations, do not include them.\n",
        expected_output="MANDATORY: The text must start with the ```json block containing the EXACT data, followed by a short Markdown report.",
        agent=guardian,
        callback=guardian_done
    )
    
    # Formazione Crew
    ev_crew = Crew(
        agents=[architect, sql_engineer, data_analyst, guardian],
        tasks=[architect_task, sql_task, analysis_task, guardian_task],
        process=Process.sequential,
        verbose=True,
        cache=False,
        step_callback=on_step if step_cb else None
    )
    
    # Esecuzione Workflow
    result = ev_crew.kickoff()
    
    print("\n" + "="*50)
    print("EV NEXUS FINAL REPORT")
    print("="*50)
    print(result)
    return str(result)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "What is the ratio between registered Tesla cars and the availability of fast charging stations?"
        
    run_ev_nexus(query)