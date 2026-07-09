import sqlite3
import pathlib

def initialize_database():
    db_path = pathlib.Path(__file__).resolve().parent.parent / "local_vault" / "step_3_taxonomy.sqlite"

    # Ensure local_vault directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS taxonomic_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                context_hash TEXT NOT NULL,
                original_english_name TEXT NOT NULL,
                gbif_usage_key INTEGER NOT NULL,
                accepted_scientific_name TEXT NOT NULL,
                taxonomic_rank TEXT NOT NULL,
                is_subspecies_match BOOLEAN NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(context_hash)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_gbif_usage_key ON taxonomic_profiles(gbif_usage_key)")
