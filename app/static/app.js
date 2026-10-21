// ─── Toggle summary cards ──────────────────────────────
async function toggleSummary(videoId) {
    const card = document.querySelector(`.video-card[data-id="${videoId}"]`);
    const summary = document.getElementById(`summary-${videoId}`);
    const contentDiv = summary.querySelector('.summary-content');

    const isOpen = card.classList.toggle('open');

    // Fetch summary content lazily on first open
    if (isOpen && contentDiv.dataset.loaded !== 'true') {
        try {
            const res = await fetch(`/public/vid/${videoId}`);
            if (!res.ok) throw new Error('Failed to load');
            const data = await res.json();
            contentDiv.textContent = data.summary || 'No summary available.';
            contentDiv.dataset.loaded = 'true';
        } catch (err) {
            contentDiv.textContent = 'Error loading summary.';
        }
    }
}

// ─── Filter form ───────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const applyBtn = document.getElementById('apply-filters');
    const clearBtn = document.getElementById('clear-filters');

    if (applyBtn) applyBtn.addEventListener('click', applyFilters);
    if (clearBtn) clearBtn.addEventListener('click', clearFilters);

    // RAG form
    const ragForm = document.getElementById('rag-form');
    if (ragForm) ragForm.addEventListener('submit', handleRagSearch);
});

async function applyFilters() {
    const params = new URLSearchParams();
    const creator = document.getElementById('creator').value;
    const contentType = document.getElementById('content_type').value;
    const dateFrom = document.getElementById('date_from').value;
    const dateTo = document.getElementById('date_to').value;

    if (creator) params.set('yt_creator', creator);
    if (contentType) params.set('content_type', contentType);
    if (dateFrom) params.set('date_from', dateFrom);
    if (dateTo) params.set('date_to', dateTo);

    const list = document.getElementById('video-list');
    list.innerHTML = '<li class="empty">Loading...</li>';

    try {
        const res = await fetch(`/public/vid?${params.toString()}`);
        const videos = await res.json();
        renderVideos(videos);
    } catch (err) {
        list.innerHTML = '<li class="empty">Error loading videos.</li>';
    }
}

function clearFilters() {
    document.getElementById('creator').value = '';
    document.getElementById('content_type').value = '';
    document.getElementById('date_from').value = '';
    document.getElementById('date_to').value = '';
    applyFilters();
}

function renderVideos(videos) {
    const list = document.getElementById('video-list');
    const count = document.getElementById('count');
    count.textContent = videos.length;

    if (videos.length === 0) {
        list.innerHTML = '<li class="empty">No videos found.</li>';
        return;
    }

    list.innerHTML = videos.map(v => `
        <li class="video-card" data-id="${v.id}">
            <div class="video-header" onclick="toggleSummary('${v.id}')">
                <div class="video-info">
                    <h3 class="video-title">${escapeHtml(v.title || 'Untitled')}</h3>
                    <div class="video-meta">
                        <span class="creator">${escapeHtml(v.yt_creator || 'Unknown')}</span>
                        ${v.content_type ? `<span class="badge">${escapeHtml(v.content_type)}</span>` : ''}
                        ${v.published_date ? `<span class="date">${v.published_date}</span>` : ''}
                    </div>
                    ${v.summary_preview ? `<p class="preview">${escapeHtml(v.summary_preview)}</p>` : ''}
                </div>
                <div class="toggle-icon">▼</div>
            </div>
            <div class="video-summary" id="summary-${v.id}">
                <div class="summary-content">
                    <div class="loading">Loading summary...</div>
                </div>
                <div class="video-actions">
                    <a href="${escapeHtml(v.url)}" target="_blank" rel="noopener" class="btn btn-ghost">Watch on YouTube ↗</a>
                </div>
            </div>
        </li>
    `).join('');
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ─── RAG search ────────────────────────────────────────
async function handleRagSearch(e) {
    e.preventDefault();

    const query = document.getElementById('rag-query').value.trim();
    const resultsDiv = document.getElementById('rag-results');
    const statusSpan = document.getElementById('rag-status');
    const submitBtn = document.getElementById('rag-submit');

    if (!query || query.length < 3) {
        resultsDiv.innerHTML = '<div class="empty">Please enter at least 3 characters.</div>';
        return;
    }

    // Show loading state
    submitBtn.disabled = true;
    submitBtn.textContent = 'Searching...';
    statusSpan.textContent = 'Embedding your query and searching...';
    resultsDiv.innerHTML = '';

    try {
        const res = await fetch('/public/rag', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query }),
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Search failed');
        }

        const results = await res.json();
        statusSpan.textContent = `Found ${results.length} results`;
        renderRagResults(results);

    } catch (err) {
        statusSpan.textContent = '';
        resultsDiv.innerHTML = `<div class="empty">Error: ${escapeHtml(err.message)}</div>`;
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Search';
    }
}

function renderRagResults(results) {
    const resultsDiv = document.getElementById('rag-results');

    if (results.length === 0) {
        resultsDiv.innerHTML = '<div class="empty">No relevant results found.</div>';
        return;
    }

    resultsDiv.innerHTML = results.map((r, i) => `
        <div class="rag-card">
            <div class="rag-card-header">
                <span class="rag-rank">#${i + 1}</span>
                <span class="rag-source badge">${escapeHtml(r.source)}</span>
                <span class="rag-similarity">${(r.similarity * 100).toFixed(1)}% match</span>
            </div>
            <div class="rag-card-body">${escapeHtml(r.text)}</div>
            <div class="rag-card-footer">
                <span class="rag-video-id">Video: ${r.video_id.slice(0, 8)}...</span>
            </div>
        </div>
    `).join('');
}
