import sqlite3
import asyncio
import pathlib
import sys
import logging
from typing import List, Tuple

from step_3_taxonomy.schemas_step_3 import TaxonomicProfile
from step_3_taxonomy.gbif_client import GBIFResolver

logger = logging.getLogger(__name__)

def fetch_claims_from_step2() -> List[Tuple[str, str, str, str]]:
    db_path = pathlib.Path(__file__).resolve().parent.parent / "local_vault" / "step_2_matrix.sqlite"
    if not db_path.exists():
        logger.error(f"Step 2 database not found at {db_path}")
        return []

    try:
        # Read-only connection to ensure we don't cross-contaminate
        uri = f"{db_path.as_uri()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as conn:
            cursor = conn.execute("SELECT context_hash, english_name, character_token, extracted_context FROM extracted_claims")
            rows = cursor.fetchall()
            return rows
    except Exception as e:
        logger.error(f"Failed to read from step 2 matrix: {e}")
        return []

async def run_pipeline():
    claims = fetch_claims_from_step2()
    total_claims = len(claims)

    if total_claims == 0:
        print("No claims found in step 2 matrix.")
        return

    resolver = GBIFResolver()

    successful_parent_resolutions = 0
    total_subspecies_upgrades = 0
    failed_resolutions = 0
    total_db_insertions = 0

    processed_profiles: List[TaxonomicProfile] = []

    try:
        for context_hash, english_name, character_token, extracted_context in claims:
            # Step B: Resolve Parent
            parent_profile = await resolver.resolve_species(english_name, context_hash)

            if not parent_profile:
                failed_resolutions += 1
                continue

            successful_parent_resolutions += 1

            # Step B: Evaluate Subspecies
            final_profile = await resolver.evaluate_subspecies(parent_profile, extracted_context)
            if final_profile.is_subspecies_match:
                total_subspecies_upgrades += 1

            processed_profiles.append(final_profile)

    except Exception as e:
        logger.error(f"Pipeline interrupted: {e}")
        # Proceed to save whatever we have so far

    # Step C: Titanium Batch Committing
    db_path_step3 = pathlib.Path(__file__).resolve().parent.parent / "local_vault" / "step_3_taxonomy.sqlite"

    # Ensure local_vault exists and schema is initialized
    from step_3_taxonomy.db_handler_step_3 import initialize_database
    initialize_database()

    try:
        with sqlite3.connect(db_path_step3, isolation_level=None) as conn:
            conn.execute("BEGIN TRANSACTION;")

            for count, profile in enumerate(processed_profiles, start=1):
                conn.execute("""
                    INSERT OR IGNORE INTO taxonomic_profiles (
                        context_hash, original_english_name, gbif_usage_key,
                        accepted_scientific_name, taxonomic_rank, is_subspecies_match
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    profile.context_hash,
                    profile.original_english_name,
                    profile.gbif_usage_key,
                    profile.accepted_scientific_name,
                    profile.taxonomic_rank,
                    profile.is_subspecies_match
                ))
                total_db_insertions += 1

                if count % 1000 == 0:
                    conn.execute("COMMIT;")
                    conn.execute("BEGIN TRANSACTION;")

            conn.execute("COMMIT;")
    except Exception as e:
        logger.error(f"Failed to commit to step 3 database: {e}")

    # Output Telemetry Dashboard
    # Clear screen
    print("\033[H\033[J", end="")

    dashboard = f"""==========================================================
              ETHNO-DOC-V2: STEP 3 TELEMETRY
==========================================================
[SYSTEM STAGE] : Step 3 (The Taxonomic Deep-Dive) Complete
[RAW CLAIMS INGESTED]         : {total_claims}
[PARENT SPECIES RESOLVED]     : {successful_parent_resolutions}
[SUBSPECIES UPGRADES EXECUTED]: {total_subspecies_upgrades}
[GBIF RESOLUTION FAILURES]    : {failed_resolutions}
[PROFILES COMMITTED TO DB]    : {total_db_insertions}
=========================================================="""
    print(dashboard)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_pipeline())
