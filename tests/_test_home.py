from your_models_module import Video  # Import your SQLAlchemy Video model


def test_home_endpoint_renders_latest_videos(client, db_session):
    # --- 1. ARRANGE ---
    # Create fake video data to populate our in-memory DB
    fake_video = Video(
        title="FastAPI Testing for Beginners",
        youtube_url="https://youtube.com",
        creator="CodeNewbie",
        content_type="Tutorial",
    )
    db_session.add(fake_video)
    db_session.commit()

    # --- 2. ACT ---
    # Call your home route
    response = client.get("/")

    # --- 3. ASSERT ---
    # Check that the page loaded successfully
    assert response.status_code == 200

    # Verify that the response is actually HTML
    assert "text/html" in response.headers["content-type"]

    # Check if the title of our fake video made it into the rendered HTML template
    assert "FastAPI Testing for Beginners" in response.text
    assert "CodeNewbie" in response.text
