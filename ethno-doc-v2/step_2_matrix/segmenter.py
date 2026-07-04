import re
import hashlib
from typing import List

class ContextExtractor:
    """
    Highly disciplined NLP Boundary Segmenter for ancient Chinese medical texts.
    Tracks chapters and intelligently segments text blocks by logical boundaries
    to extract contexts surrounding target tokens.
    """

    def __init__(self):
        """
        Initialize the ContextExtractor with a state variable for current_chapter.
        """
        self.current_chapter: str = "UNKNOWN_CHAPTER"
        # Regex for chapter headings (e.g., 卷一, 第一章, etc.)
        self.chapter_pattern = re.compile(r'^(卷[一二三四五六七八九十百千万]+|第[一二三四五六七八九十百千万]+[章回卷])')

    def track_chapter(self, line: str) -> None:
        """
        Evaluates a given line of text. If it matches a typical Chinese chapter/volume
        heading, updates the internal current_chapter state.

        Args:
            line: A single line of text to evaluate.
        """
        match = self.chapter_pattern.search(line.strip())
        if match:
            self.current_chapter = match.group(1)

    def extract_context(self, text_block: str, target_token: str) -> List[str]:
        """
        Extracts discrete boundary-aware sentences containing the target_token,
        and captures surrounding sentences.

        Splits incoming text by [。！？\n], and when the target_token is found,
        captures i-1, i, i+1, and i+2 sentences. Recombines them with periods.

        Args:
            text_block: The raw text paragraph to search within.
            target_token: The Chinese character token to locate.

        Returns:
            A list of extracted contexts (as string paragraphs). Multiple contexts
            could be extracted if the target_token appears in multiple separate
            locations within the text block that do not share the same context boundary.
        """
        # Split text into sentences using Chinese terminal punctuation as delimiters
        # We use re.split with a capture group so we can reconstruct or just split by the delimiters
        # Alternatively, we just split by delimiters and ignore keeping them for simplicity
        # based on the prompt "joins these captured sentences back together with periods (。)."

        raw_sentences = re.split(r'[。！？\n]', text_block)
        # Filter out empty strings
        sentences = [s.strip() for s in raw_sentences if s.strip()]

        extracted_contexts = []

        # Keep track of indices already included in a previous extraction to avoid duplication
        # if the token appears in consecutive sentences. But strictly following the prompt:
        # iterate, find token, capture i-1, i, i+1, i+2.

        # We will iterate and whenever we find the token, we grab the slice.
        for i, sentence in enumerate(sentences):
            if target_token in sentence:
                start_idx = max(0, i - 1)
                end_idx = min(len(sentences), i + 3) # i+3 because slice is exclusive

                captured = sentences[start_idx:end_idx]
                context_str = "。".join(captured) + "。"

                # Check if we should add it (could use a simple deduplication if desired,
                # but the hashing step later will handle true duplicates in DB anyway)
                extracted_contexts.append(context_str)

        return extracted_contexts

    def generate_sha256(self, text: str, taxon_id: str) -> str:
        """
        Generates a SHA-256 cryptographic hash of the extracted context and taxon_id
        to guarantee global uniqueness in the database.

        Args:
            text: The extracted context text.
            taxon_id: The taxon ID associated with the claim.

        Returns:
            A hexadecimal SHA-256 string representing the hash.
        """
        hash_input = f"{text}{taxon_id}".encode('utf-8')
        return hashlib.sha256(hash_input).hexdigest()
