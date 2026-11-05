// app/static/admin.js

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("submit-form");
    const statusBox = document.getElementById("status");
    const statusMsg = document.getElementById("status-message");
    const submitBtn = document.getElementById("submit-btn");

    const resultsCard = document.getElementById("results");
    const resultsTitle = document.getElementById("results-title");
    const resultsBadge = document.getElementById("results-badge");
    const resultsMeta = document.getElementById("results-meta");
    const resultsSummary = document.getElementById("results-summary");
    const clearBtn = document.getElementById("clear-btn");


    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const url = document.getElementById("url").value.trim();
        const videoType = document.getElementById("video-type").value;


        submitBtn.disabled = true;
        submitBtn.textContent = "Processing…";
        resultsCard.hidden = true;
        showStatus("Submitting…", "info");

        try {
            const res = await fetch("/admin/videos", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ url, video_type: videoType }),
            });

            const data = await res.json();

            if (!res.ok) {
                if (res.status === 403) {
                    sessionStorage.removeItem("admin_api_key");
                }
                showStatus(data.detail || `Error ${res.status}`, "error");
                return;
            }

            // Hide the status bar, show the results card
            statusBox.hidden = true;
            showResults(data);
            form.reset();

        } catch (err) {
            showStatus(`Network error: ${err.message}`, "error");
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = "Submit";
        }
    });

    clearBtn.addEventListener("click", () => {
        resultsCard.hidden = true;
    });

    function showResults(data) {
        resultsTitle.textContent = data.title;

        // Badge: "Cached" (blue) vs "Processed" (green)
        if (data.status === "cached") {
            resultsBadge.textContent = "Cached";
            resultsBadge.className = "badge badge-cached";
        } else {
            resultsBadge.textContent = "Processed";
            resultsBadge.className = "badge badge-processed";
        }

        // Meta line: type + processing time
        let meta = `Type: ${data.video_type}`;
        if (data.processing_time != null) {
            meta += ` · ${data.processing_time}s`;
        }
        resultsMeta.textContent = meta;

        // Summary text — preserve whitespace/newlines from the LLM output
        resultsSummary.textContent = data.summary;

        resultsCard.hidden = false;
        resultsCard.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    function showStatus(msg, type) {
        statusBox.hidden = false;
        statusMsg.textContent = msg;
        statusBox.className = `status-box ${type}`;
    }
});
