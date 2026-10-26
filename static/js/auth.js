(() => {
    const card = document.querySelector("[data-auth-mode]");
    const form = document.getElementById("auth-form");
    const errorBox = document.getElementById("auth-error");
    const submit = document.getElementById("auth-submit");
    const mode = card.dataset.authMode;

    fetch("/api/auth/me").then((response) => {
        if (response.ok) window.location.replace("/chat");
    }).catch(() => {});

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        errorBox.classList.add("d-none");
        submit.disabled = true;
        submit.textContent = mode === "signup" ? "Creating account…" : "Signing in…";
        try {
            const response = await fetch(`/api/auth/${mode}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    email: document.getElementById("email").value,
                    password: document.getElementById("password").value,
                }),
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                errorBox.textContent = data.detail || "Could not complete sign in. Please try again.";
                errorBox.classList.remove("d-none");
                return;
            }
            window.location.replace("/chat");
        } catch (error) {
            errorBox.textContent = "The server could not be reached. Please try again.";
            errorBox.classList.remove("d-none");
        } finally {
            submit.disabled = false;
            submit.textContent = mode === "signup" ? "Create account" : "Sign in";
        }
    });
})();
