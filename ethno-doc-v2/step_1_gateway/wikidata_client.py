import asyncio
import random
import sys
import httpx

from step_1_gateway.schemas import ChronologicalToken

class WikidataRateLimitException(Exception):
    pass

class WikidataSPARQLClient:
    def __init__(self):
        self.endpoint_url = "https://query.wikidata.org/sparql"
        self.headers = {
            "User-Agent": "EthnoDocBot/2.0 (mailto:infrastructure-admin@ethnodoc.internal) httpx/asyncio",
            "Accept": "application/sparql-results+json"
        }
        self.timeout = httpx.Timeout(30.0, connect=15.0)

    async def fetch_historical_tokens(self, english_name: str) -> list[ChronologicalToken]:
        query = f"""
        SELECT DISTINCT ?taxon ?zhToken ?priority WHERE {{
          {{
            SELECT ?taxon (MAX(?score) AS ?priority) WHERE {{
              ?taxon rdfs:label|skos:altLabel ?name_en.
              FILTER(LCASE(STR(?name_en)) = "{english_name.lower()}")
              FILTER(LANG(?name_en) = "en")

              ?taxon wdt:P31/wdt:P279* wd:Q16521.

              OPTIONAL {{
                ?taxon wdt:P2283 wd:Q200253.
                BIND(2 AS ?tcm_score)
              }}
              OPTIONAL {{
                ?taxon wdt:P3034 ?range.
                VALUES ?range {{ wd:Q148 wd:Q27231 wd:Q865 }}
                BIND(1 AS ?range_score)
              }}
              BIND(COALESCE(?tcm_score, 0) + COALESCE(?range_score, 0) AS ?score)
            }}
            GROUP BY ?taxon
          }}
          ?taxon rdfs:label|skos:altLabel ?zhToken.
          FILTER(LANG(?zhToken) IN ("zh", "zh-hans", "zh-hant", "zh-cn", "zh-tw", "zh-hk"))
        }}
        ORDER BY DESC(?priority)
        """

        async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
            for attempt in range(5):
                try:
                    response = await client.get(self.endpoint_url, params={"query": query})

                    if response.status_code in (429, 503):
                        delay = (2 ** attempt) + random.uniform(0.5, 1.5)
                        print(f"Warning: Rate limited ({response.status_code}). Retrying in {delay:.2f}s...", file=sys.stderr)
                        await asyncio.sleep(delay)
                        continue

                    response.raise_for_status()

                    data = response.json()
                    bindings = data.get("results", {}).get("bindings", [])

                    if not bindings:
                        return []

                    # Deduplication and target selection
                    target_taxon_uri = bindings[0]["taxon"]["value"]
                    target_taxon_id = target_taxon_uri.split("/")[-1]

                    unique_zh_tokens = set()
                    tokens = []

                    for binding in bindings:
                        taxon_uri = binding["taxon"]["value"]
                        if taxon_uri != target_taxon_uri:
                            continue

                        zh_token = binding["zhToken"]["value"]

                        if zh_token not in unique_zh_tokens:
                            unique_zh_tokens.add(zh_token)
                            tokens.append(
                                ChronologicalToken(
                                    generic_english_name=english_name,
                                    wikidata_taxon_id=target_taxon_id,
                                    historical_character=zh_token
                                )
                            )

                    return tokens

                except httpx.HTTPStatusError as e:
                    if e.response.status_code not in (429, 503):
                        raise

            raise WikidataRateLimitException("Max retry attempts reached due to rate limiting or service unavailability.")

if __name__ == "__main__":
    async def main():
        client = WikidataSPARQLClient()
        tokens = await client.fetch_historical_tokens("Turmeric")
        for token in tokens:
            print(token.model_dump_json(indent=2))

    asyncio.run(main())
