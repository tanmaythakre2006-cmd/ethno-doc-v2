import sqlite3
import pathlib
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def initialize_database():
    """
    Idempotent database initialization function using Python's native sqlite3.
    Creates tables and indexes without duplicating them.
    """
    try:
        # Compute the absolute path dynamically
        current_file_path = pathlib.Path(__file__).resolve()
        project_root = current_file_path.parent.parent
        db_path = project_root / "local_vault" / "step_1_gateway.sqlite"

        # Ensure the target directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initializing database at: {db_path}")

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Start transaction block explicitly (optional in sqlite3 context manager, but good practice)
            conn.execute("BEGIN TRANSACTION;")

            # Create main_tokens table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS main_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                english_name TEXT NOT NULL,
                taxon_id TEXT NOT NULL,
                character_token TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(english_name, character_token)
            );
            """)

            # Create shadow_discard table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS shadow_discard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                english_name TEXT NOT NULL,
                taxon_id TEXT NOT NULL,
                character_token TEXT NOT NULL,
                discard_reason TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Create performance optimization indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_main_tokens_english_name ON main_tokens(english_name);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_main_tokens_character_token ON main_tokens(character_token);")

            # Commit the transaction block
            conn.commit()

        logger.info(f"Successfully initialized database structures at: {db_path}")

    except sqlite3.Error as e:
        logger.error(f"Database initialization failed due to SQLite error: {e}")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")


if __name__ == "__main__":
    initialize_database()
