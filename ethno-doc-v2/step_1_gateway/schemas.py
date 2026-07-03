from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator

class ChronologicalToken(BaseModel):
    """
    Validates the incoming multi-era character data harvested from historical records
    before any filtering occurs.
    """
    model_config = ConfigDict(frozen=True)

    generic_english_name: str = Field(
        ...,
        description='The initial search string (e.g., "Turmeric").'
    )
    wikidata_taxon_id: str = Field(
        ...,
        description='The exact biological identifier (e.g., "Q425648"). Must match regex pattern ^Q\\d+$.',
        pattern=r'^Q\d+$'
    )
    historical_character: str = Field(
        ...,
        description='A single specific multi-character or single-character token found in historical records (e.g., "薑黃").'
    )
    is_verified_in_corpus: bool = Field(
        default=False,
        description='Tracks whether the token passed the forward-pass lookahead filter in the local text corpus.'
    )
    # PATCHED: Single-Character Risk Mitigation
    is_single_character_risk: bool = Field(
        default=False,
        description="Flags if the historical alias is highly generic (1 character long)"
    )

    # PATCHED: Single-Character Risk Mitigation
    @model_validator(mode='after')
    def check_single_character_risk(self):
        if len(self.historical_character) == 1:
            object.__setattr__(self, 'is_single_character_risk', True)
        return self

    @field_validator('generic_english_name')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip trailing and leading whitespace from the generic English name."""
        return v.strip()
