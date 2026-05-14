# PETROSAFE ENERGIA — Contexto do Projeto

> Documento de contexto para assistentes de IA (Claude Code, Copilot, etc.)
> Última atualização: Maio 2026

---

## 1. Visão Geral

**Projeto:** Plataforma RAG Enterprise com Governança de Dados (local)
**Disciplina:** Inteligência Artificial — UniFacens
**Professor:** Prof. Msc. Adson Nogueira Alves
**Repositório:** https://github.com/S-Lucas1/PetroSafe-Energia-RAG.git

**Empresa fictícia:** PetroSafe Energia (setor de Óleo & Gás)
**Dataset:** 3W da Petrobras — dados reais de falhas em poços de petróleo (CC BY 4.0)
**Problema de negócio:** Engenheiros de confiabilidade gastam horas buscando informações em planilhas e PDFs para diagnosticar falhas. A plataforma permite consultas em linguagem natural com rastreabilidade completa.

---

## 2. Stack Tecnológica

| Componente | Tecnologia | Porta | Função |
|---|---|---|---|
| Data Lake | MinIO | 9000/9001 | Armazenamento Medallion (Bronze/Silver/Gold) |
| Banco Relacional | PostgreSQL 16 | 5432 | Metadados, catálogo, auditoria |
| Banco Vetorial | Milvus | 19530 | Embeddings e busca por similaridade |
| LLM Local | Ollama (Llama 3.2 3B) | 11434 | Geração de respostas e embeddings |
| Experiment Tracking | MLflow | 5000 | Tracking de modelos e experimentos |
| API | FastAPI | 8000 | Endpoints REST |
| Interface | Gradio | 7860 | Frontend para consultas |
| Orquestração | Docker Compose | — | Containerização |
| Automação | Makefile | — | Comandos padronizados |

**Credenciais padrão (desenvolvimento):**
- MinIO: petrosafe / petrosafe123
- PostgreSQL: petrosafe / petrosafe123 (db: petrosafe)
- MLflow S3: mesmas credenciais do MinIO

---

## 3. Estrutura do Projeto

```
rag-platform/
├── docker-compose.yml          # 7 serviços Docker
├── Dockerfile.mlflow           # Imagem custom do MLflow (com psycopg2)
├── Makefile                    # 30+ comandos padronizados
├── requirements.txt            # Dependências Python
├── .env                        # Variáveis de ambiente
├── .gitignore
│
├── docs/
│   ├── arquitetura.md          # Documentação arquitetural
│   ├── governanca.md           # Política de governança
│   ├── product_backlog.md      # Product Backlog (Scrum)
│   ├── decisoes_tecnicas.md    # Justificativas técnicas
│   ├── modelagem_ml.md         # (Sprint 4) Documentação ML
│   ├── api_contract.md         # (Sprint 7) Contrato da API
│   └── PetroSafe_Entrega_Sprints_1-4.docx
│
├── scripts/
│   └── init-db.sql             # Schema PostgreSQL (metadata + audit)
│
├── src/
│   ├── api/
│   │   ├── main.py             # (Sprint 7) FastAPI endpoints
│   │   └── models.py           # (Sprint 7) Pydantic models
│   ├── pipelines/
│   │   ├── bronze_ingestion.py # Pipeline Bronze
│   │   ├── silver_transform.py # Pipeline Silver
│   │   ├── gold_curate.py      # Pipeline Gold
│   │   ├── embedding_pipeline.py # (Sprint 5) Embeddings → Milvus
│   │   ├── rag_pipeline.py     # (Sprint 6) RAG Core
│   │   └── rag_query.py        # (Sprint 6) CLI interativa
│   ├── models/
│   │   ├── train.py            # (Sprint 4) Treinamento ML
│   │   └── evaluate.py         # (Sprint 4) Avaliação
│   └── utils/
│       ├── config.py           # Pydantic Settings
│       ├── datalake.py         # Cliente MinIO
│       ├── metadata.py         # Cliente PostgreSQL
│       ├── embedding.py        # (Sprint 5) Cliente Ollama embeddings
│       └── milvus_client.py    # (Sprint 5) Cliente Milvus
│
├── data/
│   └── raw/
│       ├── poco_A1_sensores.csv  # CSV sintético (500 registros, 9 colunas)
│       └── poco_tipo*_3w.csv     # CSVs por tipo de falha (3W real)
│
├── artifacts/                  # Artefatos de ML (confusion matrices, reports)
├── tests/
└── frontend/                   # Gradio (Sprint 8)
```

---

## 4. Cronograma e Avaliações

| Avaliação | Data Limite | Sprints Cobertas |
|---|---|---|
| **AC1** | 17/04/2026 | Sprints 1–4 |
| **AC2** | 29/05/2026 | Sprints 5–7 |
| **AF** | 08-12/06/2026 | Sprints 8–12 (pitch de 10 min) |

---

## 5. Sprints — Status

### ✅ Sprint 1 — Definição do Produto
- Domínio: Energia (falhas industriais)
- Empresa: PetroSafe Energia
- Dataset: 3W Petrobras
- 7 RF + 6 RNF documentados
- Papéis Scrum definidos
- Product Backlog: 6 épicos, 27 user stories

### ✅ Sprint 2 — Arquitetura e Infraestrutura
- Docker Compose: 7 serviços com healthchecks
- Makefile: 30+ comandos
- MinIO, PostgreSQL, Milvus, MLflow, Ollama rodando
- Rede isolada: petrosafe-net

### ✅ Sprint 3 — Governança e Medallion
- Buckets bronze/silver/gold com versionamento
- Pipeline Bronze executado (CSV → MinIO)
- Pipeline Silver executado (limpeza → Parquet, qualidade 99.4%)
- Pipeline Gold executado (9 documentos RAG gerados)
- Documentação de governança completa

### ✅ Sprint 4 — Modelagem de Metadados
- Schema PostgreSQL: metadata (7 tabelas) + audit (1 tabela)
- Triggers de auditoria automática
- Views: vw_datasets_ultima_versao, vw_linhagem
- Seeds: 4 domínios, 5 pipelines, 3 datasets
- Cliente Python metadata.py
- Treinamento ML: Logistic Regression, Random Forest, XGBoost
- MLflow experiment: petrosafe-classificacao-falhas (3 runs)

### ✅ Sprint 5 — Pipeline de Embeddings
- nomic-embed-text (768d) via Ollama
- RecursiveCharacterTextSplitter: chunk_size=500, overlap=50
- 9 docs Gold → 33 chunks indexados no Milvus
- Collection petrosafe_documents com índice IVF_FLAT COSINE (nlist=128)
- src/utils/embedding.py — EmbeddingClient com retry/backoff
- src/utils/milvus_client.py — MilvusClient
- src/pipelines/embedding_pipeline.py — pipeline completo

### ✅ Sprint 6 — Construção do RAG Core
- Pipeline completo: query → embedding → Milvus retrieval → prompt → Ollama llama3.2:3b
- Prompt engineering com grounding no contexto
- Resposta estruturada: texto + fontes (id/titulo/score) + tempos
- src/pipelines/rag_pipeline.py — RAGPipeline
- src/pipelines/rag_query.py — CLI interativa (modo argumento + interativo)

### ✅ Sprint 7 — API FastAPI (AC2)
- FastAPI com Swagger UI: http://localhost:8000/docs
- POST /query — RAG em linguagem natural
- GET /health — status de todos os serviços
- GET /metadata/datasets — catálogo PostgreSQL
- GET /metadata/versions — versões por camada
- GET /metadata/lineage — linhagem via vw_linhagem
- src/api/main.py + src/api/models.py
- docs/api_contract.md

### 🔲 Sprint 8 — Interface Gradio
### 🔲 Sprint 9 — MLflow e Avaliação RAG
### 🔲 Sprint 10 — Automação
### 🔲 Sprint 11-12 — Validação e Pitch (AF)

---

## 6. Schema PostgreSQL

### Schema `metadata`
- **dominios** — domínios de dados (falhas, manutenção, docs, sensores)
- **datasets** — catálogo com tags, schema_info JSONB, fonte
- **dataset_versoes** — semver por camada, checksum MD5, métricas qualidade
- **pipelines** — definição com camada_origem/destino
- **pipeline_execucoes** — log com linhagem (data lineage)
- **regras_qualidade** — validações por dataset
- **validacao_resultados** — resultados das validações

### Schema `audit`
- **log** — INSERT/UPDATE/DELETE automático via triggers

---

## 7. Dataset 3W — Estrutura

**Features (entrada):** 7 variáveis numéricas de sensores
| Coluna | Significado |
|---|---|
| P-PDG | Pressão de fundo |
| P-TPT | Pressão do tubing |
| T-TPT | Temperatura do tubing |
| P-MON-CKP | Pressão montante choke |
| T-JUS-CKP | Temperatura jusante choke |
| P-JUS-CKGL | Pressão jusante choke gas lift |
| QGL | Vazão de gas lift |

**Target (saída):** coluna `class` com 9 classes
| Classe | Significado |
|---|---|
| 0 | Normal |
| 1 | Falha Abrupta na BSW |
| 2 | Falha Incipiente na BSW |
| 3 | Instabilidade Severa |
| 4 | Perda de Produção |
| 5 | Rápido Aumento de Produtividade |
| 6 | Rápido Decréscimo de Produtividade |
| 7 | Falha no sensor P-PDG |
| 8 | Falha no sensor P-TPT |

---

## 8. Bugs Conhecidos e Já Corrigidos

| Bug | Fix aplicado |
|---|---|
| `version` obsoleto no compose | Removido |
| `CMD-ARGS` no healthcheck postgres | Trocado para `CMD-SHELL` |
| MLflow sem psycopg2 | Dockerfile.mlflow custom |
| `MINIO_ENDPOINT` com http:// | Removido protocolo |
| Headers HTTP com acentos no MinIO | Sanitização ASCII (unicodedata) |
| `::jsonb` confundindo SQLAlchemy | Usado `CAST(... AS jsonb)` |
| `pd.io.common.BytesIO` deprecated | Usado `io.BytesIO` |
| `to_parquet` sem buffer | Buffer `io.BytesIO()` + `.getvalue()` |
| `metadados_qualidade` como string | Usado `json.dumps()` |
| mlflow 2.x client vs 3.x API | Upgrade mlflow → 3.11.1 |
| pymilvus 2.3.6 usa pkg_resources | Upgrade pymilvus → 2.6.12 |
| train.py usa mlflow.sklearn.log_model | Substituído por pickle + log_artifact |

---

## 9. Comandos Essenciais

```bash
cd ~/rag-platform && source venv/bin/activate
make up              # Subir tudo
make status          # Ver serviços
make down            # Parar tudo
make db-shell        # Entrar no PostgreSQL
make db-check        # Ver tabelas
make help            # Listar comandos
make train           # (Sprint 4) Treinar modelos
make pipeline-all    # Bronze → Silver → Gold
make embed           # (Sprint 5) Gerar embeddings e indexar no Milvus
make rag-query       # (Sprint 6) Consulta RAG interativa
make api             # (Sprint 7) Iniciar API FastAPI
make api-docs        # (Sprint 7) Abrir Swagger UI
```

---

## 10. Critérios de Avaliação do Professor

| Critério | Peso |
|---|---|
| Arquitetura | 20% |
| Governança de dados | 15% |
| Qualidade do RAG | 20% |
| Infraestrutura | 15% |
| Documentação | 15% |
| Apresentação final | 15% |
