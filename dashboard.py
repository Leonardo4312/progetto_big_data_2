# pyrefly: ignore [missing-import]
# pyright: reportAttributeAccessIssue=false, reportArgumentType=false, reportCallIssue=false
"""
Query aggregate per la Dashboard di EV Nexus.

Fonti dati reali del progetto:
- ev_population: tabella Postgres, ingestita da database_setup.py e pulita da clean_db.py
- charging_stations.json: file generato da database_setup.py (extract_real_charging_stations),
  NON è una tabella SQL. Viene letto direttamente qui — è la parte "semi-strutturata"
  della Variety richiesta dal corso.
- kaggle_income.csv: letto direttamente da file (non è in Postgres), filtrato su WA e
  incrociato per ZIP con ev_population. È la fusione dataset "reddito vs adozione EV".
"""
import os
import json
import pandas as pd 
from sqlalchemy import create_engine, text 
from config import DATABASE_URI, JSON_DATA_PATH, DATA_DIR # type: ignore

engine = create_engine(DATABASE_URI)

INCOME_CSV_PATH = os.path.join(DATA_DIR, "kaggle_income.csv")

# Bucket per la distribuzione dell'autonomia (electric_range in miglia)
RANGE_BINS = [0, 50, 100, 150, 200, 250, 10_000]
RANGE_LABELS = ["0-50", "50-100", "100-150", "150-200", "200-250", "250+"]


def _sql_df(query):
    return pd.read_sql(text(query), engine)


def _load_stations():
    """Legge il file JSON con le stazioni di ricarica (non è in Postgres)."""
    with open(JSON_DATA_PATH) as f:
        records = json.load(f)
    return pd.DataFrame(records)


def _clean_zip(series):
    """Normalizza i CAP a 5 cifre zero-padded, per fare match tra fonti diverse."""
    return series.astype(str).str.extract(r"(\d{1,5})")[0].str.zfill(5)


def _first_present(df, candidates):
    """Trova la prima colonna esistente tra i possibili nomi (i nomi esatti dipendono
    dall'header originale dell'xlsx, che non abbiamo sott'occhio)."""
    for c in candidates:
        if c in df.columns:
            return c
    return None


def get_kpis(include_charging=False):
    total_ev = int(_sql_df("SELECT COUNT(*) AS n FROM ev_population")["n"].iloc[0])

    avg_range_row = _sql_df("SELECT AVG(electric_range) AS v FROM ev_population WHERE electric_range > 0")
    avg_range = round(float(avg_range_row["v"].iloc[0] or 0), 1)

    total_stations = 0
    dc_fast = 0

    if include_charging:
        try:
            stations = _load_stations()
            total_stations = len(stations)
            dc_col = _first_present(stations, ["ev_dc_fast_count", "ev_dc_fast_num"])
            if dc_col:
                dc_fast = int(pd.to_numeric(stations[dc_col], errors="coerce").fillna(0).sum()) # type: ignore
        except Exception:
            pass

    return {
        "total_ev": total_ev,
        "total_stations": total_stations,
        "dc_fast_chargers": dc_fast,
        "avg_range": avg_range,
    }


def get_top_makes(limit=8):
    df = _sql_df(f"""
        SELECT make AS name, COUNT(*) AS value
        FROM ev_population
        GROUP BY make
        ORDER BY value DESC
        LIMIT {limit}
    """)
    return df.to_dict(orient="records") # type: ignore


def get_range_distribution():
    df = _sql_df("SELECT electric_range FROM ev_population WHERE electric_range > 0")
    df["bucket"] = pd.cut(df["electric_range"], bins=RANGE_BINS, labels=RANGE_LABELS, right=False)
    out = df.groupby("bucket", observed=True).size().reindex(RANGE_LABELS, fill_value=0)
    return [{"name": k, "value": int(v)} for k, v in out.items()]


def get_ev_by_county(limit=10):
    df = _sql_df(f"""
        SELECT county AS name, COUNT(*) AS value
        FROM ev_population
        WHERE county IS NOT NULL AND county != ''
        GROUP BY county
        ORDER BY value DESC
        LIMIT {limit}
    """)
    return df.to_dict(orient="records") # type: ignore


def get_registration_trends():
    df = _sql_df("""
        SELECT model_year AS name, COUNT(*) AS value
        FROM ev_population
        WHERE model_year IS NOT NULL AND model_year > 2010
        GROUP BY model_year
        ORDER BY model_year
    """)
    return df.to_dict(orient="records") # type: ignore


def get_network_share(limit=8):
    """Quota di stazioni per network di ricarica, letta dal JSON (dato semi-strutturato)."""
    try:
        stations = _load_stations()
        net_col = _first_present(stations, ["ev_network"])
        if not net_col:
            return []
        counts = stations[net_col].replace("", "Not specified").fillna("Not specified").value_counts().head(limit) # type: ignore
        return [{"name": str(k), "value": int(v)} for k, v in counts.items()]
    except Exception:
        return []


def get_income_vs_ev(limit=40):
    """
    Fusione dataset: reddito medio per ZIP (kaggle_income.csv, filtrato su WA)
    incrociato con il numero di EV registrate nello stesso ZIP (ev_population).
    Restituisce [] se il CSV non è presente o non ha le colonne attese, invece di errore.
    """
    if not os.path.exists(INCOME_CSV_PATH):
        return []

    try:
        income = pd.read_csv(INCOME_CSV_PATH, encoding="latin-1")
        income.columns = [c.strip() for c in income.columns]

        state_col = _first_present(income, ["State_ab", "state_ab", "State", "state"])
        zip_col = _first_present(income, ["Zip_Code", "zip_code", "Zip", "zip"])
        mean_col = _first_present(income, ["Mean", "mean"])

        if not (state_col and zip_col and mean_col):
            return []

        income = income[income[state_col] == "WA"].copy()
        if income.empty:
            return []

        income["zip"] = _clean_zip(income[zip_col])
        income_by_zip = (
            income.groupby("zip")[mean_col].mean().reset_index().rename(columns={mean_col: "mean_income"}) # type: ignore
        )

        ev = _sql_df("""
            SELECT postal_code, COUNT(*) AS ev_count
            FROM ev_population
            GROUP BY postal_code
        """)
        ev["zip"] = _clean_zip(ev["postal_code"])
        ev_by_zip = ev.groupby("zip")["ev_count"].sum().reset_index() # type: ignore

        merged = ev_by_zip.merge(income_by_zip, on="zip", how="inner")
        merged = merged.sort_values("ev_count", ascending=False).head(limit)
        merged["mean_income"] = merged["mean_income"].round(0)

        return merged[["zip", "mean_income", "ev_count"]].to_dict(orient="records") # type: ignore
    except Exception:
        return []


def get_marketing_adoption():
    """
    Correlazione tra il reddito medio delle contee (Kaggle CSV) e la penetrazione di auto di fascia alta (Tesla, Rivian, Lucid Motors)
    """
    if not os.path.exists(INCOME_CSV_PATH):
        return []

    try:
        income = pd.read_csv(INCOME_CSV_PATH, encoding="latin-1")
        income.columns = [c.strip() for c in income.columns]
        state_col = _first_present(income, ["State_ab", "state_ab", "State", "state"])
        county_col = _first_present(income, ["County", "county"])
        mean_col = _first_present(income, ["Mean", "mean"])

        if not (state_col and county_col and mean_col):
            return []

        income = income[income[state_col] == "WA"].copy()
        if income.empty:
            return []

        income["clean_county"] = income[county_col].str.replace(' County', '', case=False).str.strip().str.lower()
        income_by_county = income.groupby("clean_county")[mean_col].mean().reset_index().rename(columns={mean_col: "mean_income"}) # type: ignore

        ev_by_county = _sql_df("""
            SELECT county,
                   COUNT(CASE WHEN make IN ('TESLA', 'RIVIAN', 'LUCID MOTORS') THEN 1 END) AS premium_ev_count,
                   COUNT(*) AS total_ev_count
            FROM ev_population
            WHERE county IS NOT NULL AND county != ''
            GROUP BY county
        """)
        ev_by_county["clean_county"] = ev_by_county["county"].str.strip().str.lower()

        merged = ev_by_county.merge(income_by_county, on="clean_county", how="inner")
        merged["premium_ev_penetration"] = (merged["premium_ev_count"] / merged["total_ev_count"] * 100).round(2)
        merged["mean_income"] = merged["mean_income"].round(0)

        # Ripristina casing originale
        casing = dict(zip(ev_by_county["clean_county"], ev_by_county["county"]))
        merged["county"] = merged["clean_county"].map(casing) # type: ignore

        return merged[["county", "mean_income", "premium_ev_count", "total_ev_count", "premium_ev_penetration"]].sort_values("mean_income", ascending=False).to_dict(orient="records") # type: ignore
    except Exception:
        return []


def get_infrastructure_deficit():
    """
    Rapporto numerico tra EV registrati per Contea e numero di colonnine rapide (Level 3/DC Fast).
    """
    try:
        ev_by_county = _sql_df("""
            SELECT county, COUNT(*) as ev_count
            FROM ev_population
            WHERE county IS NOT NULL AND county != ''
            GROUP BY county
        """)
        ev_by_county["clean_county"] = ev_by_county["county"].str.strip().str.lower()

        zip_map = _sql_df("""
            SELECT DISTINCT postal_code, county
            FROM ev_population
            WHERE county IS NOT NULL AND county != '' AND postal_code IS NOT NULL
        """)
        zip_map["zip_str"] = _clean_zip(zip_map["postal_code"])
        zip_map = zip_map.drop_duplicates(subset=["zip_str"])
        zip_to_county_dict = dict(zip(zip_map["zip_str"], zip_map["county"]))

        stations = _load_stations()
        zip_col = _first_present(stations, ["zip"])
        dc_col = _first_present(stations, ["ev_dc_fast_count", "ev_dc_fast_num"])

        if not (zip_col and dc_col):
            return []

        stations["zip_str"] = _clean_zip(stations[zip_col])
        stations["county"] = stations["zip_str"].map(zip_to_county_dict) # type: ignore

        stations["dc_fast"] = pd.to_numeric(stations[dc_col], errors="coerce").fillna(0) # type: ignore
        stations_by_county = stations.groupby("county")["dc_fast"].sum().reset_index() # type: ignore
        stations_by_county["clean_county"] = stations_by_county["county"].str.strip().str.lower()

        merged = ev_by_county.merge(stations_by_county, on="clean_county", how="left")
        merged["dc_fast"] = merged["dc_fast"].fillna(0).astype(int) # type: ignore

        # Deficit ratio (EV per charger)
        merged["ev_per_charger"] = (merged["ev_count"] / (merged["dc_fast"] + 0.1)).round(1)
        merged = merged.sort_values(by="ev_per_charger", ascending=False)

        casing = dict(zip(ev_by_county["clean_county"], ev_by_county["county"]))
        merged["county"] = merged["clean_county"].map(casing) # type: ignore

        return merged[["county", "ev_count", "dc_fast", "ev_per_charger"]].to_dict(orient="records") # type: ignore
    except Exception:
        return []


def get_range_vs_manufacturer():
    """
    Analisi evoluzione autonomia dei top brand nel tempo.
    """
    try:
        top_makes_df = _sql_df("""
            SELECT make, COUNT(*) as cnt
            FROM ev_population
            GROUP BY make
            ORDER BY cnt DESC
            LIMIT 6
        """)
        top_makes = tuple(top_makes_df["make"].tolist())
        if not top_makes:
            return []

        df = _sql_df(f"""
            SELECT make, model_year, AVG(electric_range) AS avg_range, COUNT(*) AS vehicle_count
            FROM ev_population
            WHERE make IN {top_makes} AND electric_range > 0 AND model_year >= 2012
            GROUP BY make, model_year
            ORDER BY model_year, make
        """)
        df["avg_range"] = df["avg_range"].round(1)
        return df.to_dict(orient="records") # type: ignore
    except Exception:
        return []


def get_dashboard_payload(include_charging=False, include_income=False):
    payload = {
        "kpis": get_kpis(include_charging=include_charging),
        "top_makes": get_top_makes(),
        "range_distribution": get_range_distribution(),
        "ev_by_county": get_ev_by_county(),
        "registration_trends": get_registration_trends(),
        "range_vs_manufacturer": get_range_vs_manufacturer(),
    }

    if include_charging:
        payload["network_share"] = get_network_share()
        payload["infrastructure_deficit"] = get_infrastructure_deficit()
    else:
        payload["network_share"] = []
        payload["infrastructure_deficit"] = []

    if include_income:
        payload["income_vs_ev"] = get_income_vs_ev()
        payload["marketing_adoption"] = get_marketing_adoption()
    else:
        payload["income_vs_ev"] = []
        payload["marketing_adoption"] = []

    return payload

