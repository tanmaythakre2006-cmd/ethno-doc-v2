import sqlite3
import pathlib
import sys

from step_1_gateway.engine_step_1 import CorpusScanner
from step_1_gateway.schemas import ChronologicalToken

def main():
    current_file_path = pathlib.Path(__file__).resolve()
    db_path = current_file_path.parent.parent / "local_vault" / "step_1_gateway.sqlite"

    print("Initializing Local Text Corpus Scanner for resurrection...")
    scanner = CorpusScanner()

    records_checked = 0
    records_resurrected = 0
    discarded_tokens = []

    try:
        with sqlite3.connect(db_path, isolation_level=None) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, english_name, taxon_id, character_token FROM shadow_discard")
            shadow_rows = cursor.fetchall()

            for row in shadow_rows:
                row_id, english_name, taxon_id, character_token = row
                records_checked += 1

                token = ChronologicalToken(
                    generic_english_name=english_name,
                    wikidata_taxon_id=taxon_id,
                    historical_character=character_token
                )

                processed_token = scanner.scan(token)

                if processed_token.is_verified_in_corpus:
                    try:
                        conn.execute("BEGIN TRANSACTION;")
                        conn.execute("""
                            INSERT OR IGNORE INTO main_tokens (english_name, taxon_id, character_token)
                            VALUES (?, ?, ?)
                        """, (english_name, taxon_id, character_token))

                        conn.execute("DELETE FROM shadow_discard WHERE id = ?", (row_id,))
                        conn.execute("COMMIT;")
                        records_resurrected += 1
                        print(f"Resurrected: {character_token}")
                    except Exception as e:
                        conn.execute("ROLLBACK;")
                        print(f"Error migrating token {character_token}: {e}", file=sys.stderr)
                else:
                    discarded_tokens.append(character_token)

    except sqlite3.Error as e:
        print(f"Database error: {e}", file=sys.stderr)

    print(f"\n--- Resurrection Summary ---")
    print(f"Total shadow records checked: {records_checked}")
    print(f"Total successfully resurrected to main_tokens: {records_resurrected}")
    print(f"Tokens that remain discarded: {discarded_tokens}")

if __name__ == "__main__":
    main()
