// chat.js — wires the chat window to POST /ask
// Response contract (must match app/models/schemas.py::AskResponse exactly):
// { "answer": str, "confidence_score": float, "sources": [{document, page, chunk_id, similarity_score}] }

(() => {
    const HISTORY_KEY = "philips_agent_chat_history_v1";
    // Mirrors app/utils/config.py SIMILARITY_THRESHOLD. If that value changes
    // server-side, update this constant too — the frontend has no endpoint to
    // read it from yet.
    const CONFIDENCE_THRESHOLD = 0.50;

    const chatWindow = document.getElementById("chat-window");
    const askForm = document.getElementById("ask-form");
    const questionInput = document.getElementById("question-input");
    const askSubmitBtn = document.getElementById("ask-submit-btn");
    const clearHistoryBtn = document.getElementById("clear-history-btn");
    const serviceBanner = document.getElementById("service-banner");
    const serviceBannerClose = document.getElementById("service-banner-close");

    function loadHistory() {
        try {
            const raw = localStorage.getItem(HISTORY_KEY);
            return raw ? JSON.parse(raw) : [];
        } catch (e) {
            console.warn("Could not parse chat history from localStorage", e);
            return [];
        }
    }

    function saveHistory(history) {
        try {
            localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
        } catch (e) {
            console.warn("Could not persist chat history to localStorage", e);
        }
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    function renderUserBubble(question) {
        const bubble = document.createElement("div");
        bubble.className = "chat-bubble user";
        bubble.textContent = question;
        chatWindow.appendChild(bubble);
    }

    function renderAssistantBubble(entry) {
        const { answer, confidence_score, sources, reason } = entry;
        const passed = !reason;

        const bubble = document.createElement("div");
        bubble.className = "chat-bubble assistant" + (passed ? "" : " refused");

        const badge = document.createElement("span");
        badge.className = "confidence-badge " + (passed ? "pass" : "refuse");

        const scoreText = confidence_score != null
            ? " · " + (confidence_score * 100).toFixed(0) + "%"
            : "";

        if (passed) {
            badge.textContent = "Grounded" + scoreText;
        } else {
            const reasonLabel = {
                blocked: "Blocked",
                no_documents: "No documents",
                low_confidence: "Low confidence",
            }[reason] || "Refused";
            badge.textContent = reasonLabel + scoreText;
        }
        bubble.appendChild(badge);

        const answerP = document.createElement("div");
        answerP.textContent = answer || "";
        bubble.appendChild(answerP);

        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement("div");
            sourcesDiv.className = "bubble-sources";
            const label = document.createElement("div");
            label.innerHTML = "<strong>Sources</strong>";
            sourcesDiv.appendChild(label);

            const ul = document.createElement("ul");
            sources.forEach((s) => {
                const li = document.createElement("li");
                li.textContent = `${s.document} — page ${s.page} (similarity ${(s.similarity_score * 100).toFixed(0)}%)`;
                ul.appendChild(li);
            });
            sourcesDiv.appendChild(ul);
            bubble.appendChild(sourcesDiv);
        }

        chatWindow.appendChild(bubble);
    }

    function renderTypingIndicator() {
        const el = document.createElement("div");
        el.className = "typing-indicator";
        el.id = "typing-indicator";
        el.textContent = "Thinking…";
        chatWindow.appendChild(el);
        chatWindow.scrollTop = chatWindow.scrollHeight;
        return el;
    }

    function removeTypingIndicator() {
        const el = document.getElementById("typing-indicator");
        if (el) el.remove();
    }

    function scrollToBottom() {
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    function renderAllHistory() {
        chatWindow.innerHTML = "";
        const history = loadHistory();
        history.forEach((turn) => {
            renderUserBubble(turn.question);
            renderAssistantBubble(turn);
        });
        scrollToBottom();
    }

    function showServiceBanner() {
        serviceBanner.classList.remove("d-none");
    }

    function hideServiceBanner() {
        serviceBanner.classList.add("d-none");
    }

    async function askQuestion(question) {
        askSubmitBtn.disabled = true;
        renderUserBubble(question);
        scrollToBottom();
        const typingEl = renderTypingIndicator();

        try {
            const resp = await fetch("/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question }),
            });

            removeTypingIndicator();

            if (resp.status === 503) {
                showServiceBanner();
                // Roll back the optimistic user bubble since we have no answer to pair it with.
                chatWindow.lastElementChild?.remove();
                return;
            }

            if (!resp.ok) {
                const bubble = document.createElement("div");
                bubble.className = "chat-bubble assistant refused";
                bubble.textContent = "Something went wrong answering that question. Please try again.";
                chatWindow.appendChild(bubble);
                scrollToBottom();
                return;
            }

            hideServiceBanner();
            const data = await resp.json();
            const entry = {
                question,
                answer: data.answer,
                confidence_score: data.confidence_score,
                sources: data.sources || [],
            };

            renderAssistantBubble(entry);
            scrollToBottom();

            const history = loadHistory();
            history.push(entry);
            saveHistory(history);
        } catch (err) {
            removeTypingIndicator();
            showServiceBanner();
            chatWindow.lastElementChild?.remove();
            console.error("Error calling /ask", err);
        } finally {
            askSubmitBtn.disabled = false;
        }
    }

    askForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const question = questionInput.value.trim();
        if (!question) return;
        questionInput.value = "";
        askQuestion(question);
    });

    clearHistoryBtn.addEventListener("click", () => {
        localStorage.removeItem(HISTORY_KEY);
        chatWindow.innerHTML = "";
    });

    serviceBannerClose.addEventListener("click", hideServiceBanner);

    document.addEventListener("DOMContentLoaded", renderAllHistory);
    // In case this script runs after DOMContentLoaded already fired.
    if (document.readyState !== "loading") {
        renderAllHistory();
    }
})();