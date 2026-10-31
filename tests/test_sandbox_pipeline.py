from unittest.mock import patch

from sandbox_pipeline import Pipeline, PipelineConfig, Stage, stage_chunk, stage_report

example_chunk = {
    "id": 4,
    "text": "can integrate AVs into their network and they'll always have demand. They'll always have that network density. Waymo has to earn that every city that they go into. And this essentially means that Uber can be late to the game with AVs and still be in the lead. Even if they introduce AVs and that technology into their fleet in 4 years they still will be the ones that have the lead in it. And that is because of network density across the globe. With the way Uber's being priced for this massive disruption I believe it represents another opportunity. We have Uber here as a position that I've recently started buying into. I've purchased $24,000 worth. We have around $1,500 of gain so far. So it is a small position but it's a growing position. And of course there's no guarantees with any of this. Uber may in fact get disrupted. Maybe the stock goes to zero. And that's why we invest in more than one company. But with Uber I believe it's worth the risk. I believe that this is another company with a very high likelihood that three or four years down the road Uber will be trading at 150 160. Could be even higher at that point and investors will think \"Wow I wish I could have bought that stock when it was $70 per share.\" But today you can. The sentiment is bearish the fundamentals are strong the AV risk is being fully priced into the company and there's a strong chance it may not be nearly as bad as it looks today. Now the next obvious example is Meta. This is a stock that clearly investors are concerned about. The stock has been weathering through little bumps in the road over and over again this entire year. It's down 8%. We look over the past year it's down 21%. And there's a couple bear cases with Meta. The smaller of the bear cases is that Meta faces legal risk. There are some lawsuits and some challenges that Meta's product is unhealthy for kids. Meta is going to settle these cases they're going to make greater restrictions on their app. They'll make kids accounts have all sorts of different controls. That'll be an adaptation of the product for Meta and that will be some legal fees along the way. And we've seen them pay those legal fees just in the past quarter and they'll probably pay some for the next year. So one part of the bear case is the legal fees but I don't believe that's a big part of it. I don't think that's what most investors in Meta are really worried about. Investors are really worried about the enormous amount of capex spend what it's doing to the fundamentals of the company spending all of this money on capital expenditures on servers equipment chips on training models when they don't have any way to directly monetize it with a hyperscaler-like business. They're not leasing out compute capacity like so many others are jumping to. Meta has ways to indirectly monetize it through improving their product and that's the bull case that many people highlight but I don't believe that's the best bull case. When we look at what Mark Zuckerberg is doing he recently just today published a super in-depth very long essay on his belief of the future of AI and how it will affect everyone. Mark Zuckerberg's primary concern with investing this much money into AI is simply to be not reliant or bottlenecked by other companies. He does not want to be in a position where he has to license or use the AI that someone else built. Now why would Mark Zuckerberg want to avoid that path? Because when you're using someone else's product they can",
    "metadata": {"char_count": 3491, "word_count": 638, "sentence_count": 41},
}


def test_pipeline_runner_passes_state_correctly():
    """Verifies that the Pipeline class runs stages sequentially and populates ctx."""

    def fake_stage_1(ctx, cfg):
        return "result_1"

    def fake_stage_2(ctx, cfg):
        # Verify stage 2 can see the results of stage 1!
        assert ctx["first_stage"] == "result_1"
        return "result_2"

    pipeline = Pipeline(
        [Stage("first_stage", fake_stage_1), Stage("second_stage", fake_stage_2)]
    )
    cfg = PipelineConfig(filename="dummy.txt")

    final_context = pipeline.run(cfg)

    assert final_context["first_stage"] == "result_1"
    assert final_context["second_stage"] == "result_2"


@patch("sandbox_pipeline.text_chunker")
def test_stage_chunk_extracts_from_context(mock_text_chunker):
    """Verifies that stage_chunk correctly navigates the nested ctx dictionary."""
    mock_text_chunker.return_value = [{"id": 0, "text": "chunked text"}]

    fake_ctx = {
        "fetch_transcript": {"transcript_text": "This is a raw transcript sentence."}
    }
    cfg = PipelineConfig(filename="dummy.txt", chunk_size=100, chunk_overlap=10)

    result = stage_chunk(fake_ctx, cfg)

    assert result == [{"id": 0, "text": "chunked text"}]
    mock_text_chunker.assert_called_once_with(
        raw_transcript="This is a raw transcript sentence.",
        max_chunk_size=100,
        chunk_overlap=10,
    )


@patch("sandbox_pipeline.generate_stock_report")
def test_stage_report_formatting(mock_generate_report):
    """Verifies that stage_report loops over aggregated data and builds markdown."""
    mock_generate_report.return_value = {"stock_full_text": "NVIDIA is growing fast."}

    fake_ctx = {"aggregate": {"NVDA": {"some": "data"}}}
    cfg = PipelineConfig(filename="dummy.txt")

    markdown_report = stage_report(fake_ctx, cfg)

    assert "# Stock Analysis Report" in markdown_report
    assert "NVDA" in markdown_report
    assert "NVIDIA is growing fast." in markdown_report
    mock_generate_report.assert_called_once_with("NVDA", {"some": "data"})
