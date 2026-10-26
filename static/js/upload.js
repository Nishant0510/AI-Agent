// upload.js — wires the PDF upload form to POST /upload
// Response contract: { "filename": str, "status": str, "message": str }
// NOTE: ingestion is a stub right now (Phase 7), so a successful upload only
// means the file was saved and queued — it is NOT searchable yet. Copy here
// deliberately avoids saying "ready" or "searchable now".

(() => {
    const uploadForm = document.getElementById("upload-form");
    const fileInput = document.getElementById("file-input");
    const uploadSubmitBtn = document.getElementById("upload-submit-btn");
    const uploadStatus = document.getElementById("upload-status");

    function setStatus(message, variant) {
        uploadStatus.textContent = message;
        uploadStatus.className = "form-text mt-2 text-" + variant;
    }

    uploadForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const file = fileInput.files[0];
        if (!file) return;

        if (file.type !== "application/pdf") {
            setStatus("Only PDF files are accepted.", "danger");
            return;
        }

        uploadSubmitBtn.disabled = true;
        setStatus("Uploading…", "muted");

        const formData = new FormData();
        formData.append("file", file);

        try {
            const resp = await fetch("/upload", {
                method: "POST",
                body: formData,
            });

            if (resp.status === 401) {
                window.location.replace("/login");
                return;
            }
            if (resp.status === 403) {
                setStatus("Only the administrator account can upload manuals.", "danger");
                return;
            }

            if (resp.status === 400) {
                const data = await resp.json().catch(() => ({}));
                setStatus(data.details || "That file couldn't be accepted. Check the file type and try again.", "danger");
                return;
            }

            if (!resp.ok) {
                setStatus("Upload failed. Please try again.", "danger");
                return;
            }

            const data = await resp.json();
            // Deliberately conservative: "queued" not "ready" — ingestion is
            // still a no-op stub as of Phase 7.
            setStatus(
                `"${data.filename}" was uploaded and queued for processing. It is not yet searchable — this can take a while depending on backend processing.`,
                "success"
            );
            fileInput.value = "";
        } catch (err) {
            console.error("Error calling /upload", err);
            setStatus("Upload failed due to a network or server error.", "danger");
        } finally {
            uploadSubmitBtn.disabled = false;
        }
    });
})();
