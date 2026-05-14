# API Contract — PetroSafe Energia RAG API

**Versão:** 1.0.0  
**Base URL:** `http://localhost:8000`  
**Docs interativos:** `http://localhost:8000/docs`

---

## Endpoints

### POST /query
Consulta RAG em linguagem natural.

**Request:**
```json
{
  "question": "Quais falhas BSW foram detectadas no poço A1?",
  "top_k": 5
}
```

**Response 200:**
```json
{
  "answer": "Com base nos dados do poço A1, foram identificadas falhas do tipo Falha Abrupta na BSW...",
  "sources": [
    {"id": "3W Dataset_classe_1_chunk_0", "title": "Análise de Evento: Falha BSW", "score": 0.9231},
    {"id": "3W Dataset_classe_2_chunk_0", "title": "Análise de Evento: Falha Incipiente na BSW", "score": 0.8754}
  ],
  "timing": {
    "retrieval_ms": 142.3,
    "generation_ms": 4821.7,
    "total_ms": 4964.0
  }
}
```

---

### GET /health
Verifica status de cada serviço da plataforma.

**Response 200:**
```json
{
  "status": "ok",
  "services": {
    "minio": "up",
    "postgres": "up",
    "milvus": "up",
    "ollama": "up"
  }
}
```

---

### GET /metadata/datasets
Lista todos os datasets do catálogo PostgreSQL.

**Response 200:**
```json
[
  {
    "nome": "3W Dataset - Falhas em Poços",
    "descricao": "Dataset de sensores industriais para classificação de falhas",
    "dominio": "falhas_industriais",
    "formato": "csv",
    "criado_em": "2026-04-09T22:11:00"
  }
]
```

---

### GET /metadata/versions
Lista versões dos datasets por camada.

**Response 200:**
```json
[
  {"dataset": "3W Dataset - Falhas em Poços", "versao": "1.0.1", "camada": "gold",   "registros": 9,   "criado_em": "2026-04-09T22:15:07"},
  {"dataset": "3W Dataset - Falhas em Poços", "versao": "1.0.1", "camada": "silver", "registros": 500, "criado_em": "2026-04-09T22:13:38"},
  {"dataset": "3W Dataset - Falhas em Poços", "versao": "1.0.1", "camada": "bronze", "registros": 500, "criado_em": "2026-04-09T22:11:18"}
]
```

---

### GET /metadata/lineage
Retorna linhagem completa de dados (data lineage).

**Response 200:**
```json
[
  {
    "pipeline": "curadoria_silver_gold",
    "tipo_pipeline": "transformacao",
    "camada_origem": "silver",
    "camada_destino": "gold",
    "origem_path": null,
    "destino_path": null,
    "status": "sucesso",
    "inicio": "2026-04-09 22:15:05",
    "registros_processados": 9
  }
]
```

---

## Códigos de Erro

| Código | Significado |
|--------|-------------|
| 200 | Sucesso |
| 400 | Requisição inválida (parâmetros ausentes ou inválidos) |
| 500 | Erro interno (serviço indisponível ou falha no pipeline) |
| 503 | RAG pipeline não inicializado |

---

## Exemplos curl

```bash
# Health check
curl http://localhost:8000/health

# Listar datasets
curl http://localhost:8000/metadata/datasets

# Listar versões
curl http://localhost:8000/metadata/versions

# Linhagem
curl http://localhost:8000/metadata/lineage

# Consulta RAG
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "O que e uma falha BSW?", "top_k": 5}'
```

---

## Iniciar a API

```bash
# Via Makefile
make api

# Via uvicorn direto
source venv/bin/activate
python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Swagger UI: http://localhost:8000/docs
```
