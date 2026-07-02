import asyncio
import httpx
import random
import sys
from typing import List

from step_1_gateway.schemas import ChronologicalToken

class WikidataRateLimitException(Exception):
    """Custom exception raised when Wikidata rate limits are exceeded after retries."""
    pass

class WikidataSPARQLClient:
    """
    An asynchronous client for querying Wikidata via SPARQL, designed with aggressive
    backoff/retry logic and defensive timeouts.
    """
    def __init__(self):
        self.endpoint_url = "https://query.wikidata.org/sparql"
        self.headers = {
            "User-Agent": "EthnoDocBot/2.0 (mailto:infrastructure-admin@ethnodoc.internal) httpx/asyncio",
            "Accept": "application/sparql-results+json"
        }
        # Connection timeout of 15.0s, read timeout of 30.0s
        self.timeout = httpx.Timeout(connect=15.0, read=30.0, write=15.0, pool=15.0)

    async def _execute_query(self, query: str) -> dict:
        max_attempts = 5

        async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
            for attempt in range(max_attempts):
                try:
                    response = await client.get(
                        self.endpoint_url,
                        params={"query": query}
                    )

                    if response.status_code in (429, 502, 503, 504):
                        delay = (2 ** attempt) + random.uniform(0.5, 1.5)
                        sys.stderr.write(f"Warning: Received HTTP {response.status_code}. Retrying in {delay:.2f} seconds (Attempt {attempt + 1}/{max_attempts}).\n")
                        await asyncio.sleep(delay)
                        continue

                    response.raise_for_status()
                    return response.json()

                except httpx.HTTPStatusError as e:
                    if e.response.status_code in (429, 502, 503, 504):
                        delay = (2 ** attempt) + random.uniform(0.5, 1.5)
                        sys.stderr.write(f"Warning: Received HTTP {e.response.status_code}. Retrying in {delay:.2f} seconds (Attempt {attempt + 1}/{max_attempts}).\n")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise e
                except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
                    delay = (2 ** attempt) + random.uniform(0.5, 1.5)
                    sys.stderr.write(f"Warning: Timeout occurred. Retrying in {delay:.2f} seconds (Attempt {attempt + 1}/{max_attempts}).\n")
                    await asyncio.sleep(delay)
                    continue

            raise WikidataRateLimitException("Max retry attempts reached for Wikidata SPARQL endpoint.")

    async def fetch_historical_tokens(self, english_name: str) -> List[ChronologicalToken]:
        english_name_lower = english_name.lower().strip()

        query = f"""
        SELECT DISTINCT ?taxon ?token ?is_tcm ?is_east_asia WHERE {{
          {{
            ?taxon rdfs:label "{english_name_lower}"@en .
          }} UNION {{
            ?taxon skos:altLabel "{english_name_lower}"@en .
          }}

          ?taxon wdt:P31/wdt:P279* wd:Q16521 .

          {{
            ?taxon rdfs:label ?token .
            FILTER(LANG(?token) IN ("zh", "zh-hans", "zh-hant", "zh-cn", "zh-tw", "zh-hk"))
          }} UNION {{
            ?taxon skos:altLabel ?token .
            FILTER(LANG(?token) IN ("zh", "zh-hans", "zh-hant", "zh-cn", "zh-tw", "zh-hk"))
          }}

          OPTIONAL {{
            ?taxon wdt:P2283 wd:Q200253 .
            BIND(1 AS ?is_tcm)
          }}
          OPTIONAL {{
            ?taxon wdt:P3034 ?range .
            FILTER(?range IN (wd:Q148, wd:Q27231, wd:Q48, wd:Q865, wd:Q17))
            BIND(1 AS ?is_east_asia)
          }}
        }} ORDER BY DESC(?is_tcm) DESC(?is_east_asia)
        """

        data = await self._execute_query(query)
        bindings = data.get("results", {}).get("bindings", [])

        if not bindings:
            return []

        best_taxon_uri = bindings[0]["taxon"]["value"]
        wikidata_taxon_id = best_taxon_uri.split("/")[-1]

        unique_tokens = set()

        for row in bindings:
            if row["taxon"]["value"] == best_taxon_uri:
                token_val = row["token"]["value"]
                unique_tokens.add(token_val)

        results = []
        for token in unique_tokens:
            model = ChronologicalToken(
                generic_english_name=english_name,
                wikidata_taxon_id=wikidata_taxon_id,
                historical_character=token,
                is_verified_in_corpus=False
            )
            results.append(model)

        return results

async def main():
    client = WikidataSPARQLClient()
    tokens = await client.fetch_historical_tokens("Turmeric")
    for token in tokens:
        print(token.model_dump_json(indent=2))

if __name__ == "__main__":
    asyncio.run(main())
