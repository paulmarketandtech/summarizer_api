import json
import os
from collections import defaultdict
from pathlib import Path

import yaml
from dotenv import load_dotenv

from app.services import llm_client

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


ollama_host = os.getenv("OLLAMA_HOST")
llm = llm_client.OllamaClient(ollama_host)


def extract_facts_from_chunk(chunk: str):
    config = prompts["extract_data_to_json"]
    system_prompt = config["system"]
    user_prompt = config["user"]

    prompt = user_prompt.format(chunk_text=chunk)
    response = llm.generate(
        user_prompt=prompt, system_prompt=system_prompt, json_mode=True
    )

    # llm_chunk_metadata = create_response_metadata(response)
    # llm_chunk_metadata["user_prompt"] = prompt
    # llm_chunk_metadata["system_prompt"] = system_prompt

    raw_response = response["response"]  # pyright: ignore
    try:
        data = json.loads(raw_response)
        if isinstance(data, list):
            return data  # , llm_chunk_metadata
        elif isinstance(data, dict):
            # In case the model returns {"stocks": [...]} instead of direct list
            print("*" * 40)
            __import__("pprint").pprint(data.get("stocks", [data]))
            # print(data.get("stocks", [data]))
            print("=" * 40)
            return data.get("stocks", [data])  # , llm_chunk_metadata
    except json.JSONDecodeError:
        print("Failed to parse JSON, skipping chunk.")
        return []
    return []
