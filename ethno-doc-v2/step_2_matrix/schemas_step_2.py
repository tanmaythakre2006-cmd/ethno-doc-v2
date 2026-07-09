from pydantic import BaseModel, ConfigDict, Field

class ExtractedClaim(BaseModel):
    """
    Pydantic V2 schema for storing claims extracted from ancient texts.
    Configured as a frozen model to ensure immutability once created.
    """
    model_config = ConfigDict(frozen=True)

    english_name: str = Field(..., description="English name of the target entity")
    taxon_id: str = Field(..., description="Taxon ID of the entity")
    character_token: str = Field(..., description="The original Chinese character token")
    source_book: str = Field(..., description="The filename of the .txt book")
    chapter_metadata: str = Field(..., description="The nearest preceding chapter heading")
    extracted_context: str = Field(..., description="The raw text paragraph containing the token and its surrounding sentences")
    context_hash: str = Field(..., description="A SHA-256 cryptographic hash of extracted_context + taxon_id")
    confidence_score: int = Field(..., description="The confidence score of the source book")
