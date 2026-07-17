# pyrefly: ignore [missing-import]
from crewai import Agent, LLM
from tools import get_database_schema, execute_sql_query, read_json_data, get_charging_stations_stats # type: ignore
from config import OPENAI_API_KEY, LLM_MODEL # type: ignore


llm = LLM(
    model=f"openai/{LLM_MODEL}",
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)
print(f"[INFO] Using Local Ollama LLM: {LLM_MODEL}")

class EVNexusAgents:
    
    def architect_agent(self):
        return Agent(
            role="The Architect",
            goal="Analyze user requests and formulate a precise strategy for data retrieval and analysis.",
            backstory=(
                "You are a Senior Data Architect. Plan how to answer the user's question.\n"
                "1. POSTGRESQL DATABASE: Table 'ev_population' (columns: vin_1_10, county, city, state, postal_code, model_year, make, model, electric_vehicle_type, clean_alternative_fuel_vehicle_cafv_eligibility, electric_range, base_msrp). "
                "Views: view_ev_count_by_city, view_ev_count_by_make, view_ev_count_by_county, view_ev_count_by_model, view_ev_count_by_city_and_make. "
                "Instruct the SQL Engineer to write a SQL query. If the required fields are not in a view, query 'ev_population' directly. Car makes are ALL-UPPERCASE (e.g., 'TESLA').\n"
                "2. CHARGING STATIONS: If the user explicitly asks about charging stations, instruct the Data Analyst to use 'get_charging_stations_stats'. Otherwise, instruct them to report 'Not applicable'.\n"
                "Write a step-by-step plan for the SQL Engineer and Data Analyst."
            ),
            tools=[get_database_schema, get_charging_stations_stats, read_json_data],
            llm=llm,
            allow_delegation=False,
            verbose=True,
            max_iter=3
        )
        
    def sql_engineer_agent(self):
        return Agent(
            role='SQL Engineer',
            goal='Execute SQL queries on PostgreSQL and provide the raw data results.',
            backstory=(
                "You are a SQL Developer. You ONLY use the 'execute_sql_query' tool.\n"
                "Listen carefully to the Architect's plan and write the exact SQL query needed.\n"
                "DATABASE SCHEMA:\n"
                "Table: ev_population\n"
                "Columns: vin_1_10, county, city, state, postal_code, model_year, make, model, electric_vehicle_type, clean_alternative_fuel_vehicle_cafv_eligibility (Valid: 'Clean Alternative Fuel Vehicle Eligible', 'Not eligible due to low battery range'), electric_range, base_msrp\n"
                "Views: view_ev_count_by_city, view_ev_count_by_make, view_ev_count_by_county, view_ev_count_by_model, view_ev_count_by_city_and_make\n"
                "CRITICAL: You MUST use the exact JSON format for the tool:\n"
                "Action: execute_sql_query\n"
                "Action Input: {\"query\": \"SELECT ...\"}\n"
                "Always execute the query and return the actual data."
            ),
            tools=[execute_sql_query, get_database_schema],
            llm=llm,
            allow_delegation=False,
            verbose=True,
            max_iter=3
        )
        
    def data_analyst_agent(self):
        return Agent(
            role='Data Analyst',
            goal='Extract charging station statistics from JSON data to complement the SQL findings.',
            backstory=(
                "You are a Data Analyst. You retrieve statistics about charging stations. "
                "CRITICAL RULE: You DO NOT have access to the SQL database. NEVER try to use 'execute_sql_query' or 'get_database_schema'. "
                "FUNDAMENTAL RULE 1: You DO NOT write PySpark code. You DO NOT write Python code. You ONLY use the 'get_charging_stations_stats' tool. "
                "FUNDAMENTAL RULE 2: The ONLY parameter for 'get_charging_stations_stats' is 'group_by_column'. You MUST choose the correct value based on the user's question from this list: 'city', 'state', 'zip', 'ev_network', 'facility_type'. "
                "For example, if asked about charging networks, use 'ev_network'. If asked about cities, use 'city'.\n"
                "CRITICAL REACT SYNTAX: To use a tool, you MUST use exactly this format:\n"
                "Thought: I need to get charging station stats by [chosen column].\n"
                "Action: get_charging_stations_stats\n"
                "Action Input: {\"group_by_column\": \"[chosen column]\"}\n"
            ),
            tools=[get_charging_stations_stats],
            llm=llm,
            allow_delegation=False,
            verbose=True,
            max_iter=3
        )
        
    def veracity_guardian_agent(self):
        return Agent(
            role='Guardian of Veracity',
            goal='Write a brief, precise, and 100% accurate final report based ONLY on the data provided.',
            backstory=(
                "You are the Guardian of Veracity. Your ONLY job is to take the exact numbers found by the SQL Engineer and Data Analyst and format them into a JSON block and a short Markdown summary. "
                "CRITICAL: You are strictly FORBIDDEN from inventing, guessing, or estimating ANY numbers. If the previous agents found '52078' and '1190', you MUST write exactly '52078' and '1190'. "
                "Do not add extra details or verbose explanations if you don't have the data. Precision is more important than length. "
                "FORMATTING RULE: You MUST write the report and conclusions ABSOLUTELY IN ENGLISH. It is strictly forbidden to write in Italian."
            ),
            tools=[],
            llm=llm,
            allow_delegation=False,
            verbose=True,
            max_iter=3
        )
