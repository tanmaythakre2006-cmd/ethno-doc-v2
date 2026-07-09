from pydantic import BaseModel, ConfigDict, Field

class TaxonomicProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    context_hash: str = Field(description="The exact SHA-256 hash from Step 2")
    original_english_name: str = Field(description="The name passed from Step 2")
    gbif_usage_key: int = Field(description="The canonical integer ID returned by GBIF")
    accepted_scientific_name: str = Field(description="The official Latin binomial (e.g., 'Curcuma longa L.')")
    taxonomic_rank: str = Field(description="The biological rank (e.g., 'SPECIES', 'SUBSPECIES', 'VARIETY')")
    is_subspecies_match: bool = Field(default=False, description="Defaults to False. Will be used later if a regional variant is identified")
