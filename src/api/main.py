"""
PetroSafe Energia — RAG API
Sprint 7 - FastAPI com endpoints de consulta, metadados e saúde

Iniciar: uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
Docs:    http://localhost:8000/docs
"""

import sys
from pathlib import Path

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.api.models import (
    DatasetInfo, HealthResponse, LineageEntry,
    QueryRequest, QueryResponse, SourceInfo, TimingInfo, VersionInfo,
)
from src.pipelines.rag_pipeline import RAGPipeline
from src.utils.config import get_settings
from src.utils.metadata import MetadataClient

# ── App ────────────────────────────────────────────────────
app = FastAPI(
    title="PetroSafe Energia — RAG API",
    description=(
        "Plataforma RAG Enterprise para diagnóstico de falhas em poços de petróleo. "
        "Permite consultas em linguagem natural com rastreabilidade completa via "
        "arquitetura Medallion (Bronze → Silver → Gold) e busca vetorial (Milvus)."
    ),
    version="1.0.0",
    contact={"name": "PetroSafe Energia", "email": "ia@petrosafe.com.br"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Singletons (inicializados no startup) ──────────────────
_rag: RAGPipeline | None = None
_settings = get_settings()


@app.on_event("startup")
async def startup_event():
    global _rag
    _rag = RAGPipeline()


# ── Endpoints: RAG ─────────────────────────────────────────
@app.post(
    "/query",
    response_model=QueryResponse,
    tags=["RAG"],
    summary="Consulta RAG em linguagem natural",
)
async def query_rag(req: QueryRequest):
    """
    Recebe uma pergunta, recupera contexto do Milvus e gera resposta via Ollama (llama3.2:3b).
    """
    if _rag is None:
        raise HTTPException(status_code=503, detail="RAG pipeline não inicializado")
    try:
        result = _rag.query(req.question, top_k=req.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return QueryResponse(
        answer=result["resposta"],
        sources=[
            SourceInfo(id=f["id"], title=f["titulo"], score=f["score"])
            for f in result["fontes"]
        ],
        timing=TimingInfo(
            retrieval_ms=result["tempo_retrieval_ms"],
            generation_ms=result["tempo_geracao_ms"],
            total_ms=result["total_ms"],
        ),
    )


# ── Endpoints: Metadata ────────────────────────────────────
@app.get(
    "/metadata/datasets",
    response_model=list[DatasetInfo],
    tags=["Metadata"],
    summary="Lista datasets do catálogo",
)
async def get_datasets():
    """Retorna todos os datasets registrados no catálogo PostgreSQL."""
    try:
        meta = MetadataClient()
        rows = meta.listar_datasets()
        return [DatasetInfo(**r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/metadata/versions",
    response_model=list[VersionInfo],
    tags=["Metadata"],
    summary="Lista versões dos datasets",
)
async def get_versions():
    """Retorna todas as versões registradas por camada (bronze/silver/gold)."""
    try:
        meta = MetadataClient()
        with meta.Session() as session:
            result = session.execute(text("""
                SELECT d.nome AS dataset, dv.versao, dv.camada,
                       dv.num_registros AS registros,
                       dv.criado_em
                FROM metadata.dataset_versoes dv
                JOIN metadata.datasets d ON dv.dataset_id = d.id
                ORDER BY dv.criado_em DESC
            """))
            rows = result.fetchall()
        return [
            VersionInfo(
                dataset=r[0], versao=r[1], camada=r[2],
                registros=r[3],
                criado_em=r[4].isoformat() if r[4] else None,
            )
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/metadata/lineage",
    response_model=list[LineageEntry],
    tags=["Metadata"],
    summary="Linhagem de dados (data lineage)",
)
async def get_lineage():
    """Retorna a linhagem completa via view vw_linhagem do PostgreSQL."""
    try:
        meta = MetadataClient()
        with meta.Session() as session:
            result = session.execute(text("SELECT * FROM metadata.vw_linhagem ORDER BY inicio DESC LIMIT 50"))
            cols = list(result.keys())
            rows = result.fetchall()
        entries = []
        for row in rows:
            d = dict(zip(cols, row))
            entries.append(LineageEntry(
                pipeline=d.get("pipeline"),
                tipo_pipeline=d.get("tipo_pipeline"),
                camada_origem=d.get("camada_origem"),
                camada_destino=d.get("camada_destino"),
                origem_path=d.get("origem_path"),
                destino_path=d.get("destino_path"),
                status=d.get("status"),
                inicio=str(d["inicio"]) if d.get("inicio") else None,
                registros_processados=d.get("registros_processados"),
            ))
        return entries
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Endpoints: Health ──────────────────────────────────────
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Status dos serviços",
)
async def health_check():
    """Verifica conectividade com MinIO, PostgreSQL, Milvus e Ollama."""
    services: dict[str, str] = {}
    all_ok = True

    # MinIO
    try:
        r = requests.get(f"http://{_settings.minio_endpoint}/minio/health/live", timeout=3)
        services["minio"] = "up" if r.status_code == 200 else "degraded"
    except Exception:
        services["minio"] = "down"
        all_ok = False

    # PostgreSQL
    try:
        meta = MetadataClient()
        with meta.Session() as session:
            session.execute(text("SELECT 1"))
        services["postgres"] = "up"
    except Exception:
        services["postgres"] = "down"
        all_ok = False

    # Milvus
    try:
        from pymilvus import connections, utility
        connections.connect("health_check", host=_settings.milvus_host, port=_settings.milvus_port)
        utility.list_collections()
        services["milvus"] = "up"
    except Exception:
        services["milvus"] = "down"
        all_ok = False

    # Ollama
    try:
        r = requests.get(f"{_settings.ollama_host}/api/tags", timeout=5)
        services["ollama"] = "up" if r.status_code == 200 else "degraded"
    except Exception:
        services["ollama"] = "down"
        all_ok = False

    return HealthResponse(
        status="ok" if all_ok else "degraded",
        services=services,
    )
