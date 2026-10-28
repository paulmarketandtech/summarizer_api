import re

from langchain_text_splitters import RecursiveCharacterTextSplitter


def clean_transcript(text: str) -> str:
    # 1. Collapse multiple spaces/newlines into a single space
    text = re.sub(r"\s+", " ", text).strip()

    # 2. Remove everything inside square brackets (and the brackets)
    #    Examples: [music]  [Applause]  [inaudible 00:12]  → gone
    text = re.sub(r"\[[^\]]*\]", "", text)

    # 3. Remove repeated single words (stutters): "I I I really" → "I really"
    #    (\w+)   = capture one word
    #    ( \1)+  = one or more repetitions of " space + the same word"
    #    r'\1'   = replace the whole match with just the first captured word
    text = re.sub(r"\b(\w+)( \1\b)+", r"\1", text, flags=re.IGNORECASE)

    # 4 remove all >>
    text = re.sub(r">>", "", text)

    # 5. Remove common fillers (add/remove patterns as you like)
    fillers = [
        r"\bi mean\b",
        r"\byou know\b",
        r"\bum+\b",
        r"\buh+\b",
        r"\ber+\b",
        r"\bah+\b",
        r"\bkind of\b",
        r"\bkinda\b",
        r"\bsort of\b",
        r"\bsorta\b",
        r"\bbasically\b",
        r"\bactually\b",
        r"\bokay\b",
        r"\bok\b",
        r"\byeah\b",
        r"\bsounds good\b",
    ]
    for pattern in fillers:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # 6. Remove common greetings and goodbyes (flexible patterns)
    greetings_goodbyes = [
        # Openings
        r"\b(hey|hi|hello|good morning|good afternoon|good evening) (everyone|everybody|guys|folks|all)?\b",
        r"\bwelcome back\b",
        r"\bthanks for (joining|tuning in|watching)\b",
        r"\bladies and gentlem[ae]n\b",
        # Closings
        r"\b(see you|catch you) (all |guys |folks )?(later|next time|soon|tomorrow)\b",
        r"\b(that\'?s|that is) (it|all) for (today|now|this (one|episode|video))\b",
        r"\b(alright|okay|ok),? (that\'?s|that is) (it|all)\b",
        r"\bthanks for (watching|listening|tuning in)\b",
        r"\buntil next time\b",
        r"\bsee you guys all next time\b",
        r"\btake care\b",
        r"\bbye[\s,]*bye\b",
        r"\bgoodbye\b",
    ]
    for pattern in greetings_goodbyes:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # 7. === FIX LONELY / LEFTOVER PUNCTUATION ===
    #    Remove comma/period/etc. that are now sitting alone at the start
    #    or after another space
    text = re.sub(r"(^|\s)[,:;]+", r"\1", text)  # leading ", insane" → " insane"
    text = re.sub(r"[,:;]+(\s|$)", r"\1", text)  # trailing "earnings ," → "earnings "

    # 8. Clean up spaces around remaining punctuation
    #    "word , word" → "word, word"
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)

    # 9. Collapse multiple punctuation marks: "!!" or ",," → single
    text = re.sub(r"([,.!?;:]){2,}", r"\1", text)

    # 10. Final space cleanup
    text = re.sub(r"\s{2,}", " ", text).strip()

    # with open("cleared_chunks.txt", "a") as file:
    # file.write(text + "\n")
    return text


def text_chunker(
    raw_transcript: str, max_chunk_size: int = 6000, chunk_overlap: int = 600
) -> list[dict]:
    cleaned_transcript = clean_transcript(raw_transcript)
    chunks = []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    texts = text_splitter.split_text(cleaned_transcript)

    for i, chunk in enumerate(texts):
        chunks.append(
            {
                "id": i,
                "text": chunk,
                "metadata": {
                    "char_count": len(chunk),
                    "word_count": len(chunk.split()),
                    "sentence_count": len(chunk.split(".")),
                },
            }
        )

    return chunks
