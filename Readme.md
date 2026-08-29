<div align="center">

# 🏥 Philips Product Knowledge AI Agent

### Enterprise-Grade Multi-Agent RAG System for Grounded Product Documentation Q&A

*Zero hallucination. Full traceability. Production-ready.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-1C3C3C?style=for-the-badge)](https://langchain-ai.github.io/langgraph/)
[![FAISS](https://img.shields.io/badge/FAISS-Vector%20Store-0467DF?style=for-the-badge)](https://github.com/facebookresearch/faiss)
[![HuggingFace](https://img.shields.io/badge/🤗-HuggingFace-FFD21E?style=for-the-badge)](https://huggingface.co/)
[![Qwen2.5)](https://img.shields.io/badge/Qwen2.5--7B-LLM-purple?style=for-the-badge)](https://huggingface.co/Qwen)

[![License](https://img.shields.io/badge/License-Educational%2FShowcase-lightgrey?style=flat-square)]()
[![Build](https://img.shields.io/badge/Build-Passing-brightgreen?style=flat-square)]()
[![Tests](https://img.shields.io/badge/Tests-Pytest-yellow?style=flat-square)]()
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-black?style=flat-square)]()
[![Maintained](https://img.shields.io/badge/Maintained-Yes-success?style=flat-square)]()

<br/>

**A production-ready Retrieval-Augmented Generation system that answers questions strictly from Philips product manuals — never from parametric knowledge.**

[Overview](#-overview) •
[Architecture](#-system-architecture) •
[Installation](#-installation) •
[API Reference](#-api-endpoints) •
[Testing](#-testing) •
[Roadmap](#-future-improvements)

</div>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Why This Project](#-why-this-project)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Multi-Agent Design](#-multi-agent-design)
- [LangGraph Workflow](#-langgraph-workflow)
- [Data Flow Sequence](#-data-flow-sequence)
- [Confidence Decision Logic](#-confidence-decision-logic)
- [Security Architecture](#-security-architecture)
- [Folder Structure](#-folder-structure)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [Building the Vector Database](#-building-the-vector-database)
- [Ingestion Pipeline](#-ingestion-pipeline-flow)
- [Using the UI](#-using-the-ui)
- [API Endpoints](#-api-endpoints)
- [Request Lifecycle](#-request-lifecycle-state-diagram)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Logging & Observability](#-logging--observability)
- [Performance](#-performance)
- [Security Features](#-security-features)
- [Deployment Topology](#-deployment-topology)
- [Future Improvements](#-future-improvements)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🔎 Overview

The **Philips Product Knowledge AI Agent** is an enterprise-grade **Retrieval-Augmented Generation (RAG)** system purpose-built to answer user questions **strictly from uploaded Philips product manuals**.

Unlike a conventional chatbot, this agent **never relies on parametric (model-internal) knowledge**. Every response is:

- ✅ Grounded in retrieved documentation
- ✅ Backed by source citations and page numbers
- ✅ Accompanied by retrieved chunks for transparency
- ✅ Scored with a confidence rating before being served

The system showcases a modern **Multi-Agent AI architecture** orchestrated with **LangGraph**, making it a strong reference implementation for enterprise AI applications and technical portfolios.

> **💡 Design Philosophy**
> If the answer isn't in the documents, the agent refuses to answer rather than hallucinate. Grounding is enforced at multiple pipeline stages, not just prompted for.

---

## 🎯 Why This Project

| Traditional Chatbot | Philips Product Knowledge AI Agent |
|---|---|
| Relies on LLM's internal (parametric) knowledge | Strictly grounded in retrieved documents |
| No citation of sources | Every answer includes document, page, and chunk citations |
| Vulnerable to prompt injection | Dedicated Security Agent for injection/jailbreak detection |
| Single monolithic prompt | Multi-agent pipeline with specialized responsibilities |
| No confidence signaling | Confidence-based decision making with refusal logic |
| Difficult to audit | Full structured logging with node execution trace |

---

## 👥 Who This Is For

**Primary users**

- **[Field Service Engineers]** — troubleshoot Philips equipment on-site or remotely and need fast, trustworthy answers to "does the manual say X" questions without paging through a 200-page PDF.
- **[L1/L2 Support Agents]** — handle inbound calls/tickets and need to confirm procedures, specs, or error-code meanings against the official manual before responding to a customer.

**What they do today, without this**

- Manually search PDF manuals (Ctrl+F across large documents, or physical binders).
- Ask a more senior colleague and wait for a reply.
- Rely on memory or informal tribal knowledge, which risks inconsistent or outdated answers.
- Escalate tickets that could have been resolved with a manual lookup.

**What changes with this system**

- A natural-language question returns a grounded answer with the exact document, page, and chunk it came from — so the user can verify it themselves in seconds rather than trusting an unsourced claim.
- If the manuals don't contain the answer, the system says so instead of guessing — preserving trust in the tool over time.

**Ownership post-launch**


- **Content owner:** [The documentation/knowledge-management team]
- **System owner:** [The engineering team that built it, or a platform/MLOps team]
- **Escalation path:** [The documentation/knowledge-management team, reviews the log and closes the gap in documentation]

---

## 🔗 Workflow Integration

This system is designed to plug into an **existing support workflow**, not to stand alone as a general-purpose chatbot.

> **📝 Status:** The specific integration point below is illustrative. Replace it with the actual workflow this will be embedded in before calling it "integrated."

**Where it fits**

```mermaid
flowchart LR
    A["Ticket / Call Comes In"] --> B{"Can agent answer<br/>from memory?"}
    B -->|Yes| C["Respond directly"]
    B -->|No| D["Query Philips AI Agent<br/>via ticket tool / technician app"]
    D --> E{"Confident,<br/>grounded answer?"}
    E -->|Yes| F["Agent verifies citation<br/>& responds to customer"]
    E -->|No / Refused| G["Escalate to L2 /<br/>flag documentation gap"]

    style D fill:#e3f2fd,stroke:#1565c0
    style F fill:#c8e6c9,stroke:#2e7d32
    style G fill:#ffe0b2,stroke:#e65100
```

**Integration points to consider** (choose and detail the one(s) relevant to your deployment):

| Integration Point | Description | Status |
|---|---|---|
| **Ticketing system lookup** | Support agent queries the system from within the ticketing tool (e.g., as a sidebar panel or slash command) before responding to a ticket | [Planned / In progress / Not started] |
| **Call center knowledge lookup** | Agent queries the system live during a call, e.g., via a browser tab or internal tool, to answer caller questions in real time | [Planned / In progress / Not started] |
| **Technician mobile app** | Field engineer queries the system from a mobile app while on-site, without needing network access to the full manual PDF | [Planned / In progress / Not started] |
| **Standalone web UI (current state)** | The Bootstrap chat interface included in this repo, used directly | Implemented |

**Why this matters:** a chatbot that exists in isolation, disconnected from where support work actually happens, tends to go unused. The goal is for this to be a lookup step inside an existing process — not an extra tool agents have to remember to open.

---

## ✨ Features

<table>
<tr>
<td width="50%" valign="top">

**Core Architecture**
- Multi-Agent Architecture using LangGraph
- Enterprise RAG Pipeline
- Modular Clean Architecture
- Dependency Injection
- FastAPI Backend

**Document Processing**
- PDF Document Ingestion
- Semantic Chunking
- BAAI/bge-base-en-v1.5 Embeddings
- FAISS Vector Database

</td>
<td width="50%" valign="top">

**Safety & Trust**
- Prompt Injection Detection
- Jailbreak Prevention
- Hallucination Prevention
- Confidence-Based Decision Making
- Source Citations & Page Number References

**Operations**
- Qwen2.5-7B/OpenAI(Optional) LLM
- Structured Logging
- Bootstrap Chat Interface
- Comprehensive Unit Tests

</td>
</tr>
</table>

---

## 🏗 System Architecture

```mermaid
graph TB
    subgraph Client["🖥️ Client Layer"]
        UI["Web Frontend<br/>HTML • Bootstrap • JS"]
    end

    subgraph API["⚙️ API Layer"]
        FASTAPI["FastAPI REST API"]
    end

    subgraph Orchestration["🧠 Orchestration Layer"]
        SUPERVISOR["LangGraph Supervisor Orchestrator"]
    end

    subgraph Agents["🤖 Agent Layer"]
        SECURITY["Security Agent"]
        DOCUMENT["Document Agent"]
        RETRIEVAL["Retrieval Agent"]
        LOGGING["Logging Agent"]
        CONFIDENCE["Confidence Agent"]
        ANSWER["Answer Agent"]
        CITATION["Citation Agent"]
        VALIDATION["Validation Agent"]
    end

    subgraph Storage["💾 Storage & Services"]
        DOCSTORE["Document Store"]
        EMBED["Embedding Service"]
        FAISS["FAISS Vector Store"]
    end

    UI --> FASTAPI
    FASTAPI --> SUPERVISOR
    SUPERVISOR --> SECURITY
    SUPERVISOR --> DOCUMENT
    SUPERVISOR --> RETRIEVAL
    SUPERVISOR --> LOGGING

    DOCUMENT --> DOCSTORE
    RETRIEVAL --> EMBED
    EMBED --> FAISS
    SECURITY -.blocks unsafe input.-> RETRIEVAL
    FAISS --> CONFIDENCE

    CONFIDENCE -->|Low Confidence| REFUSAL["Refusal Response"]
    CONFIDENCE -->|Sufficient Confidence| ANSWER
    ANSWER --> CITATION
    CITATION --> VALIDATION
    VALIDATION --> FINAL["Final Response"]

    style Client fill:#e3f2fd,stroke:#1565c0
    style API fill:#e8f5e9,stroke:#2e7d32
    style Orchestration fill:#fff3e0,stroke:#e65100
    style Agents fill:#f3e5f5,stroke:#6a1b9a
    style Storage fill:#fce4ec,stroke:#ad1457
    style REFUSAL fill:#ffcdd2,stroke:#c62828
    style FINAL fill:#c8e6c9,stroke:#2e7d32
```

---

## 🧩 Multi-Agent Design

Each agent has a **single, well-defined responsibility**, following the separation-of-concerns principle used in enterprise microservice design.

```mermaid
graph LR
    A["1️⃣ Supervisor Orchestrator<br/>Entry point & routing"] --> B["2️⃣ Security Agent<br/>Injection & jailbreak detection"]
    B --> C["3️⃣ Document Agent<br/>Verify documents & DB"]
    C --> D["4️⃣ Retrieval Agent<br/>FAISS search & Top-K"]
    D --> E["5️⃣ Confidence Agent<br/>Score & gate decision"]
    E --> F["6️⃣ Answer Agent<br/>Grounded generation"]
    F --> G["7️⃣ Citation Agent<br/>Sources & page numbers"]
    G --> H["8️⃣ Validation Agent<br/>Grounding verification"]

    style A fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style B fill:#ffebee,stroke:#c62828,stroke-width:2px
    style C fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style D fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style E fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    style F fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    style G fill:#e0f2f1,stroke:#00695c,stroke-width:2px
    style H fill:#fce4ec,stroke:#ad1457,stroke-width:2px
```

### Agent Responsibility Matrix

| # | Agent | Primary Responsibility | Key Outputs |
|---|---|---|---|
| 1 | **Supervisor Orchestrator** | Entry point, execution routing, state management, conditional branching | Workflow control signals |
| 2 | **Security Agent** | Prompt injection detection, jailbreak detection, sanitization, unsafe request blocking | Sanitized query / block signal |
| 3 | **Document Agent** | Verify uploaded documents, FAISS DB integrity, metadata validity | Availability status |
| 4 | **Retrieval Agent** | Generate query embeddings, FAISS search, Top-5 retrieval, deduplication, similarity thresholding | Retrieved chunks |
| 5 | **Confidence Agent** | Evaluate retrieval quality, compute confidence score, gate generation | Confidence score + decision |
| 6 | **Answer Agent** | Build context, construct prompt, generate grounded response | Draft answer |
| 7 | **Citation Agent** | Attach document names, page numbers, chunk IDs, similarity scores | Cited answer |
| 8 | **Validation Agent** | Verify grounding, ensure citations exist, prevent hallucination, validate confidence | Final validated response |

<details>
<summary><strong>🔐 Security Agent — Blocked Request Examples</strong></summary>

The Security Agent actively detects and blocks adversarial prompts, including:

- Instructions attempting to override system behavior (e.g., "ignore previous instructions")
- Attempts to expose internal system prompts
- Attempts to impersonate a different AI system
- Attempts to trigger destructive operations on the vector database
- Requests to answer from general internet knowledge instead of the document store
- Requests to fabricate or invent information not present in the source documents

</details>

---

## 🔄 LangGraph Workflow

```mermaid
flowchart TD
    START(["User Question"]) --> VALID["Input Validation"]
    VALID --> SEC["Security Agent<br/>(Prompt Injection Detection)"]
    SEC --> DOCCHECK["Document Availability Check"]
    DOCCHECK --> EMBED["Embedding Generation"]
    EMBED --> RETRIEVE["FAISS Retrieval"]
    RETRIEVE --> EVAL["Retrieval Evaluation"]
    EVAL --> CONF{"Confidence<br/>Decision"}

    CONF -->|Low Confidence| REFUSE["🚫 Refuse Answer"]
    CONF -->|High Confidence| CTX["Context Builder"]

    CTX --> PROMPT["Prompt Builder"]
    PROMPT --> LLM["LLM Response Generation"]
    LLM --> CITE["Citation Formatter"]
    CITE --> CALC["Confidence Calculation"]
    CALC --> GROUND["Grounding Validation"]
    GROUND --> FINAL(["Final Response"])
    REFUSE --> FINAL

    style START fill:#bbdefb,stroke:#1565c0
    style FINAL fill:#c8e6c9,stroke:#2e7d32
    style REFUSE fill:#ffcdd2,stroke:#c62828
    style CONF fill:#fff9c4,stroke:#f57f17
```

> **⚠️ Warning**
> If retrieval confidence falls below `SIMILARITY_THRESHOLD`, the workflow short-circuits directly to a refusal response — the LLM generation stage is never invoked. This prevents hallucinated answers from ever reaching the user.

---

## 🔁 Data Flow Sequence

```mermaid
sequenceDiagram
    actor User
    participant UI as Web Frontend
    participant API as FastAPI
    participant Sup as Supervisor Agent
    participant Sec as Security Agent
    participant Ret as Retrieval Agent
    participant Vec as FAISS Vector Store
    participant Conf as Confidence Agent
    participant Ans as Answer Agent
    participant LLM as Qwen2.5-7B-Instruct
    participant Cit as Citation Agent
    participant Val as Validation Agent

    User->>UI: Submit question
    UI->>API: POST /ask
    API->>Sup: Forward request
    Sup->>Sec: Validate & sanitize input

    alt Unsafe input detected
        Sec-->>API: Block request
        API-->>UI: Return refusal
    else Safe input
        Sec->>Ret: Proceed with query
        Ret->>Vec: Embed & search Top-K
        Vec-->>Ret: Return candidate chunks
        Ret->>Conf: Submit retrieval results
        Conf->>Conf: Compute confidence score

        alt Confidence below threshold
            Conf-->>API: Refusal response
        else Confidence sufficient
            Conf->>Ans: Build context & generate
            Ans->>LLM: Prompt with grounded context
            LLM-->>Ans: Generated response
            Ans->>Cit: Attach citations
            Cit->>Val: Validate grounding
            Val-->>API: Final validated response
        end
    end

    API-->>UI: JSON response + citations
    UI-->>User: Render answer with sources
```

---

## 🎚 Confidence Decision Logic

```mermaid
stateDiagram-v2
    [*] --> RetrievalComplete
    RetrievalComplete --> ComputeScore: Chunks retrieved

    ComputeScore --> BelowThreshold: score < SIMILARITY_THRESHOLD
    ComputeScore --> AboveThreshold: score >= SIMILARITY_THRESHOLD

    BelowThreshold --> RefusalResponse
    RefusalResponse --> [*]

    AboveThreshold --> GenerateAnswer
    GenerateAnswer --> AttachCitations
    AttachCitations --> ValidateGrounding

    ValidateGrounding --> GroundingFailed: No citations found
    ValidateGrounding --> GroundingPassed: Citations verified

    GroundingFailed --> RefusalResponse
    GroundingPassed --> FinalResponse
    FinalResponse --> [*]
```

---

## 🔐 Security Architecture

```mermaid
graph TD
    INPUT["Incoming User Query"] --> SCAN["Security Agent Scan"]

    SCAN --> INJ{"Prompt Injection<br/>Detected?"}
    INJ -->|Yes| BLOCK1["❌ Block Request"]
    INJ -->|No| JAIL{"Jailbreak Attempt<br/>Detected?"}

    JAIL -->|Yes| BLOCK2["❌ Block Request"]
    JAIL -->|No| SANITIZE["Sanitize Query"]

    SANITIZE --> ISOLATE["Context Isolation"]
    ISOLATE --> SYSPROMPT["System Prompt Protection Check"]
    SYSPROMPT --> PROCEED["✅ Proceed to Retrieval Agent"]

    BLOCK1 --> LOG1["Log Security Event"]
    BLOCK2 --> LOG1
    LOG1 --> REFUSAL["Return Refusal Response"]

    style BLOCK1 fill:#ffcdd2,stroke:#c62828
    style BLOCK2 fill:#ffcdd2,stroke:#c62828
    style PROCEED fill:#c8e6c9,stroke:#2e7d32
    style REFUSAL fill:#ffe0b2,stroke:#e65100
```

> **📝 Note**
> Security scanning happens **before** document availability checks and retrieval — no query reaches the vector store without first passing injection and jailbreak detection.

---

## 📁 Folder Structure

```text
product-ai-agent/
│
├── app/
│   ├── agent/
│   │   ├── graph/          # LangGraph graph definitions
│   │   ├── nodes/          # Individual agent node implementations
│   │   ├── routers/        # Conditional routing logic
│   │   ├── state/          # Shared state schemas
│   │   └── tools/          # Agent tool implementations
│   │
│   ├── api/                # FastAPI route definitions
│   ├── ingestion/          # PDF parsing & chunking pipeline
│   ├── retrieval/          # FAISS retrieval logic
│   ├── vectorstore/        # Vector store management
│   ├── llm/                # LLM client & inference wrappers
│   ├── prompts/            # Prompt templates
│   ├── services/           # Business logic services
│   ├── models/             # Pydantic / data models
│   ├── utils/               # Shared utilities
│
├── data/                   # Uploaded documents & vector DB
├── static/                 # Static frontend assets
├── templates/               # Jinja2/HTML templates
├── logs/                   # Structured application logs
├── tests/                  # Unit & integration tests
│
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
└── README.md
```

---

## ⚙️ Installation

### 1️⃣ Clone Repository

```bash
git clone <repository_url>
cd product-ai-agent
```

### 2️⃣ Create Virtual Environment

<details>
<summary><strong>🪟 Windows</strong></summary>

```powershell
python -m venv .venv
.venv\Scripts\activate
```

</details>

<details>
<summary><strong>🐧 Linux / macOS</strong></summary>

```bash
python3 -m venv .venv
source .venv/bin/activate
```

</details>

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔧 Configuration

Create a `.env` file in the project root:

```dotenv
APP_NAME=Philips Product Knowledge AI Agent

LOG_LEVEL=INFO

EMBEDDING_MODEL=BAAI/bge-base-en-v1.5
LLM_MODEL=Qwen/Qwen2.5-7B

VECTOR_DB=data/vector_db
DATA_DIRECTORY=data/users

TOP_K=5
SIMILARITY_THRESHOLD=0.75
MAX_CONTEXT_CHUNKS=5

DEVICE=cpu
```

### Configuration Reference

| Variable | Description | Default |
|---|---|---|
| `APP_NAME` | Display name of the application | `Philips Product Knowledge AI Agent` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `EMBEDDING_MODEL` | HuggingFace embedding model identifier | `BAAI/bge-base-en-v1.5` |
| `LLM_MODEL` | LLM used for answer generation | `Qwen/Qwen2.5-7B` |
| `VECTOR_DB` | Path to persisted FAISS index | `data/vector_db` |
| `DATA_DIRECTORY` | Directory for uploaded source PDFs | `data/users` |
| `TOP_K` | Number of chunks retrieved per query | `5` |
| `SIMILARITY_THRESHOLD` | Minimum similarity score to proceed with generation | `0.50` |
| `MAX_CONTEXT_CHUNKS` | Maximum chunks passed into LLM context | `5` |
| `DEVICE` | Inference device (`cpu` or `cuda`) | `cpu` |

> **💡 Tip**
> Lower `SIMILARITY_THRESHOLD` cautiously — reducing it increases recall but also increases the risk of low-quality or loosely related context being passed to the LLM.

---

## 🚀 Running the Application

Start the backend server:

```bash
uvicorn main:app --reload
```

| Resource | URL |
|---|---|
| Web Interface | `http://127.0.0.1:8000` |
| Swagger UI (API Docs) | `http://127.0.0.1:8000/docs` |

---

## 🐳 Running with Docker
 
The application ships with a CPU-only `Dockerfile` and a `docker-compose.yml` for running the full stack — FastAPI app, FAISS index, and structured logs — as a single containerized service. The LLM (`Qwen2.5-7B-Instruct`) is served through **Ollama**, which runs separately from the app container.
 
> **📝 Note**
> Ollama is not bundled into the app image. It must be running and reachable — either on your host machine or as a separate container/service — before you start the app container.
 
### 1️⃣ Prerequisites
 
- Docker and Docker Compose installed
- Ollama installed and running, with the Qwen2.5-7B-Instruct model pulled:
```bash
ollama pull qwen2.5:7b-instruct
ollama serve
```
 
### 2️⃣ Configure Environment
 
Create a `.env` file in the project root (same variables as the [Configuration](#-configuration) section). The Compose file will also set a few container-specific defaults automatically (`DEVICE`, `VECTOR_DB`, `DATA_DIRECTORY`, `LOG_DIR`), so you don't need to duplicate those in `.env` unless you want to override them.
 
If Ollama is running on your **host machine** (not in a container), the default `OLLAMA_HOST` is already set to reach it via `host.docker.internal`. If you're running Ollama elsewhere — a remote server or a separate container — override it in `.env`:
 
```dotenv
OLLAMA_HOST=http://your-ollama-host:11434
```
 
### 3️⃣ Build and Run
 
```bash
docker compose up --build
```
 
This will:
- Build the app image from the `Dockerfile` (CPU-only base, `libgomp1` installed for FAISS/PyTorch)
- Start the FastAPI app on `http://127.0.0.1:8000`
- Mount persistent volumes for the FAISS index, uploaded manuals, and logs
| Resource | URL |
|---|---|
| Web Interface | `http://127.0.0.1:8000` |
| Swagger UI (API Docs) | `http://127.0.0.1:8000/docs` |
 
To run in the background:
 
```bash
docker compose up --build -d
```
 
To stop:
 
```bash
docker compose down
```
 
### 4️⃣ Persisted Data
 
The Compose file bind-mounts three directories so data survives container restarts and rebuilds:
 
| Host Path | Container Path | Purpose |
|---|---|---|
| `./data/vector_db` | `/app/data/vector_db` | Persisted FAISS index |
| `./data/users` | `/app/data/users` | Uploaded Philips product manuals |
| `./logs` | `/app/logs` | Structured application logs |
 
Rebuilding the image (`docker compose up --build`) does **not** wipe these — they live on the host and are re-mounted on every container start.
 
> **⚠️ Warning**
> The container runs as a non-root `appuser`, matching the `Dockerfile`. If you see permission errors on the mounted volumes, check that the host-side `data/` and `logs/` directories are writable by the container's UID.
 
### Container Architecture
 
```mermaid
graph LR
    subgraph Host["🖥️ Host Machine"]
        OLLAMA["Ollama Server<br/>Qwen2.5-7B-Instruct"]
        VOLDB[("./data/vector_db")]
        VOLUSERS[("./data/users")]
        VOLLOGS[("./logs")]
    end
 
    subgraph Container["🐳 App Container"]
        UVICORN["Uvicorn + FastAPI"]
        GRAPH["LangGraph Runtime"]
    end
 
    GRAPH -->|HTTP| OLLAMA
    UVICORN --> GRAPH
    GRAPH -.mounted.-> VOLDB
    GRAPH -.mounted.-> VOLUSERS
    GRAPH -.mounted.-> VOLLOGS
 
    style Host fill:#e3f2fd,stroke:#1565c0
    style Container fill:#e8f5e9,stroke:#2e7d32
```
 
> **💡 Tip**
> This CPU-only setup is intended for local development and small-scale demos. For production, place the app behind a reverse proxy (e.g., Nginx) with TLS termination, and consider Kubernetes for orchestration — see [Future Improvements](#-future-improvements).
---

## 🗃 Building the Vector Database

### Step 1 — Add Source Documents

Place Philips product manuals (PDF) into:

```text
data/users/
```

### Step 2 — Run Ingestion Pipeline

```bash
python build_vector_database.py
```

### 📥 Ingestion Pipeline Flow

```mermaid
flowchart LR
    A["📄 Place PDFs in<br/>data/users/"] --> B["Parse PDFs"]
    B --> C["Extract Text"]
    C --> D["Generate Semantic Chunks"]
    D --> E["Create Embeddings<br/>(BAAI/bge-base-en-v1.5)"]
    E --> F["Build FAISS Index"]
    F --> G["Persist Metadata & Vectors<br/>(data/vector_db)"]
    G --> H["✅ Ready for Retrieval"]

    style A fill:#e3f2fd,stroke:#1565c0
    style H fill:#c8e6c9,stroke:#2e7d32
```

> **📝 Note**
> The ingestion pipeline must be re-run any time new documents are added or existing documents are updated — the FAISS index does not update incrementally by default.

---

## 🖥 Using the UI

Once the FastAPI server is running, navigate to `http://127.0.0.1:8000` to access:

| Component | Description |
|---|---|
| 📤 **PDF Upload** | Upload new Philips product manuals directly through the browser |
| 💬 **Chat Window** | Ask natural-language questions about uploaded documentation |
| 🎯 **Confidence Badge** | Visual indicator of the system's confidence in each answer |
| 📚 **Source Panel** | Displays cited documents, page numbers, and retrieved chunks |
| 🕘 **Conversation History** | Maintains a record of prior questions and answers |
| 📱 **Responsive Bootstrap Layout** | Fully responsive across desktop and mobile |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Web Interface |
| `GET` | `/health` | Health Check |
| `POST` | `/upload` | Upload PDFs |
| `POST` | `/ask` | Ask Questions |
| `GET` | `/sources` | View Uploaded Sources |

<details>
<summary><strong>📮 Example: POST /ask</strong></summary>

```bash
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
        "question": "What is the recommended cleaning cycle for the Philips AVENT sterilizer?"
      }'
```

**Example Response Shape:**

```json
{
  "answer": "...",
  "confidence_score": 0.87,
  "sources": [
    {
      "document": "AVENT_Sterilizer_Manual.pdf",
      "page": 14,
      "chunk_id": "chunk_0091",
      "similarity_score": 0.89
    }
  ]
}
```

</details>

---

## 🔄 Request Lifecycle State Diagram

```mermaid
stateDiagram-v2
    [*] --> Received: POST /ask
    Received --> Validating: Input Validation
    Validating --> SecurityCheck
    SecurityCheck --> Blocked: Injection/Jailbreak detected
    SecurityCheck --> DocCheck: Passed
    DocCheck --> NoDocuments: No documents found
    DocCheck --> Retrieving: Documents available
    Retrieving --> ConfidenceGate
    ConfidenceGate --> Refused: Low confidence
    ConfidenceGate --> Generating: Sufficient confidence
    Generating --> Citing
    Citing --> Validating2: Grounding Validation
    Validating2 --> Responded: Passed
    Validating2 --> Refused: Failed
    Blocked --> [*]
    NoDocuments --> [*]
    Refused --> [*]
    Responded --> [*]
```

---

## 🧪 Testing

Run all tests:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app
```



| Category | Scenario |
|---|---|
| **Upload** | Multiple PDFs, large PDFs, corrupted PDFs, empty documents |
| **Security** | Prompt injection, jailbreak attempts |
| **Query Handling** | Unknown questions, long queries, concurrent requests |
| **System State** | Missing vector database, confidence threshold validation, citation generation |

---

## 🛠 Troubleshooting

<details>
<summary><strong>❌ No documents found</strong></summary>

**Cause:** No manuals uploaded.

**Solution:**
1. Add PDFs to `data/users`
2. Rebuild the vector database

</details>

<details>
<summary><strong>❌ Vector database missing</strong></summary>

**Cause:** FAISS index not created.

**Solution:**

```bash
python build_vector_database.py
```

</details>

<details>
<summary><strong>🐢 Slow responses</strong></summary>

**Possible causes:**
- CPU inference
- Large document corpus
- Cold model startup

**Recommendations:**
- Use GPU acceleration
- Batch embedding generation
- Increase available RAM

</details>

<details>
<summary><strong>📉 Low confidence responses</strong></summary>

**Possible causes:**
- Missing information in manuals
- Poorly phrased queries
- Similarity threshold too high

**Recommendations:**
- Verify the required information exists in the uploaded documentation
- Use more specific product names and terminology
- Adjust the retrieval threshold if appropriate

</details>

> **⚠️ Warning**
> Do not lower `SIMILARITY_THRESHOLD` as a blanket fix for low-confidence responses — first verify the source documentation actually contains the answer.

---

## 📊 Logging & Observability

The application records structured logs for every request:

```mermaid
graph LR
    A["Request Received"] --> B["Timestamp"]
    A --> C["User Question"]
    A --> D["Retrieved Chunks"]
    A --> E["Similarity Scores"]
    A --> F["LLM Latency"]
    A --> G["Execution Time"]
    A --> H["Confidence Score"]
    A --> I["Errors"]
    A --> J["Node Execution Trace"]

    B & C & D & E & F & G & H & I & J --> LOG["📁 logs/"]

    style LOG fill:#fff3e0,stroke:#e65100,stroke-width:2px
```

| Field | Purpose |
|---|---|
| Timestamp | Request time correlation |
| User Question | Audit trail of queries |
| Retrieved Chunks | Debugging retrieval quality |
| Similarity Scores | Confidence tuning |
| LLM Latency | Performance monitoring |
| Execution Time | End-to-end SLA tracking |
| Confidence Score | Quality assurance |
| Errors | Failure diagnostics |
| Node Execution Trace | Full LangGraph path replay |

Logs are stored under `logs/`.

---

## ⚡ Performance

The following snapshot was generated from `logs/app.jsonl` using the
latency aggregation script. It covers six completed requests across 18 parsed
JSON log records; no malformed records were skipped.

| Outcome | Count |
|---|---:|
| Responded | 6 |

### End-to-end request latency

| Requests | P50 | P95 | Min | Max |
|---:|---:|---:|---:|---:|
| 6 | 10,812.42 ms | 18,056.40 ms | 2,656.86 ms | 18,597.94 ms |

### Node latency

| Node | Samples | P50 | P95 | Min | Max |
|---|---:|---:|---:|---:|
| `graph:step:1` | 6 | 0.54 ms | 2.64 ms | 0.42 ms | 3.27 ms |
| `graph:step:2` | 6 | 0.69 ms | 4.25 ms | 0.44 ms | 5.25 ms |
| `graph:step:3` | 6 | 156.50 ms | 6,883.93 ms | 44.37 ms | 6,915.25 ms |
| `graph:step:4` | 6 | 0.55 ms | 0.64 ms | 0.52 ms | 0.66 ms |
| `graph:step:5` | 6 | 7,254.16 ms | 15,124.94 ms | 2,576.25 ms | 16,239.35 ms |
| `graph:step:6` | 6 | 0.38 ms | 1.95 ms | 0.31 ms | 2.12 ms |
| `graph:step:7` | 6 | 0.38 ms | 2.06 ms | 0.31 ms | 2.22 ms |
| `seq:step:3` | 18 | 0.03 ms | 0.20 ms | 0.03 ms | 0.21 ms |
| `unknown_node` | 6 | 10,793.77 ms | 18,052.05 ms | 2,656.61 ms | 18,592.44 ms |

LLM latency was not recorded for this sample (`count=0`). This means no
percentile can be reported; it does **not** mean LLM latency was zero. The
`graph:*`, `seq:*`, and `unknown_node` labels are LangGraph callback labels.

Recalculate these figures as log volume grows:

```bash
venv\\Scripts\\python.exe scripts\\aggregate_log_latencies.py --log-path logs\\app.jsonl
```

---

## 🛡 Security Features

| Feature | Description |
|---|---|
| **Prompt Injection Detection** | Identifies and blocks attempts to override system instructions |
| **Jailbreak Prevention** | Detects role-play or persona-override attacks |
| **System Prompt Protection** | Prevents disclosure of internal prompt configuration |
| **Context Isolation** | Ensures user input cannot contaminate agent instructions |
| **Confidence-Based Refusal** | Automatically refuses to answer when retrieval confidence is low |
| **Strict Document Grounding** | Disallows any response not traceable to retrieved source chunks |

---

## 🌐 Deployment Topology

```mermaid
graph TB
    subgraph Client
        Browser["Browser / API Client"]
    end

    subgraph Server["Application Server"]
        Uvicorn["Uvicorn ASGI Server"]
        FastAPIApp["FastAPI Application"]
        Graph["LangGraph Runtime"]
    end

    subgraph ModelLayer["Model Layer"]
        Embedder["BAAI/bge-base-en-v1.5<br/>(Embedding Model)"]
        LLMModel["Qwen2.5-7B/OpenAI(optional)<br/>(Generation Model)"]
    end

    subgraph DataLayer["Data Layer"]
        FAISSIdx[("FAISS Index")]
        Docs[("PDF Documents")]
        LogFiles[("Structured Logs")]
    end

    Browser -->|HTTPS| Uvicorn
    Uvicorn --> FastAPIApp
    FastAPIApp --> Graph
    Graph --> Embedder
    Graph --> LLMModel
    Graph --> FAISSIdx
    Graph --> Docs
    Graph --> LogFiles

    style Client fill:#e3f2fd,stroke:#1565c0
    style Server fill:#e8f5e9,stroke:#2e7d32
    style ModelLayer fill:#f3e5f5,stroke:#6a1b9a
    style DataLayer fill:#fce4ec,stroke:#ad1457
```

> **💡 Tip**
> For production deployments, place Uvicorn behind a reverse proxy (e.g., Nginx) with TLS termination, and consider deploying via Docker/Kubernetes as noted in the [Future Improvements](#-future-improvements) section.

---


## 📈 Impact

> **⚠️ Honesty note:** This project has **not** run a formal pilot with real users. The numbers below come from **internal log aggregation and a 6-question grounding evaluation set**, not from field-measured business outcomes (ticket deflection, handle-time reduction, agent satisfaction). Sample sizes are small (n=6) — treat these as early system-characterization data, not statistically robust claims, until a larger eval set and a real pilot exist.

**Current status:** Internal testing only — no pilot users yet. Latency and grounding-quality data below are from local runs against the ingested Philips manual set.

### What has actually been measured

**Request latency** (aggregated from structured logs, `count=6` completed requests, 1 refused / 5 responded)

| Metric | P50 | P95 | Min | Max |
|---|---|---|---|---|
| End-to-end request execution time | 3,679.85 ms | 40,763.85 ms | 89.26 ms | 50,482.33 ms |

| Node | P50 | P95 | Min | Max | Notes |
|---|---|---|---|---|---|
| `graph:step:1` (Security) | 0.65 ms | 3.27 ms | 0.53 ms | 4.11 ms | Negligible cost |
| `graph:step:2` (Document check) | 0.79 ms | 4.45 ms | 0.47 ms | 5.66 ms | Negligible cost |
| `graph:step:3` (Retrieval) | 108.17 ms | 6,859.12 ms | 71.99 ms | 9,061.47 ms | High P95 variance — worth investigating |
| `graph:step:4` (Confidence gate) | 0.71 ms | 3.34 ms | 0.60 ms | 4.19 ms | Negligible cost |
| `graph:step:5` (likely Answer/LLM generation) | 3,560.48 ms | 33,848.93 ms | 0.54 ms | 41,358.26 ms | **Dominant cost** — see gap below |
| `graph:step:6` (Citation) | 0.39 ms | 2.38 ms | 0.28 ms | 2.44 ms | Negligible cost |
| `graph:step:7` (Validation) | 0.37 ms | 1.70 ms | 0.32 ms | 2.01 ms | Negligible cost |

> **⚠️ Observability gap:** `LLM latency: count=0` — LLM generation time is not currently being logged as its own metric; node timings are logged as `unknown_node` / unlabeled `graph:step:N` instead. Given step 5's cost profile (3.56s p50, up to 41s p95, near-zero min on the refused case), it is almost certainly where LLM generation happens, but this is an inference from timing shape, not a confirmed attribution. **Action:** add explicit LLM-latency instrumentation before quoting generation time as a standalone number.

**Grounding evaluation** (`tests/eval_set.json`, 6 questions — 3 in-scope, 3 out-of-scope — run against `/ask`)

| Metric | Value | Target | Assessment |
|---|---|---|---|
| Citation-presence rate (in-scope) | 100.0% | 100% | ✅ Met |
| Refusal rate (out-of-scope) | 100.0% | 100% | ✅ Met |
| False-refusal rate (in-scope) | 33.3% | 0% | ❌ **Gap — see below** |
| Precision@k (expected doc in sources) | 100.0% | as high as possible | ✅ Met |
| Avg. confidence (in-scope) | 0.738 | > `SIMILARITY_THRESHOLD` | ✅ Met (threshold 0.75, avg. just below — see note) |
| Avg. latency | 11.94 s | — | For reference only, n=6 |
| Errored requests | 0 / 6 | 0 | ✅ Met |

**Per-case detail**

| ID | Scope | Confidence | Cited? | Refused? | Doc Match | Question |
|---|---|---|---|---|---|---|
| q01 | in_scope | 0.783 | yes | yes | ✅ | How should I clean the DreamStation 2 humidifier water tank? |
| q02 | in_scope | 0.730 | yes | no | ✅ | How do I replace the air filter in a DreamStation 2? |
| q03 | in_scope | 0.701 | yes | no | ✅ | Where should I place the DreamStation 2 device during use? |
| oos01 | out_of_scope | 0.333 | no | yes | — | What is the capital of France? |
| oos02 | out_of_scope | 0.761 | yes | yes | — | How should I clean a ResMed AirSense 10 humidifier water tank? |
| oos03 | out_of_scope | 0.626 | yes | yes | — | How do I replace the battery in a DreamStation Go travel CPAP? |


### What can be reasonably projected from the above (and how)

- **Time-to-answer, if adopted:** median end-to-end latency of ~3.7s (P50) is a defensible lower bound on how fast a user could get a grounded answer through this tool. The P95 of ~40.8s is a real tail-latency risk for interactive use (e.g., a live call) and should be treated as a blocker for real-time workflow integration until narrowed — this is not yet compared against a timed manual-search baseline (see [Who This Is For](#-who-this-is-for)).
- **Grounding behavior is directionally sound but not yet reliable:** the system correctly distinguishes lexically-similar-but-wrong-product questions (oos02, oos03) from genuinely in-scope ones, which is the hardest case for a grounding gate to get right. But a 33.3% false-refusal rate on only 3 in-scope test cases means the in-scope reliability claim cannot be generalized yet — it takes only one more accurate answer or one more false refusal to swing this metric by 33 points.


### Plan to close the gap

1. **Root-cause q01's false refusal** — check Validation Agent logs for that specific request to see whether a citation was found but discarded, or never attached.
2. **Instrument LLM latency explicitly** (separate from total node duration) so `graph:step:5` / `unknown_node` cost can be attributed correctly.
3. **Expand the eval set** beyond 6 questions — 3 in-scope cases is too small to trust a false-refusal percentage.
4. **Investigate P95 tail latency** on `graph:step:3` (retrieval) and `graph:step:5` (likely generation) before considering this viable for real-time workflows (live call, chat).
5. **Define and run an actual pilot** per [Who This Is For](#-who-this-is-for) — including a timed manual-search baseline — before making any deflection/time-saved claims externally.
---

## 🗺 Future Improvements

```mermaid
graph TD
    ROOT["🚀 Roadmap"]

    ROOT --> RETR["Retrieval Enhancements"]
    RETR --> R1["Hybrid Retrieval (BM25 + Dense)"]
    RETR --> R2["Cross-Encoder Reranking"]

    ROOT --> UX["User Experience"]
    UX --> U1["Streaming Responses"]
    UX --> U2["Multi-turn Conversation Memory"]

    ROOT --> DOC["Document Processing"]
    DOC --> D1["OCR Support for Scanned PDFs"]
    DOC --> D2["Table and Image Extraction"]
    DOC --> D3["Multi-language Document Retrieval"]
    DOC --> D4["Automatic Document Versioning"]

    ROOT --> INFRA["Infrastructure"]
    INFRA --> I1["Elasticsearch / OpenSearch Integration"]
    INFRA --> I2["Milvus, Qdrant, or Pinecone Support"]
    INFRA --> I3["Docker and Kubernetes Deployment"]
    INFRA --> I4["Distributed Workers (Celery / Ray)"]
    INFRA --> I5["Model Quantization for Faster Inference"]

    ROOT --> OPS["Operations & Governance"]
    OPS --> O1["Authentication & RBAC"]
    OPS --> O2["Monitoring with Prometheus & Grafana"]
    OPS --> O3["CI/CD Pipeline (GitHub Actions)"]
    OPS --> O4["Model Evaluation Dashboard"]

    style ROOT fill:#fff3e0,stroke:#e65100,stroke-width:3px
```

| Category | Planned Enhancement |
|---|---|
| Retrieval | Hybrid Retrieval (BM25 + Dense Retrieval) |
| Retrieval | Cross-Encoder Reranking |
| UX | Streaming Responses |
| UX | Multi-turn Conversation Memory |
| Document Processing | OCR Support for Scanned PDFs |
| Document Processing | Table and Image Extraction |
| Document Processing | Multi-language Document Retrieval |
| Document Processing | Automatic Document Versioning |
| Infrastructure | Elasticsearch or OpenSearch Integration |
| Infrastructure | Milvus, Qdrant, or Pinecone Vector Store Support |
| Infrastructure | Model Quantization for Faster Inference |
| Infrastructure | Distributed Worker Architecture with Celery or Ray |
| Operations | Authentication and Role-Based Access Control |
| Operations | Monitoring with Prometheus and Grafana |
| Operations | CI/CD Pipeline with GitHub Actions |


---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

> **📝 Note**
> Please ensure all new features include corresponding unit tests under `tests/` and pass `pytest --cov=app` before submitting a PR.

---

## 📄 License

This project is intended as an **enterprise AI engineering showcase and educational reference**.

> **⚠️ Important**
> Review and comply with the licenses of all third-party models, libraries, and datasets used (including `Qwen2.5-7B`, `BAAI/bge-base-en-v1.5`, and FAISS) before deploying this system in a production environment.

---

<div align="center">

**Built with LangGraph • FastAPI • FAISS • HuggingFace • Qwen2.5**

⭐ If you find this project useful, consider starring the repository!

</div>
