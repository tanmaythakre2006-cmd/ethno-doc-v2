import sqlite3
import pathlib

def initialize_database():
    """
    Initializes the database for step 2 targeting local_vault/step_2_matrix.sqlite.
    Creates the extracted_claims table with a UNIQUE constraint on context_hash.
    Uses isolation_level=None for autocommit/explicit transaction handling.
    """
    # Calculate the absolute path for local_vault/step_2_matrix.sqlite
    # __file__ is step_2_matrix/db_handler_step_2.py
    # parents[1] is ethno-doc-v2/
    base_dir = pathlib.Path(__file__).resolve().parents[1]
    db_path = base_dir / "local_vault" / "step_2_matrix.sqlite"

    # Ensure local_vault directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Connect with isolation_level=None to satisfy constraints in memory instructions
    conn = sqlite3.connect(str(db_path), isolation_level=None)

    # Create the table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS extracted_claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        english_name TEXT NOT NULL,
        taxon_id TEXT NOT NULL,
        character_token TEXT NOT NULL,
        source_book TEXT NOT NULL,
        chapter_metadata TEXT NOT NULL,
        extracted_context TEXT NOT NULL,
        context_hash TEXT NOT NULL UNIQUE,
        confidence_score INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    try:
        conn.execute(create_table_sql)
    finally:
        conn.close()

if __name__ == "__main__":
    initialize_database()
