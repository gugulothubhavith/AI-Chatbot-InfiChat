from app.database.db import engine
from sqlalchemy import text
with engine.connect() as conn:
    r = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='system_updates' ORDER BY ordinal_position"))
    cols = [x[0] for x in r.fetchall()]
    print("Columns:", cols)
