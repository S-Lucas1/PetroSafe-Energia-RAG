# 📐 Documentação Arquitetural — PetroSafe Energia

> RAG Enterprise Platform com Governança de Dados

---

## 1. Visão Geral da Arquitetura

A plataforma PetroSafe é organizada em 4 camadas + infraestrutura:

```
┌───────────────────────────────────────────────────────────────────┐
│                      CAMADA DE APLICAÇÃO                          │
│                                                                   │
│   ┌──────────┐    ┌──────────┐                                   │
│   │ FastAPI   │    │  Gradio  │                                   │
│   │ (REST)    │◄──►│  (UI)    │                                   │
│   └─────┬────┘    └──────────┘                                   │
│         │                                                         │
├─────────┼─────────────────────────────────────────────────────────┤
│         │          CAMADA DE IA                                   │
│         ▼                                                         │
│   ┌──────────┐    ┌──────────────────────────────────┐           │
│   │ Ollama   │    │     Pipeline RAG                  │           │
│   │ LLM +    │◄──►│  Chunking → Embedding → Indexação │           │
│   │ Embedding│    │  Recuperação → Prompt → Geração   │           │
│   └──────────┘    └──────────────────────────────────┘           │
│                                                                   │
├───────────────────────────────────────────────────────────────────┤
│                      CAMADA DE DADOS                              │
│                                                                   │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│   │   MinIO       │  │  PostgreSQL  │  │   Milvus     │          │
│   │  Data Lake    │  │  Metadados   │  │  Vetorial    │          │
│   │              │  │              │  │              │          │
│   │ ┌──────────┐ │  │ metadata.*   │  │  Embeddings  │          │
│   │ │  Bronze  │ │  │ audit.*      │  │  Índices     │          │
│   │ │  Silver  │ │  │              │  │              │          │
│   │ │  Gold    │ │  │              │  │              │          │
│   │ └──────────┘ │  │              │  │              │          │
│   └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
├───────────────────────────────────────────────────────────────────┤
│                     CAMADA DE MLOps                                │
│                                                                   │
│   ┌──────────────────────────────────────────────────────┐       │
│   │  MLflow                                               │       │
│   │  • Tracking de Experimentos                           │       │
│   │  • Model Registry                                     │       │
│   │  • Backend: PostgreSQL │ Artifacts: MinIO (Gold)      │       │
│   └──────────────────────────────────────────────────────┘       │
│                                                                   │
├───────────────────────────────────────────────────────────────────┤
│                     INFRAESTRUTURA                                │
│                                                                   │
│   Docker Compose │ Makefile │ .env │ Healthchecks │ Rede Isolada │
└───────────────────────────────────────────────────────────────────┘
```

---

## 2. Diagrama de Fluxo de Dados

```
                    ┌─────────────┐
                    │  Fontes de  │
                    │   Dados     │
                    │ (3W, PDFs,  │
                    │  Manuais)   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   BRONZE    │ ← Dados brutos, sem transformação
                    │   (MinIO)   │   Versionamento habilitado
                    └──────┬──────┘
                           │ Pipeline Silver
                           │ (limpeza, padronização)
                    ┌──────▼──────┐
                    │   SILVER    │ ← Dados limpos em Parquet
                    │   (MinIO)   │   Score de qualidade calculado
                    └──────┬──────┘
                           │ Pipeline Gold
                           │ (enriquecimento, docs RAG)
                    ┌──────▼──────┐
                    │    GOLD     │ ← Documentos prontos para RAG
                    │   (MinIO)   │   JSON estruturado
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼──────┐  ┌─▼──────┐  ┌─▼──────────┐
       │  Chunking   │  │MLflow  │  │ PostgreSQL  │
       │  (textos)   │  │Tracking│  │ (metadados  │
       └──────┬──────┘  └────────┘  │  linhagem)  │
              │                      └─────────────┘
       ┌──────▼──────┐
       │  Embedding  │ ← Ollama (nomic-embed-text)
       │  (vetores)  │
       └──────┬──────┘
              │
       ┌──────▼──────┐
       │   Milvus    │ ← Indexação vetorial
       │  (índices)  │
       └──────┬──────┘
              │
       ┌──────▼──────────────────┐
       │    Pipeline RAG         │
       │                         │
       │  Query → Embedding      │
       │  → Busca Milvus         │
       │  → Contexto + Prompt    │
       │  → Ollama (Llama 3.2)   │
       │  → Resposta             │
       └──────┬──────────────────┘
              │
       ┌──────▼──────┐
       │  FastAPI /   │
       │  Gradio      │ ← Interface do usuário
       └─────────────┘
```

---

## 3. Diagrama de Componentes Docker

```
┌─ docker-compose.yml ──────────────────────────────────────────────┐
│                                                                    │
│  ┌─────────────────┐    ┌──────────────────┐                     │
│  │ petrosafe-minio  │    │ petrosafe-postgres│                     │
│  │ :9000 / :9001    │    │ :5432             │                     │
│  │ Data Lake        │    │ Metadados         │                     │
│  └────────┬────────┘    └────────┬─────────┘                     │
│           │                       │                                │
│  ┌────────▼────────┐             │                                │
│  │ minio-init      │             │                                │
│  │ (cria buckets)  │             │                                │
│  └─────────────────┘             │                                │
│                                   │                                │
│  ┌─────────────────┐    ┌───────▼──────────┐                     │
│  │ petrosafe-milvus │    │ petrosafe-mlflow  │                     │
│  │ :19530 / :9091   │    │ :5000             │                     │
│  │  ┌─────────┐    │    │ backend→postgres  │                     │
│  │  │  etcd   │    │    │ artifacts→minio   │                     │
│  │  │  minio  │    │    └──────────────────┘                     │
│  │  └─────────┘    │                                              │
│  └─────────────────┘                                              │
│                                                                    │
│  ┌─────────────────┐                                              │
│  │ petrosafe-ollama │                                              │
│  │ :11434           │                                              │
│  │ Llama 3.2 + emb │                                              │
│  └─────────────────┘                                              │
│                                                                    │
│  Network: petrosafe-net (bridge)                                  │
└────────────────────────────────────────────────────────────────────┘
```

---

## 4. Modelo de Dados (PostgreSQL)

### Schema `metadata`

```
┌─────────────────────┐       ┌──────────────────────────┐
│   dominios          │       │   datasets                │
├─────────────────────┤       ├──────────────────────────┤
│ id (PK, UUID)       │◄──┐  │ id (PK, UUID)            │
│ nome                │   └──│ dominio_id (FK)           │
│ descricao           │      │ nome                      │
│ responsavel         │      │ descricao                 │
│ criado_em           │      │ formato_origem            │
│ atualizado_em       │      │ fonte                     │
└─────────────────────┘      │ licenca                   │
                              │ tags (TEXT[])             │
                              │ schema_info (JSONB)       │
                              │ criado_em                 │
                              └────────────┬──────────────┘
                                           │
                              ┌────────────▼──────────────┐
                              │   dataset_versoes          │
                              ├───────────────────────────┤
                              │ id (PK, UUID)              │
                              │ dataset_id (FK)            │
                              │ versao                     │
                              │ camada (bronze/silver/gold)│
                              │ caminho_minio              │
                              │ minio_version_id           │
                              │ tamanho_bytes              │
                              │ num_registros              │
                              │ checksum_md5               │
                              │ status                     │
                              │ metadados_qualidade (JSONB)│
                              └───────────────────────────┘

┌─────────────────────┐       ┌──────────────────────────┐
│   pipelines         │       │   pipeline_execucoes      │
├─────────────────────┤       ├──────────────────────────┤
│ id (PK, UUID)       │◄─────│ pipeline_id (FK)          │
│ nome                │      │ id (PK, UUID)             │
│ descricao           │      │ dataset_versao_origem (FK)│
│ tipo                │      │ dataset_versao_destino(FK)│
│ camada_origem       │      │ status                    │
│ camada_destino      │      │ inicio / fim              │
│ script_path         │      │ duracao_segundos          │
│ parametros (JSONB)  │      │ registros_processados     │
└─────────────────────┘      │ registros_rejeitados      │
                              │ erro_mensagem             │
                              │ metricas (JSONB)          │
                              └──────────────────────────┘

┌─────────────────────┐       ┌──────────────────────────┐
│ regras_qualidade    │       │ validacao_resultados      │
├─────────────────────┤       ├──────────────────────────┤
│ id (PK, UUID)       │◄─────│ regra_id (FK)             │
│ dataset_id (FK)     │      │ dataset_versao_id (FK)    │
│ nome                │      │ passou (BOOLEAN)          │
│ tipo                │      │ total_registros           │
│ expressao           │      │ registros_validos         │
│ severidade          │      │ percentual_conformidade   │
└─────────────────────┘      └──────────────────────────┘
```

### Schema `audit`

```
┌───────────────────────────┐
│   audit.log               │
├───────────────────────────┤
│ id (PK, BIGSERIAL)        │
│ tabela                    │
│ operacao (INS/UPD/DEL)    │
│ registro_id               │
│ dados_anteriores (JSONB)  │
│ dados_novos (JSONB)       │
│ usuario                   │
│ executado_em              │
└───────────────────────────┘
```

---

## 5. Portas e Serviços

| Serviço | Porta(s) | Protocolo |
|---------|----------|-----------|
| MinIO (API) | 9000 | HTTP/S3 |
| MinIO (Console) | 9001 | HTTP |
| PostgreSQL | 5432 | TCP |
| Milvus (gRPC) | 19530 | gRPC |
| Milvus (Health) | 9091 | HTTP |
| MLflow | 5000 | HTTP |
| Ollama | 11434 | HTTP |
| FastAPI (futuro) | 8000 | HTTP |
| Gradio (futuro) | 7860 | HTTP |

---

## 6. Decisões Arquiteturais (ADRs)

| # | Decisão | Justificativa |
|---|---------|---------------|
| ADR-001 | MinIO para Data Lake | Compatível S3, self-hosted, versionamento nativo |
| ADR-002 | PostgreSQL para metadados | JSONB, triggers, integração MLflow |
| ADR-003 | Milvus para vetores | Performance, escalável, hybrid search |
| ADR-004 | Ollama para LLM | Local, privacidade, custo zero |
| ADR-005 | Medallion (3 camadas) | Rastreabilidade, padrão de mercado |
| ADR-006 | Parquet na Silver | Colunar, compressão, tipagem |
| ADR-007 | Docker Compose | Reprodutibilidade, simplicidade |

Detalhes completos em `docs/decisoes_tecnicas.md`.
