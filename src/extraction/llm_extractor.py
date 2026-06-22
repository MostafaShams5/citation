import logging
import httpx
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from src.schemas import CitationMetadata

logger = logging.getLogger(__name__)

# 1. Initialize the Agent to output our final schema
model = OpenAIModel('phi3', base_url='http://localhost:11434/v1', api_key='local-ollama')

agent = Agent(
    model,
    result_type=CitationMetadata,
    system_prompt=(
        "You are an academic data extraction assistant. "
        "First, use the 'search_crossref_by_title' tool to search for the document's verified metadata. "
        "If the search tool returns a match, use that perfect data to fill out the final schema. "
        "If the search tool returns nothing, do your best to extract the fields directly from the raw text provided. "
        "Output the final structured metadata."
    )
)

# 2. Give the agent a tool to find more info
@agent.tool
def search_crossref_by_title(ctx: RunContext, title: str, author_last_name: str = "") -> str:
    """
    Use this tool to search the CrossRef registry for a paper by its title and author.
    It returns verified metadata if found.
    """
    logger.info(f"LLM decided to search CrossRef for title: '{title}'")
    query = f"{title} {author_last_name}".strip()
    url = f"https://api.crossref.org/works?query.title={query}&rows=1"
    
    try:
        with httpx.Client() as client:
            response = client.get(url, timeout=5.0)
            if response.status_code == 200:
                items = response.json().get('message', {}).get('items', [])
                if items:
                    # Return the top match to the LLM so it can read it
                    return str(items[0])
        return "No results found in CrossRef."
    except Exception as e:
        return f"Search failed: {str(e)}"

class LLMExtractor:
    def extract(self, raw_text: str) -> CitationMetadata:
        truncated_text = raw_text[:3000]
        logger.info("Executing Agent Workflow...")
        
        # The agent will independently decide to call search_crossref_by_title first, 
        # read the result, and then output the CitationMetadata.
        result = agent.run_sync(f"Document text:\n{truncated_text}")
        
        return result.data
