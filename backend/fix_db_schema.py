import sys
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Add the directory containing this script to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Load environment variables from .env file
load_dotenv(os.path.join(current_dir, ".env"))

from app.core.config import settings

def fix_schema():
    print("Connecting to database to fix schema...")
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as connection:
            print("Adding 'is_active' column to users table...")
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;"))
            
            print("Adding 'avatar_url' column to users table...")
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR;"))
            
            print("Adding 'settings' column to users table...")
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}';"))
            
            print("Adding 'workspace' column to chat_sessions table...")
            connection.execute(text("ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS workspace VARCHAR DEFAULT 'personal';"))

            print("Adding 'password_verified' column to otp_codes table...")
            connection.execute(text("ALTER TABLE otp_codes ADD COLUMN IF NOT EXISTS password_verified BOOLEAN DEFAULT FALSE;"))

            print("Creating 'snippets' table...")
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS snippets (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES users(id),
                    title VARCHAR NOT NULL,
                    content TEXT NOT NULL,
                    language VARCHAR NOT NULL DEFAULT 'text',
                    tags JSON DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))

            connection.commit()
            print("Schema updated successfully!")
    except Exception as e:
        print(f"Error updating schema: {e}")

if __name__ == "__main__":
    fix_schema()
