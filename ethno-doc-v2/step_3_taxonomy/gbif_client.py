import asyncio
import httpx
import math
import random
import logging
from typing import Optional

from .schemas_step_3 import TaxonomicProfile

logger = logging.getLogger(__name__)

class GBIFResolver:
    def __init__(self):
        self.base_url = "https://api.gbif.org/v1/species/match"
        self.headers = {
            "User-Agent": "EthnoDocBot/2.0 (mailto:infrastructure-admin@ethnodoc.internal)"
        }
        self.timeout = httpx.Timeout(20.0)

    async def resolve_species(self, english_name: str, context_hash: str) -> Optional[TaxonomicProfile]:
        params = {
            "name": english_name,
            "strict": "false"
        }

        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            for attempt in range(5):
                try:
                    response = await client.get(self.base_url, params=params)

                    if response.status_code in (429, 503):
                        delay = (2 ** attempt) + random.uniform(0.5, 1.5)
                        logger.warning(f"Received {response.status_code} from GBIF. Retrying in {delay:.2f} seconds (attempt {attempt + 1}/5).")
                        await asyncio.sleep(delay)
                        continue

                    response.raise_for_status()
                    data = response.json()

                    match_type = data.get("matchType")
                    if match_type == "NONE":
                        logger.warning(f"GBIF returned matchType='NONE' for {english_name}")
                        return None
                    elif match_type in ("EXACT", "FUZZY"):
                        return TaxonomicProfile(
                            context_hash=context_hash,
                            original_english_name=english_name,
                            gbif_usage_key=data.get("usageKey"),
                            accepted_scientific_name=data.get("scientificName"),
                            taxonomic_rank=data.get("rank")
                        )
                    else:
                        logger.warning(f"GBIF returned unexpected matchType='{match_type}' for {english_name}")
                        return None

                except httpx.RequestError as e:
                    delay = (2 ** attempt) + random.uniform(0.5, 1.5)
                    logger.warning(f"Request error: {e}. Retrying in {delay:.2f} seconds (attempt {attempt + 1}/5).")
                    await asyncio.sleep(delay)

            logger.error(f"Failed to resolve {english_name} after 5 attempts.")
            return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    async def main():
        resolver = GBIFResolver()
        profile = await resolver.resolve_species("Turmeric", "mock_hash_1234567890")
        if profile:
            print("Successfully resolved species:")
            print(profile.model_dump_json(indent=2))
        else:
            print("Failed to resolve species.")

    asyncio.run(main())
