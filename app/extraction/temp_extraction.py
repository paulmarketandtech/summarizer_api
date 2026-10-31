import json
import os
from collections import defaultdict
from pathlib import Path

import yaml
from dotenv import load_dotenv

from app.services import llm_client
from app.utils.create_report_metadata import (
    create_response_metadata,
    create_stock_metadata,
)

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


def extract_facts_from_chunk(chunk: str) -> tuple[dict, dict]:
    config = prompts["extract_data_to_json"]
    system_prompt = config["system"]
    user_prompt = config["user"]

    prompt = user_prompt.format(chunk_text=chunk)
    response = llm.generate(
        user_prompt=prompt, system_prompt=system_prompt, json_mode=True
    )

    llm_chunk_metadata = create_response_metadata(response)
    llm_chunk_metadata["user_prompt"] = prompt
    llm_chunk_metadata["system_prompt"] = system_prompt

    raw_response = response["response"]  # pyright: ignore
    try:
        data = json.loads(raw_response)
        if isinstance(data, list):
            return data, llm_chunk_metadata
        elif isinstance(data, dict):
            # In case the model returns {"stocks": [...]} instead of direct list
            print("*" * 40)
            __import__("pprint").pprint(data.get("stocks", data))
            print("=" * 40)
            return data.get("stocks", [data]), llm_chunk_metadata

    except json.JSONDecodeError:
        print("Failed to parse JSON, skipping chunk.")
        return []
    return []


def aggregate_extracted_data(
    all_chunk_extractions: list,
) -> dict:
    """Combines extracted JSON pieces into a unified dictionary by Stock Name."""
    grouped_stocks = defaultdict(
        lambda: {
            "kpis_mentioned": [],
            "bull_thesis": [],
            "bear_thesis": [],
            "strengths": [],
            "weaknesses": [],
            "catalysts": [],
        }
    )
    for chunk_data in all_chunk_extractions:
        for item in chunk_data:
            name = item.get("company_name", "").strip().upper()
            if not name or len(name) < 2:
                continue

            # Append raw extracted facts
            for key in [
                "kpis_mentioned",
                "bull_thesis",
                "bear_thesis",
                "strengths",
                "weaknesses",
                "catalysts",
            ]:
                if key in item and isinstance(item[key], list):
                    grouped_stocks[name][key].extend(item[key])

    return grouped_stocks


def generate_stock_report(stock_name: str, stock_data: dict) -> dict:
    config = prompts["synthesis_json_data"]
    synthesis_system_template = config["system"]
    synthesis_user_template = config["user"]

    prompt = synthesis_user_template.format(
        stock_name=stock_name,
        kpis_mentioned=json.dumps(stock_data["kpis_mentioned"]),
        bull_thesis=json.dumps(stock_data["bull_thesis"]),
        bear_thesis=json.dumps(stock_data["bear_thesis"]),
        strengths=json.dumps(stock_data["strengths"]),
        weaknesses=json.dumps(stock_data["weaknesses"]),
        catalysts=json.dumps(stock_data["catalysts"]),
    )

    response = llm.generate(
        user_prompt=prompt, system_prompt=synthesis_system_template, json_mode=False
    )

    llm_stock_metadata = create_stock_metadata(
        response, stock_name, synthesis_user_template, synthesis_system_template
    )

    return llm_stock_metadata
