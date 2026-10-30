import re
from datetime import datetime


def create_final_report_metadata(final_report: str, transcript_file_name: str) -> dict:
    final_report_metadata = {}

    splitted_file_name = transcript_file_name.split("_")

    # transcript file names ends with a _tanscript
    # change the _tanscript word to _summarized
    final_report_metadata["summary_file_name"] = (
        "_".join(splitted_file_name[:-1]) + "_summarized.md"
    )
    final_report_metadata["final_report"] = final_report
    final_report_metadata["char_count"] = len(final_report)
    final_report_metadata["word_count"] = len(final_report.split())
    final_report_metadata["summary_preview"] = final_report[:490]

    return final_report_metadata


def parse_ollama_ts(s: str | None) -> datetime | None:
    """
    Helper func to format date
    From this: 2026-10-12T13:25:54.186469944Z
    """
    if not s:
        return None
    s = re.sub(r"(\.\d{6})\d+", r"\1", s)  # trim nanoseconds to microseconds
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def create_response_metadata(response) -> dict:
    """
    By default time is given in nanoseconds.
    So making them more readable (will be displayed in seconds)
    and won't have to use in postgres BigIntiger
    """
    tokens_per_second = response["eval_count"] / (
        response["eval_duration"] / 1_000_000_000
    )
    eval_duration = response["eval_duration"] / 1_000_000_000

    prompt_eval_duration = response["prompt_eval_duration"] / 1_000_000_000

    load_duration = response["load_duration"] / 1_000_000_000

    total_duration = response["total_duration"] / 1_000_000_000
    return {
        "model": response["model"],
        "created_at": parse_ollama_ts(response["created_at"]),
        "eval_count": response["eval_count"],
        "eval_duration": round(eval_duration, 2),
        "tokens_per_second": round(tokens_per_second, 2),
        "prompt_eval_count": response["prompt_eval_count"],
        "prompt_eval_duration": round(prompt_eval_duration, 2),
        "load_duration": round(load_duration, 2),
        "total_duration": round(total_duration, 2),
    }


def create_stock_metadata(
    response,
    stock_name: str,
    synthesis_user_template: str,
    synthesis_system_template: str,
) -> dict:

    stock_summary = response["response"]

    llm_stock_metadata = create_response_metadata(response)
    llm_stock_metadata["stock_name"] = stock_name
    llm_stock_metadata["user_prompt_used"] = synthesis_user_template
    llm_stock_metadata["system_prompt_used"] = synthesis_system_template
    llm_stock_metadata["stock_full_text"] = stock_summary
    llm_stock_metadata["char_count"] = len(stock_summary)
    llm_stock_metadata["word_count"] = len(stock_summary.split())

    return llm_stock_metadata
