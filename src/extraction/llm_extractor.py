import json
import logging
import re
from typing import Optional
from src.schemas import CitationMetadata, Author

logger = logging.getLogger(__name__)

class LLMExtractor:
    """
    Fallback extraction engine using a local Hugging Face model.
    Designed to run on Kaggle/Colab GPUs.
    """
    def __init__(self, model_id: str = "microsoft/Phi-3-mini-4k-instruct"):
        logger.info(f"Initializing LLMExtractor with model: {model_id}")
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id, 
            torch_dtype=torch.bfloat16, 
            device_map="auto", 
            trust_remote_code=True
        )
        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
        )

    def _clean_json_output(self, raw_output: str) -> dict:
        """Extracts JSON from the LLM's raw text output using regex."""
        # Find everything between the first { and the last }
        match = re.search(r'\{.*\}', raw_output, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError as e:
                logger.error(f"LLM produced invalid JSON: {e}")
                raise
        raise ValueError("No JSON object found in LLM output.")

    def extract(self, raw_text: str) -> CitationMetadata:
        """Passes the document text to the LLM and maps the result to CitationMetadata."""
        
        # Truncate text to avoid exceeding the context window.
        # The first 3000 chars (approx 1-2 pages) usually contain all necessary metadata.
        truncated_text = raw_text[:3000]

        prompt = f"""<|user|>
You are an academic data extraction assistant. I will provide the beginning text of a document. 
Extract the citation metadata and output ONLY a valid JSON object. Do not include any markdown formatting, explanations, or extra text.

The JSON must have EXACTLY these keys:
- "title" (string or null)
- "authors" (list of objects with "family_name" and "given_name" or empty list)
- "publication_year" (integer or null)
- "publisher" (string or null)
- "container_title" (string, the journal or book name, or null)
- "volume" (string or null)
- "issue" (string or null)
- "pages" (string or null)

Document Text:
{truncated_text}
<|end|>
<|assistant|>
"""
        
        logger.info("Sending document to LLM for extraction...")
        
        # Generation configuration optimized for Phi-3 JSON extraction
        generation_args = {
            "max_new_tokens": 500,
            "return_full_text": False,
            "temperature": 0.1,  # Low temperature for deterministic factual extraction
            "do_sample": True,
        }

        output = self.pipe(prompt, **generation_args)
        generated_text = output[0]['generated_text']
        
        logger.info("LLM extraction complete. Parsing JSON...")
        data = self._clean_json_output(generated_text)
        
        # Map raw dictionary to our validated Pydantic model
        authors_list = [Author(**a) for a in data.get('authors', [])]
        
        return CitationMetadata(
            title=data.get('title', 'Unknown Title'),
            authors=authors_list,
            publication_year=data.get('publication_year'),
            publisher=data.get('publisher'),
            container_title=data.get('container_title'),
            volume=data.get('volume'),
            issue=data.get('issue'),
            pages=data.get('pages'),
            doi=None # If LLM is triggered, we already know DOI wasn't found
        )
