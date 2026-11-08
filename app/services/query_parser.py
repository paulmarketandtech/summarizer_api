import os

from dotenv import load_dotenv

from app.schemas.parse_rag_query import ParsedRagQuery
from app.services.llm_client import OllamaClient
from app.services.rag_date_conventer import quarter_to_date_range

load_dotenv()


QUERY_PARSER_SYSTEM_PROMPT = """
You extract search fields from a user's question about indexed YouTube videos.

You do NOT answer the question.
You only return valid JSON matching the supplied schema.

A query is market-related when it concerns:
- stocks, companies, earnings, valuation, dividends, investing
- stock market, sectors, market sentiment
- macroeconomics relevant to markets, including inflation, interest rates,
  central banks, recession, GDP, employment, bond yields, liquidity

A query is unrelated when it asks about topics such as recipes, sports,
travel, programming, entertainment, weather, or general knowledge that is
not about markets, companies, or macroeconomics.

Rules:
- Do not invent company names, dates, financial facts, or topics.
- Use an empty companies list when the query is macroeconomic or broad market
  related and has no company.
- Normalize well-known company names consistently, for example:
  NVIDIA, Microsoft, Apple, Tesla.
- embedding_query must be a concise search phrase, not an answer.
- Preserve meaningful terms such as risks, threats, earnings, valuation,
  competition, inflation, interest rates, and recession.

Time rules:
- video_year and video_quarter are for the publication/discussion period
  of the source videos.
- Fill video_year and video_quarter when the user asks what people were
  saying in a time period, or asks for videos from a time period.

- mentioned_year and mentioned_quarter are for the subject being discussed.
- For "Nvidia earnings in Q1 2025", Q1 2025 is a mentioned period,
  not automatically a source-video publication filter.
- A question can have both a video period and a mentioned period.
- If there is no clear quarter/year, leave the relevant fields null.
"""


class QueryParser:
    def __init__(self, ollama_host: str):
        self.client = OllamaClient(ollama_host)

    def parse(self, user_query: str) -> ParsedRagQuery:
        response = self.client.generate(
            user_prompt=user_query,
            system_prompt=QUERY_PARSER_SYSTEM_PROMPT,
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
parsed = parser.parse("What did people say about Nvidia earnings in Q1 2025?")
print(parsed)
"""
