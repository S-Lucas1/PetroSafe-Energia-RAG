"""
PetroSafe Energia - RAG Pipeline Core
Sprint 6 - Retrieval-Augmented Generation
"""

import sys
import time
from pathlib import Path

import requests
import structlog

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.config import get_settings
from src.utils.embedding import EmbeddingClient
from src.utils.milvus_client import MilvusClient

logger = structlog.get_logger()

PROMPT_TEMPLATE = """\
Você é o assistente técnico da PetroSafe Energia, especializado em falhas em poços de petróleo.
Responda APENAS com base no contexto fornecido. Se a informação não estiver no contexto, diga que não tem dados suficientes.

CONTEXTO:
{contexto}

PERGUNTA: {pergunta}

RESPOSTA:"""


class RAGPipeline:
    """
    Pipeline Sprint 6: query → embedding → Milvus retrieval → prompt → Ollama LLM.
    """

    def __init__(self):
        settings = get_settings()
        self.embedder    = EmbeddingClient(host=settings.ollama_host, model=settings.ollama_embedding_model)
        self.milvus      = MilvusClient(host=settings.milvus_host, port=settings.milvus_port)
        self.ollama_host = settings.ollama_host
        self.llm_model   = settings.ollama_model
        self.milvus.connect()

    def query(self, pergunta: str, top_k: int = 5) -> dict:
        """
        Executa o pipeline RAG completo e retorna resposta estruturada.
        """
        # ── Retrieval ──────────────────────────────────────────────
        t0        = time.time()
        query_emb = self.embedder.generate(pergunta)
        results   = self.milvus.search(query_emb, top_k=top_k)
        t_retrieval = (time.time() - t0) * 1000

        fontes: list[dict] = []
        contexto_parts: list[str] = []
        for hits in results:
            for hit in hits:
                texto  = hit.entity.get("texto", "")
                titulo = hit.entity.get("titulo", "")
                doc_id = hit.entity.get("id", "")
                score  = float(hit.score)
                contexto_parts.append(f"[{titulo}]\n{texto}")
                fontes.append({"id": doc_id, "titulo": titulo, "score": score})

        contexto = "\n\n---\n\n".join(contexto_parts)
        prompt   = PROMPT_TEMPLATE.format(contexto=contexto, pergunta=pergunta)

        # ── Geração LLM ────────────────────────────────────────────
        t1   = time.time()
        resp = requests.post(
            f"{self.ollama_host}/api/generate",
            json={
                "model": self.llm_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_thread": 12,
                    "num_ctx": 1024,
                    "num_predict": 200,
                },
            },
            timeout=600,
        )
        resp.raise_for_status()
        resposta    = resp.json()["response"]
        t_geracao   = (time.time() - t1) * 1000

        logger.info(
            "rag_query_concluida",
            pergunta=pergunta[:60],
            fontes=len(fontes),
            retrieval_ms=round(t_retrieval),
            geracao_ms=round(t_geracao),
        )

        return {
            "resposta":          resposta,
            "fontes":            fontes,
            "tempo_retrieval_ms": round(t_retrieval, 1),
            "tempo_geracao_ms":   round(t_geracao, 1),
            "total_ms":           round(t_retrieval + t_geracao, 1),
        }
