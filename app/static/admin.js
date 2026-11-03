// app/static/admin.js

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("submit-form");
    const statusBox = document.getElementById("status");
    const statusMsg = document.getElementById("status-message");
    const submitBtn = document.getElementById("submit-btn");

    // Prompt once per browser session, then remember
    let apiKey = sessionStorage.getItem("admin_api_key");
    if (!apiKey) {
        apiKey = prompt("Enter admin API key:");
        if (apiKey) {
            sessionStorage.setItem("admin_api_key", apiKey);
        }
    }

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const url = document.getElementById("url").value.trim();
        const videoType = document.getElementById("video-type").value;

        if (!apiKey) {
            showStatus("No API key provided.", "error");
            return;
        }

        submitBtn.disabled = true;
        submitBtn.textContent = "Submitting…";
        showStatus("Sending…", "info");

        try {
            const res = await fetch("/api/admin/videos", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-API-Key": apiKey,
                },
                body: JSON.stringify({ url, video_type: videoType }),
            });

            const data = await res.json();

            if (!res.ok) {
                // If 403, clear the cached key so they get prompted again
                if (res.status === 403) {
                    sessionStorage.removeItem("admin_api_key");
                }
                showStatus(data.detail || `Error: ${res.status}`, "error");
                return;
            }

            showStatus(`Received: ${data.video_type} — ${data.url}`, "success");
            form.reset();
        } catch (err) {
            showStatus(`Network error: ${err.message}`, "error");
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = "Submit";
        }
    });

    function showStatus(msg, type) {
        statusBox.hidden = false;
        statusMsg.textContent = msg;
        statusBox.className = `status-box ${type}`;
    }
});
