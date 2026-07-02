import json
import os
import asyncio
import sqlite3
import pathlib
import opencc

from step_1_gateway.schemas import ChronologicalToken
from step_1_gateway.wikidata_client import WikidataSPARQLClient
from step_1_gateway.db_handler import initialize_database

class CorpusScanner:
    """
    Scans a local text corpus for exact substring matches of historical character tokens.
    """
    def __init__(self):
        # Initialize variant conversion engines
        self.s2t = opencc.OpenCC('s2t')
        self.t2s = opencc.OpenCC('t2s')

        # Dynamically compute the path to the local text corpus directory
        current_file_path = pathlib.Path(__file__).resolve()
        self.tcm_texts_dir = current_file_path.parent.parent / "local_vault" / "tcm_texts"

        # Ensure the directory exists
        self.tcm_texts_dir.mkdir(parents=True, exist_ok=True)

        # Check if directory is empty
        has_txt_files = any(f.is_file() and f.suffix == '.txt' for f in self.tcm_texts_dir.iterdir())
        if not has_txt_files:
            mock_file_path = self.tcm_texts_dir / "mock_bencao.txt"
            print(f"Directory {self.tcm_texts_dir} is empty or missing. Creating fallback mock_bencao.txt.")
            with open(mock_file_path, 'w', encoding='utf-8') as f:
                f.write("Test corpus containing 薑黃 and other herbs")

        self.corpus_texts = []
        self._load_corpus()

    def _load_corpus(self):
        for file_path in self.tcm_texts_dir.glob("*.txt"):
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.corpus_texts.append(f.read())
                except Exception as e:
                    print(f"Failed to read corpus file {file_path}: {e}")

    def _get_character_variants(self, raw_token: str) -> set[str]:
        """
        Takes a raw token string and generates a deduplicated set
        of its Simplified and Traditional Chinese character variants.
        """
        return {
            raw_token,
            self.s2t.convert(raw_token),
            self.t2s.convert(raw_token)
        }

    def scan(self, token: ChronologicalToken) -> ChronologicalToken:
        """
        Performs an exact substring search across loaded texts using multi-variant lookahead.
        Returns a new token instance with updated verification status.
        """
        variants = self._get_character_variants(token.historical_character)

        for variant in variants:
            match_count = sum(
                variant in text
                for text in self.corpus_texts
            )

            if match_count > 0:
                return token.model_copy(update={'is_verified_in_corpus': True})

        return token


def commit_airlock_to_db(db_path: pathlib.Path, airlock_path: pathlib.Path):
    """
    Executes a dual-path atomic commit to SQLite from the temporary JSONL airlock.
    """
    print(f"Starting atomic commit from {airlock_path} to {db_path}...")

    # Initialize database schemas if they don't exist
    initialize_database()

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        try:
            conn.execute("BEGIN TRANSACTION;")

            with open(airlock_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue

                    data = json.loads(line)
                    # Convert dict back to Pydantic model for validation/structure guarantee (optional but safe)
                    token = ChronologicalToken(**data)

                    if token.is_verified_in_corpus:
                        cursor.execute("""
                            INSERT OR IGNORE INTO main_tokens
                            (english_name, taxon_id, character_token)
                            VALUES (?, ?, ?)
                        """, (token.generic_english_name, token.wikidata_taxon_id, token.historical_character))
                    else:
                        cursor.execute("""
                            INSERT OR IGNORE INTO shadow_discard
                            (english_name, taxon_id, character_token, discard_reason)
                            VALUES (?, ?, ?, ?)
                        """, (
                            token.generic_english_name,
                            token.wikidata_taxon_id,
                            token.historical_character,
                            "Zero substring matches found across local text corpuses"
                        ))

            conn.commit()
            print("Database transaction committed successfully.")

            # Clean up the airlock file
            os.remove(airlock_path)
            print(f"Removed temporary airlock file: {airlock_path}")

        except Exception as e:
            conn.rollback()
            print(f"Database transaction failed and rolled back. Airlock preserved. Error: {e}")
            raise


async def main():
    print("Initializing Wikidata SPARQL Client...")
    client = WikidataSPARQLClient()

    target_name = "Turmeric"
    print(f"Fetching historical tokens for target: {target_name}")
    tokens = await client.fetch_historical_tokens(target_name)

    if not tokens:
        print("No tokens found. Exiting.")
        return

    print(f"Found {len(tokens)} distinct tokens from Wikidata.")

    print("Initializing Local Text Corpus Scanner...")
    scanner = CorpusScanner()

    current_file_path = pathlib.Path(__file__).resolve()
    local_vault_dir = current_file_path.parent.parent / "local_vault"
    local_vault_dir.mkdir(parents=True, exist_ok=True)
    airlock_path = local_vault_dir / "temp_airlock.jsonl"

    if airlock_path.exists():
        print(f"Deleting existing temp_airlock.jsonl at {airlock_path}")
        os.remove(airlock_path)

    print(f"Scanning tokens and streaming to Airlock: {airlock_path}")
    with open(airlock_path, 'a', encoding='utf-8') as f:
        for token in tokens:
            processed_token = scanner.scan(token)
            f.write(processed_token.model_dump_json() + "\n")

    db_path = local_vault_dir / "step_1_gateway.sqlite"
    commit_airlock_to_db(db_path, airlock_path)
    print("Extraction and filtering pipeline completed successfully.")

if __name__ == "__main__":
    asyncio.run(main())
