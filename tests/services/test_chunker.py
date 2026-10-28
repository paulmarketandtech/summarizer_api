import pytest

from app.services.lang_chunker import text_chunker


@pytest.fixture
def sample_transcript():
    return "Over this recent earnings season, we've seen stocks do particularly well. In fact, many of them have surged to all-time highs. The index, the S&P 500, is near its all-time high, and the QQQ is near its all-time high. With all this momentum in stocks, you may believe that there's no longer any good deals, that every stock has raced up and you missed the train. Well, I believe that that's wrong. There's still a couple of them, a select few, that represent tremendous value today, that are being misunderstood by the market, and they will have their day in the market."


def test_chunker(sample_transcript):
    chunks = text_chunker(
        raw_transcript=sample_transcript, max_chunk_size=100, chunk_overlap=20
    )
    assert isinstance(chunks, list)


def test_chunker_metadata_is_accurate(sample_transcript):
    chunks = text_chunker(
        raw_transcript=sample_transcript, max_chunk_size=100, chunk_overlap=20
    )
    assert len(chunks) > 0

    first_chunk = chunks[0]

    assert "id" in first_chunk
    assert "text" in first_chunk
    assert "metadata" in first_chunk

    metadata = first_chunk["metadata"]
    actual_text = first_chunk["text"]

    assert first_chunk["id"] == 0
    assert isinstance(actual_text, str)
    assert metadata["char_count"] == len(actual_text)
    assert metadata["word_count"] == len(actual_text.split())
    assert metadata["sentence_count"] == len(actual_text.split("."))


def test_chunker_respects_max_size(sample_transcript):
    max_size = 50
    chunks = text_chunker(sample_transcript, max_chunk_size=max_size, chunk_overlap=10)

    for chunk in chunks:
        assert chunk["metadata"]["char_count"] <= max_size


def test_chunker_creates_overlap():
    text = "ABCDEFGHIJ"  # 10 characters

    chunks = text_chunker(text, max_chunk_size=6, chunk_overlap=3)

    assert len(chunks) >= 2
    chunk_1_text = chunks[0]["text"]
    chunk_2_text = chunks[1]["text"]

    shared_chars = set(chunk_1_text).intersection(set(chunk_2_text))
    print("+" * 70)
    print(shared_chars)

    assert len(shared_chars) >= 1
