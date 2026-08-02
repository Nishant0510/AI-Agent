// sources.js — wires the source panel to GET /sources and the health badge to GET /health
// /sources response contract: { "documents": [{document, num_chunks, last_ingested_at}] }
// /health response contract: { "status": str, "vector_db_ready": bool }

(() => {
    const sourcesPanel = document.getElementById("sources-panel");
    const refreshBtn = document.getElementById("refresh-sources-btn");
    const healthIndicator = document.getElementById("health-indicator");

    function renderEmptyState() {
        sourcesPanel.innerHTML = `
            <p class="text-muted mb-0">
                No documents indexed yet. Upload a Philips product manual to get started.
            </p>
        `;
    }

    function renderSources(documents) {
        sourcesPanel.innerHTML = "";
        documents.forEach((doc) => {
            const card = document.createElement("div");
            card.className = "source-doc-card";

            const title = document.createElement("div");
            title.innerHTML = `<strong>${escapeHtml(doc.document)}</strong>`;
            card.appendChild(title);

            const meta = document.createElement("div");
            meta.className = "text-muted small";
            const chunkText = `${doc.num_chunks} chunk${doc.num_chunks === 1 ? "" : "s"}`;
            const ingestedText = doc.last_ingested_at
                ? new Date(doc.last_ingested_at).toLocaleString()
                : "unknown";
            meta.textContent = `${chunkText} · last ingested ${ingestedText}`;
            card.appendChild(meta);

            sourcesPanel.appendChild(card);
        });
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    async function loadSources() {
        sourcesPanel.innerHTML = '<p class="text-muted mb-0">Loading sources…</p>';
        try {
            const resp = await fetch("/sources");
            if (!resp.ok) {
                sourcesPanel.innerHTML = '<p class="text-danger mb-0">Could not load sources.</p>';
                return;
            }
            const data = await resp.json();
            const documents = data.documents || [];
            if (documents.length === 0) {
                renderEmptyState();
            } else {
                renderSources(documents);
            }
        } catch (err) {
            console.error("Error calling /sources", err);
            sourcesPanel.innerHTML = '<p class="text-danger mb-0">Could not load sources.</p>';
        }
    }

    async function loadHealth() {
        try {
            const resp = await fetch("/health");
            if (!resp.ok) {
                healthIndicator.textContent = "unreachable";
                healthIndicator.className = "badge bg-danger";
                return;
            }
            const data = await resp.json();
            if (data.vector_db_ready) {
                healthIndicator.textContent = "index ready";
                healthIndicator.className = "badge bg-success";
            } else {
                healthIndicator.textContent = "no index yet";
                healthIndicator.className = "badge bg-warning text-dark";
            }
        } catch (err) {
            console.error("Error calling /health", err);
            healthIndicator.textContent = "unreachable";
            healthIndicator.className = "badge bg-danger";
        }
    }

    refreshBtn.addEventListener("click", loadSources);

    document.addEventListener("DOMContentLoaded", () => {
        loadSources();
        loadHealth();
    });
    if (document.readyState !== "loading") {
        loadSources();
        loadHealth();
    }
})();