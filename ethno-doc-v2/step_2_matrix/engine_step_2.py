import os
import re
import hashlib
import sqlite3
import pathlib
import sys

from step_2_matrix.schemas_step_2 import ExtractedClaim
from step_2_matrix.segmenter import ContextExtractor

BOOK_CONFIDENCE_MATRIX = {
    "shennong_bencaojing.txt": 5,
    "bencao_gangmu.txt": 5,
    "leigong_paozhilun.txt": 4,
    "mock_bencao.txt": 1
}

def get_confidence_score(filename: str) -> int:
    return BOOK_CONFIDENCE_MATRIX.get(filename, 3)

def main():
    base_dir = pathlib.Path(__file__).resolve().parents[1]
    local_vault = base_dir / "local_vault"
    tcm_texts_dir = local_vault / "tcm_texts"
    step1_db_path = local_vault / "step_1_gateway.sqlite"
    step2_db_path = local_vault / "step_2_matrix.sqlite"

    if not tcm_texts_dir.exists() or not any(tcm_texts_dir.iterdir()):
        print("[NOTICE] local_vault/tcm_texts/ is empty or missing. Terminating gracefully.")
        sys.exit(0)

    try:
        conn1 = sqlite3.connect(f"file:{step1_db_path}?mode=ro", uri=True)
    except sqlite3.OperationalError:
        conn1 = sqlite3.connect(str(step1_db_path))

    conn1.row_factory = sqlite3.Row
    cur1 = conn1.cursor()
    cur1.execute("SELECT english_name, taxon_id, character_token FROM main_tokens")
    tokens = cur1.fetchall()

    clean_tokens = [(row["english_name"], row["taxon_id"], row["character_token"]) for row in tokens]
    conn1.close()

    total_tokens_from_step1 = len(clean_tokens)
    total_text_files_processed = 0
    raw_substring_matches_found = 0
    duplicate_hashes_ignored = 0
    successful_sqlite_insertions = 0

    conn2 = sqlite3.connect(str(step2_db_path), isolation_level=None)
    conn2.execute("BEGIN TRANSACTION;")

    # PATCHED: Batch Committing (RAM Flush) (engine_step_2.py)
    batch_count = 0

    for filepath in tcm_texts_dir.glob("*.txt"):
        total_text_files_processed += 1
        filename = filepath.name
        score = get_confidence_score(filename)

        extractor = ContextExtractor()
        # PATCHED: The Metadata State Wipe (engine_step_2.py)
        extractor.current_chapter = "Metadata Unspecified"

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                extractor.track_chapter(line)

                compressed_line = re.sub(r'\s+', '', line)

                for english_name, taxon_id, character_token in clean_tokens:
                    compressed_token = re.sub(r'\s+', '', character_token)

                    if compressed_token and compressed_token in compressed_line:
                        pattern = r'\s*'.join(re.escape(c) for c in compressed_token)
                        match = re.search(pattern, line)
                        if match:
                            actual_token = match.group(0)
                            contexts = extractor.extract_context(line, actual_token)

                            for ctx in contexts:
                                raw_substring_matches_found += 1

                                context_hash = hashlib.sha256(f"{ctx}{taxon_id}".encode('utf-8')).hexdigest()

                                claim = ExtractedClaim(
                                    english_name=english_name,
                                    taxon_id=taxon_id,
                                    character_token=character_token,
                                    source_book=filename,
                                    chapter_metadata=extractor.current_chapter,
                                    extracted_context=ctx,
                                    context_hash=context_hash,
                                    confidence_score=score
                                )

                                insert_sql = """
                                INSERT OR IGNORE INTO extracted_claims
                                (english_name, taxon_id, character_token, source_book, chapter_metadata, extracted_context, context_hash, confidence_score)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """
                                cur2 = conn2.cursor()
                                cur2.execute(insert_sql, (
                                    claim.english_name,
                                    claim.taxon_id,
                                    claim.character_token,
                                    claim.source_book,
                                    claim.chapter_metadata,
                                    claim.extracted_context,
                                    claim.context_hash,
                                    claim.confidence_score
                                ))

                                if cur2.rowcount == 0:
                                    duplicate_hashes_ignored += 1
                                else:
                                    successful_sqlite_insertions += 1

                                    # PATCHED: Batch Committing (RAM Flush) (engine_step_2.py)
                                    batch_count += 1
                                    if batch_count % 1000 == 0:
                                        conn2.commit()
                                        conn2.execute("BEGIN TRANSACTION;")

    # PATCHED: Batch Committing (RAM Flush) (engine_step_2.py)
    conn2.commit()
    conn2.close()

    os.system('cls' if os.name == 'nt' else 'clear')

    dashboard = f"""==========================================================
              ETHNO-DOC-V2: STEP 2 TELEMETRY
==========================================================
[SYSTEM STAGE] : Step 2 (The Matrix Searcher) Complete
[TOTAL TOKENS INGESTED]       : {total_tokens_from_step1}
[ACTIVE CORPUS FILES SCANNED] : {total_text_files_processed}
[TOTAL TARGET MATCHES FOUND]  : {raw_substring_matches_found}
[DUPLICATES DROPPED (SHA256)] : {duplicate_hashes_ignored}
[CLEAN CLAIMS COMMITTED]      : {successful_sqlite_insertions}
=========================================================="""
    print(dashboard)

if __name__ == "__main__":
    main()
