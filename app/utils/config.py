# app/utils/config.py
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Philips Product Knowledge AI Agent")

    # Embedding Model
    embedding_model: str = os.getenv(
        "EMBEDDING_MODEL",
        "BAAI/bge-base-en-v1.5"
    )

    # -----------------------------
    # LLM Configuration
    # -----------------------------
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")  # openai | ollama

    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5")

    # Ollama (optional)
    llm_model: str = os.getenv(
        "LLM_MODEL",
        "Qwen/Qwen2.5-7B"
    )
    ollama_model_tag: str = os.getenv(
        "OLLAMA_MODEL_TAG",
        "qwen2.5:7b"
    )
    ollama_host: str = os.getenv(
        "OLLAMA_HOST",
        "http://localhost:11434"
    )

    log_dir: str = os.getenv("LOG_DIR", "logs")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # -----------------------------
    # Retrieval
    # -----------------------------
    vector_db: str = os.getenv("VECTOR_DB", "data/vector_db")
    data_directory: str = os.getenv("DATA_DIRECTORY", "data/users")

    top_k: int = int(os.getenv("TOP_K", "5"))
    similarity_threshold: float = float(
        os.getenv("SIMILARITY_THRESHOLD", "0.5")
    )
    max_context_chunks: int = int(
        os.getenv("MAX_CONTEXT_CHUNKS", "5")
    )

    # Device
    device: str = os.getenv("DEVICE", "cpu")


settings = Settings()
