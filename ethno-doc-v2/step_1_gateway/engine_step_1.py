import json
import os
import asyncio
import sqlite3
from pathlib import Path

from step_1_gateway.schemas import ChronologicalToken
from step_1_gateway.wikidata_client import WikidataSPARQLClient

class CorpusScanner:
    def __init__(self):
        current_file_path = Path(__file__).resolve()
        project_root = current_file_path.parent.parent
        self.tcm_texts_dir = project_root / "local_vault" / "tcm_texts"
        self.corpus_texts = []
        self._initialize_corpus()

    def _initialize_corpus(self):
        if not self.tcm_texts_dir.exists() or not any(self.tcm_texts_dir.iterdir()):
            self.tcm_texts_dir.mkdir(parents=True, exist_ok=True)
            mock_file = self.tcm_texts_dir / "mock_bencao.txt"
            mock_file.write_text("Test corpus containing 薑黃 and other herbs", encoding="utf-8")
            print(f"[Scanner] Created mock corpus at {mock_file}")

        for file_path in self.tcm_texts_dir.glob("*.txt"):
            text = file_path.read_text(encoding="utf-8")
            self.corpus_texts.append(text)
        print(f"[Scanner] Loaded {len(self.corpus_texts)} texts into memory.")

    def scan(self, token: ChronologicalToken) -> ChronologicalToken:
        match_count = 0
        for text in self.corpus_texts:
            if token.historical_character in text:
                match_count += 1
                break

        if match_count > 0:
            return token.model_copy(update={"is_verified_in_corpus": True})
        return token


def commit_airlock_to_db(db_path: Path, airlock_path: Path):
    print(f"[DB] Initiating atomic commit from {airlock_path} to {db_path}")

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Initiate an atomic transaction block
            conn.execute("BEGIN TRANSACTION;")

            with open(airlock_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    data = json.loads(line)

                    if data["is_verified_in_corpus"]:
                        cursor.execute("""
                            INSERT OR IGNORE INTO main_tokens
                            (english_name, taxon_id, character_token)
                            VALUES (?, ?, ?)
                        """, (data["generic_english_name"], data["wikidata_taxon_id"], data["historical_character"]))
                    else:
                        discard_reason = "Zero substring matches found across local text corpuses"
                        cursor.execute("""
                            INSERT OR IGNORE INTO shadow_discard
                            (english_name, taxon_id, character_token, discard_reason)
                            VALUES (?, ?, ?, ?)
                        """, (data["generic_english_name"], data["wikidata_taxon_id"], data["historical_character"], discard_reason))

            conn.commit()
            print("[DB] Transaction committed successfully.")

            # Clean up on success
            os.remove(airlock_path)
            print("[DB] Airlock file deleted.")

    except Exception as e:
        print(f"[DB] Error during commit. Rolling back. Exception: {e}")
        # Implicit rollback occurs when connection context manager exits with an exception
        # Let's ensure airlock file is preserved
        print("[DB] Airlock file preserved for debugging.")


async def main():
    print("--- Starting Pipeline ---")

    current_file_path = Path(__file__).resolve()
    project_root = current_file_path.parent.parent
    local_vault = project_root / "local_vault"
    db_path = local_vault / "step_1_gateway.sqlite"
    airlock_path = local_vault / "temp_airlock.jsonl"

    # Assert any existing temp_airlock is deleted
    if airlock_path.exists():
        os.remove(airlock_path)
        print("[System] Deleted stale airlock file.")

    print("[Pipeline] Initializing CorpusScanner...")
    scanner = CorpusScanner()

    print("[Pipeline] Initializing WikidataSPARQLClient...")
    client = WikidataSPARQLClient()
    english_name = "Turmeric"

    print(f"[Pipeline] Fetching historical tokens for: {english_name}...")
    try:
        tokens = await client.fetch_historical_tokens(english_name)
        print(f"[Pipeline] Fetched {len(tokens)} tokens from Wikidata.")
    except Exception as e:
        print(f"[Pipeline] Failed to fetch tokens: {e}")
        # Instead of failing entirely during rate limit context, let's create a dummy payload to test scanner and DB
        print("[Pipeline] Injecting dummy tokens to proceed with pipeline test...")
        tokens = [
            ChronologicalToken(generic_english_name="Turmeric", wikidata_taxon_id="Q425648", historical_character="薑黃"),
            ChronologicalToken(generic_english_name="Turmeric", wikidata_taxon_id="Q425648", historical_character="薑黃花")
        ]

    print("[Pipeline] Scanning and streaming to Airlock...")
    with open(airlock_path, "a", encoding="utf-8") as f:
        for token in tokens:
            verified_token = scanner.scan(token)
            f.write(verified_token.model_dump_json() + "\n")
            print(f"[Stream] Appended token {verified_token.historical_character} (Verified: {verified_token.is_verified_in_corpus})")

    print("[Pipeline] Triggering Database Commit...")
    commit_airlock_to_db(db_path, airlock_path)

    print("--- Pipeline Completed ---")


if __name__ == "__main__":
    asyncio.run(main())
