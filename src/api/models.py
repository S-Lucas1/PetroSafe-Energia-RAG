"""
PetroSafe Energia - Modelos Pydantic para a API
Sprint 7 - Contratos de request/response
"""

from typing import Optional
from pydantic import BaseModel, Field


# ── Request ────────────────────────────────────────────────
class QueryRequest(BaseModel):
    question: str = Field(..., description="Pergunta em linguagem natural", min_length=3)
    top_k: int    = Field(5, description="Número de documentos de contexto", ge=1, le=20)

    model_config = {"json_schema_extra": {"example": {"question": "Quais falhas BSW foram detectadas?", "top_k": 5}}}


# ── Response /query ────────────────────────────────────────
class SourceInfo(BaseModel):
    id:    str
    title: str
    score: float

class TimingInfo(BaseModel):
    retrieval_ms:  float
    generation_ms: float
    total_ms:      float

class QueryResponse(BaseModel):
    answer:  str
    sources: list[SourceInfo]
    timing:  TimingInfo


# ── Response /metadata/datasets ────────────────────────────
class DatasetInfo(BaseModel):
    nome:      str
    descricao: Optional[str] = None
    dominio:   str
    formato:   Optional[str] = None
    criado_em: Optional[str] = None


# ── Response /metadata/versions ────────────────────────────
class VersionInfo(BaseModel):
    dataset:    str
    versao:     str
    camada:     str
    registros:  Optional[int] = None
    criado_em:  Optional[str] = None


# ── Response /health ───────────────────────────────────────
class HealthResponse(BaseModel):
    status:   str
    services: dict[str, str]


# ── Response /metadata/lineage ─────────────────────────────
class LineageEntry(BaseModel):
    pipeline:              Optional[str] = None
    tipo_pipeline:         Optional[str] = None
    camada_origem:         Optional[str] = None
    camada_destino:        Optional[str] = None
    origem_path:           Optional[str] = None
    destino_path:          Optional[str] = None
    status:                Optional[str] = None
    inicio:                Optional[str] = None
    registros_processados: Optional[int] = None
