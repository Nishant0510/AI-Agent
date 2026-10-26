(() => {
    const chatWindow = document.getElementById("chat-window");
    const askForm = document.getElementById("ask-form");
    const questionInput = document.getElementById("question-input");
    const askSubmitBtn = document.getElementById("ask-submit-btn");
    const conversationList = document.getElementById("conversation-list");
    const newChatBtn = document.getElementById("new-chat-btn");
    const uploadCard = document.getElementById("upload-card");
    const banner = document.getElementById("service-banner");
    const bannerMessage = document.getElementById("service-banner-message");
    let currentConversationId = null;

    async function api(url, options = {}) {
        const response = await fetch(url, { credentials: "same-origin", ...options });
        if (response.status === 401) {
            window.location.replace("/login");
            throw new Error("Sign in required.");
        }
        return response;
    }

    function escapeHtml(value) {
        const el = document.createElement("div");
        el.textContent = value || "";
        return el.innerHTML;
    }

    function renderUserBubble(content) {
        const bubble = document.createElement("div");
        bubble.className = "chat-bubble user";
        bubble.textContent = content;
        chatWindow.appendChild(bubble);
    }

    function renderAssistantBubble(entry) {
        const { content, confidence_score, sources, reason } = entry;
        const directLlm = reason === "direct_llm";
        const passed = !reason || directLlm;
        const bubble = document.createElement("div");
        bubble.className = "chat-bubble assistant" + (passed ? "" : " refused");

        const badge = document.createElement("span");
        badge.className = "confidence-badge " + (passed ? "pass" : "refuse");
        if (directLlm) {
            badge.textContent = "Conversation";
        } else if (passed) {
            const score = confidence_score == null ? "" : ` · ${(confidence_score * 100).toFixed(0)}%`;
            badge.textContent = "Grounded" + score;
        } else {
            badge.textContent = ({
                blocked: "Blocked",
                no_documents: "No documents",
                low_confidence: "Low confidence",
                ungrounded: "Could not verify",
            })[reason] || "Refused";
        }
        bubble.appendChild(badge);

        const answer = document.createElement("div");
        answer.textContent = content || "";
        bubble.appendChild(answer);
        if (sources?.length) {
            const sourceBox = document.createElement("div");
            sourceBox.className = "bubble-sources";
            const label = document.createElement("strong");
            label.textContent = "Sources";
            sourceBox.appendChild(label);
            const list = document.createElement("ul");
            sources.forEach((source) => {
                const item = document.createElement("li");
                item.textContent = `${source.document} — page ${source.page} (similarity ${(source.similarity_score * 100).toFixed(0)}%)`;
                list.appendChild(item);
            });
            sourceBox.appendChild(list);
            bubble.appendChild(sourceBox);
        }
        chatWindow.appendChild(bubble);
    }

    function scrollToBottom() {
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    async function refreshConversations() {
        const response = await api("/api/conversations");
        if (!response.ok) throw new Error("Could not load your conversations.");
        const conversations = await response.json();
        conversationList.replaceChildren();
        conversations.forEach((conversation) => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "list-group-item list-group-item-action text-truncate";
            button.textContent = conversation.title || "New chat";
            button.classList.toggle("active", conversation.id === currentConversationId);
            button.addEventListener("click", () => loadConversation(conversation.id));
            conversationList.appendChild(button);
        });
        return conversations;
    }

    async function loadConversation(conversationId) {
        currentConversationId = conversationId;
        const response = await api(`/api/conversations/${conversationId}/messages`);
        if (!response.ok) throw new Error("Could not load this conversation.");
        const messages = await response.json();
        chatWindow.replaceChildren();
        messages.forEach((message) => {
            if (message.role === "user") renderUserBubble(message.content);
            else renderAssistantBubble(message);
        });
        await refreshConversations();
        scrollToBottom();
    }

    async function createConversation() {
        const response = await api("/api/conversations", { method: "POST" });
        if (!response.ok) throw new Error("Could not start a new chat.");
        const conversation = await response.json();
        await loadConversation(conversation.id);
        questionInput.focus();
    }

    function renderTypingIndicator() {
        const indicator = document.createElement("div");
        indicator.id = "typing-indicator";
        indicator.className = "typing-indicator";
        indicator.textContent = "Thinking…";
        chatWindow.appendChild(indicator);
        scrollToBottom();
    }

    askForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const question = questionInput.value.trim();
        if (!question || !currentConversationId) return;
        askSubmitBtn.disabled = true;
        questionInput.value = "";
        renderUserBubble(question);
        renderTypingIndicator();
        try {
            const response = await api("/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question, conversation_id: currentConversationId }),
            });
            document.getElementById("typing-indicator")?.remove();
            if (response.status === 503) {
                bannerMessage.textContent = "The answer engine is unavailable. Try again later.";
                banner.classList.remove("d-none");
                return;
            }
            if (!response.ok) throw new Error("Could not answer that question. Please try again.");
            const data = await response.json();
            renderAssistantBubble({
                content: data.answer,
                confidence_score: data.confidence_score,
                sources: data.sources || [],
                reason: data.reason,
            });
            banner.classList.add("d-none");
            await refreshConversations();
            scrollToBottom();
        } catch (error) {
            document.getElementById("typing-indicator")?.remove();
            if (error.message !== "Sign in required.") {
                bannerMessage.textContent = error.message;
                banner.classList.remove("d-none");
            }
        } finally {
            askSubmitBtn.disabled = false;
        }
    });

    newChatBtn.addEventListener("click", () => createConversation().catch((error) => {
        bannerMessage.textContent = error.message;
        banner.classList.remove("d-none");
    }));

    document.getElementById("logout-btn").addEventListener("click", async () => {
        await fetch("/api/auth/logout", { method: "POST", credentials: "same-origin" });
        window.location.replace("/login");
    });

    document.getElementById("service-banner-close").addEventListener("click", () => {
        banner.classList.add("d-none");
    });

    async function initialize() {
        try {
            const meResponse = await api("/api/auth/me");
            if (!meResponse.ok) throw new Error("Could not verify your session.");
            const user = await meResponse.json();
            document.getElementById("signed-in-user").textContent = user.email;
            if (user.role === "admin") uploadCard.hidden = false;

            const conversations = await refreshConversations();
            if (conversations.length) await loadConversation(conversations[0].id);
            else await createConversation();
        } catch (error) {
            if (error.message !== "Sign in required.") {
                bannerMessage.textContent = error.message;
                banner.classList.remove("d-none");
            }
        }
    }

    initialize();
})();
