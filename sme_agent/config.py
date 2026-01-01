from __future__ import annotations

from dataclasses import dataclass
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    model_name: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.6"))
    embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    secret_key: str = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")

    chroma_dir: str = os.getenv("CHROMA_DIR", "data/chroma")
    knowledge_dir: str = os.getenv("KNOWLEDGE_DIR", "sme_agent/knowledge")
    rebuild_vectorstore: bool = os.getenv("REBUILD_VECTORSTORE", "false").lower() == "true"

    database_url: str = os.getenv("DATABASE_URL", "sqlite:///data/app.db")
    enable_metrics: bool = os.getenv("ENABLE_METRICS", "false").lower() == "true"

    enable_web_sources: bool = os.getenv("ENABLE_WEB_SOURCES", "false").lower() == "true"
    retriever_k: int = int(os.getenv("RETRIEVER_K", "4"))
    retriever_score_threshold: float = float(
        os.getenv("RETRIEVER_SCORE_THRESHOLD", "0.3")
    )
    memory_window: int = int(os.getenv("MEMORY_WINDOW", "4"))

    web_sources: tuple[str, ...] = (
        "https://www.dian.gov.co/tramitesservicios/Paginas/adicionresponsabilidad42obligadollevarcontabilidad.aspx",
        "https://www.mincit.gov.co/servicio-ciudadano/preguntas-frecuentes/mipymes",
        "https://www.mincit.gov.co/minindustria/estrategia-transversal/formalizacion-empresarial",
        "https://www.ccb.org.co/services/create-your-company/establish-your-company/registration",
        "https://www.mincit.gov.co/getattachment/3a4e043d-98d3-40a8-ad9f-4160384088f3/Ley-590-de-2000-Por-la-cual-se-dictan-disposicione.aspx",
        "https://phylo.co/blog/obligaciones-legales-de-una-empresa-en-colombia/",
    )


def require_openai_key(settings: Settings) -> None:
    if not settings.openai_api_key:
        raise RuntimeError(
            "Falta OPENAI_API_KEY. Configurala en el entorno o en un archivo .env."
        )
