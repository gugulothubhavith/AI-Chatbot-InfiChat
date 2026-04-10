"""Migration: Add new columns to system_updates table"""
from app.database.db import engine
from sqlalchemy import text

def run():
    with engine.connect() as conn:
        existing = conn.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name='system_updates'")
        ).fetchall()
        existing_names = [r[0] for r in existing]
        print("Existing columns:", existing_names)
        
        if 'status' not in existing_names:
            conn.execute(text("ALTER TABLE system_updates ADD COLUMN status VARCHAR DEFAULT 'active'"))
            print("Added: status")
        if 'is_active' not in existing_names:
            conn.execute(text("ALTER TABLE system_updates ADD COLUMN is_active BOOLEAN DEFAULT true"))
            print("Added: is_active")
        if 'checksum' not in existing_names:
            conn.execute(text("ALTER TABLE system_updates ADD COLUMN checksum VARCHAR"))
            print("Added: checksum")
        if 'download_count' not in existing_names:
            conn.execute(text("ALTER TABLE system_updates ADD COLUMN download_count INTEGER DEFAULT 0"))
            print("Added: download_count")
        conn.commit()
        print("Migration complete!")

if __name__ == "__main__":
    run()
