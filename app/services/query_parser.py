import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from app.schemas.parse_rag_query import ParsedRagQuery
from app.services.llm_client import OllamaClient
from app.services.rag_date_conventer import quarter_to_date_range

load_dotenv()
prompts_file = os.getenv("PROMPTS_FILE_PATH")
if not prompts_file:
    raise RuntimeError(
        "Environment variable PROMPTS_FILE_PATH is not set. "
        "Please set it to the path of your prompts YAML file."
    )

prompts_path = Path(prompts_file)
with prompts_path.open("r", encoding="utf-8") as f:
    prompts = yaml.safe_load(f)

config = prompts["query_parser_system_prompt"]
system_prompt = config["system"]


class QueryParser:
    def __init__(self, ollama_host: str):
        self.client = OllamaClient(ollama_host)

    def parse(self, user_query: str, system_prompt: str) -> ParsedRagQuery:
        response = self.client.generate(
            user_prompt=user_query,
            system_prompt=system_prompt,
            temperature=0.0,
            top_p=0.9,
            top_k=40,
            json_mode=ParsedRagQuery.model_json_schema(),
        )

        raw_json = response["response"]

        return ParsedRagQuery.model_validate_json(raw_json)


ollama_host = os.getenv("OLLAMA_HOST")
parser = QueryParser(ollama_host=ollama_host)

"""
parsed = parser.parse(
    "What concerns did people have about inflation and interest rates in Q4 2023?"
)
"""
parsed = parser.parse(
    "What did people say about Nvidia earnings in Q1 2025?", system_prompt
)
print(parsed)
