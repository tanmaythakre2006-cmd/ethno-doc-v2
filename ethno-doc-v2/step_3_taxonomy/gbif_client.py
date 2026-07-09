import asyncio
import httpx
import math
import random
import logging
import re
from typing import Optional

from step_3_taxonomy.schemas_step_3 import TaxonomicProfile

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

    async def fetch_children(self, parent_usage_key: int) -> list[dict]:
        url = f"https://api.gbif.org/v1/species/{parent_usage_key}/children"

        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            for attempt in range(5):
                try:
                    response = await client.get(url)

                    if response.status_code in (429, 503):
                        delay = (2 ** attempt) + random.uniform(0.5, 1.5)
                        logger.warning(f"Received {response.status_code} fetching children for {parent_usage_key}. Retrying in {delay:.2f}s.")
                        await asyncio.sleep(delay)
                        continue

                    response.raise_for_status()
                    data = response.json()
                    return data.get("results", [])

                except httpx.RequestError as e:
                    delay = (2 ** attempt) + random.uniform(0.5, 1.5)
                    logger.warning(f"Request error fetching children: {e}. Retrying in {delay:.2f}s.")
                    await asyncio.sleep(delay)

            logger.error(f"Failed to fetch children for {parent_usage_key} after 5 attempts.")
            return []

    async def fetch_vernaculars(self, usage_key: int) -> list[str]:
        url = f"https://api.gbif.org/v1/species/{usage_key}/vernacularNames"

        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            for attempt in range(5):
                try:
                    response = await client.get(url)

                    if response.status_code in (429, 503):
                        delay = (2 ** attempt) + random.uniform(0.5, 1.5)
                        logger.warning(f"Received {response.status_code} fetching vernaculars for {usage_key}. Retrying in {delay:.2f}s.")
                        await asyncio.sleep(delay)
                        continue

                    response.raise_for_status()
                    data = response.json()
                    results = data.get("results", [])

                    vernaculars = set()
                    for item in results:
                        lang = item.get("language", "")
                        name = item.get("vernacularName", "")

                        if lang == "zho" or re.search(r'[\u4e00-\u9fff]', name):
                            if name:
                                vernaculars.add(name)

                    return list(vernaculars)

                except httpx.RequestError as e:
                    delay = (2 ** attempt) + random.uniform(0.5, 1.5)
                    logger.warning(f"Request error fetching vernaculars: {e}. Retrying in {delay:.2f}s.")
                    await asyncio.sleep(delay)

            logger.error(f"Failed to fetch vernaculars for {usage_key} after 5 attempts.")
            return []

    async def evaluate_subspecies(self, parent_profile: TaxonomicProfile, extracted_context: str) -> TaxonomicProfile:
        children = await self.fetch_children(parent_profile.gbif_usage_key)

        for child in children:
            child_key = child.get("key") or child.get("usageKey")
            if not child_key:
                continue

            vernaculars = await self.fetch_vernaculars(child_key)
            for v_name in vernaculars:
                if v_name in extracted_context:
                    # Match found! Mutate and return profile
                    return TaxonomicProfile(
                        context_hash=parent_profile.context_hash,
                        original_english_name=parent_profile.original_english_name,
                        gbif_usage_key=child_key,
                        accepted_scientific_name=child.get("scientificName", parent_profile.accepted_scientific_name),
                        taxonomic_rank=child.get("rank", "SUBSPECIES"),
                        is_subspecies_match=True
                    )

        # No match found, return original profile
        return parent_profile

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
