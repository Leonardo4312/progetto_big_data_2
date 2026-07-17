from sqlalchemy import create_engine, text
from config import DATABASE_URI

engine = create_engine(DATABASE_URI)
with engine.connect() as conn:
    conn.execute(text("""
        CREATE OR REPLACE VIEW view_ev_count_by_city_and_make AS
        SELECT city, make, COUNT(*) as total_evs
        FROM ev_population
        GROUP BY city, make
    """))
    conn.commit()
    print("View created successfully.")
