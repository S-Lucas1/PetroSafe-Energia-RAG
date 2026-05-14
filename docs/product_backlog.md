# 📋 Product Backlog — PetroSafe Energia

> Plataforma RAG Enterprise com Governança de Dados
> Última atualização: Sprint 7 (AC2)

---

## Visão do Produto

**Para** engenheiros de confiabilidade da PetroSafe Energia  
**Que** precisam diagnosticar falhas em poços de petróleo rapidamente  
**O** PetroSafe RAG é uma plataforma de consulta inteligente  
**Que** permite buscar informações em linguagem natural sobre dados históricos de falhas, procedimentos e manuais técnicos  
**Diferente de** buscas manuais em planilhas e documentos  
**Nosso produto** oferece respostas contextualizadas com rastreabilidade de dados e governança completa

---

## Épicos

| ID | Épico | Descrição |
|----|-------|-----------|
| E1 | Infraestrutura | Setup Docker Compose, MinIO, PostgreSQL, Milvus |
| E2 | Governança de Dados | Arquitetura Medallion, versionamento, auditoria |
| E3 | Pipeline RAG | Chunking, embedding, indexação e recuperação |
| E4 | LLM e Geração | Integração Ollama, prompt engineering, geração |
| E5 | API e Interface | FastAPI, documentação, Gradio frontend |
| E6 | MLOps | MLflow, tracking de experimentos, métricas |

---

## Sprint 1 — Definição do Produto ✅

| ID | User Story | Prioridade | Pontos | Status |
|----|-----------|-----------|--------|--------|
| US01 | Como PO, quero definir o domínio do projeto para alinhar o time | Must | 2 | ✅ Done |
| US02 | Como PO, quero definir a empresa fictícia e o problema de negócio | Must | 3 | ✅ Done |
| US03 | Como PO, quero levantar os requisitos funcionais e não-funcionais | Must | 5 | ✅ Done |
| US04 | Como SM, quero definir os papéis Scrum do time | Must | 2 | ✅ Done |
| US05 | Como PO, quero criar o Product Backlog inicial priorizado | Must | 3 | ✅ Done |
| US06 | Como time, quero escolher o dataset público base (3W Petrobras) | Must | 3 | ✅ Done |

**Velocity Sprint 1:** 18 pontos

### Definições Sprint 1

**Domínio:** Energia — Falhas Industriais em Poços de Petróleo  
**Empresa Fictícia:** PetroSafe Energia  
**Dataset:** 3W Dataset (Petrobras) — dados reais de 8 tipos de falhas em poços  

**Requisitos Funcionais:**
- RF01: Ingestão de dados com arquitetura Medallion (Bronze/Silver/Gold)
- RF02: Versionamento de datasets no Data Lake
- RF03: Catálogo de metadados com auditoria
- RF04: Pipeline RAG funcional ponta a ponta
- RF05: Consulta em linguagem natural via API
- RF06: Interface web para consulta e visualização
- RF07: Tracking de experimentos com MLflow

**Requisitos Não-Funcionais:**
- RNF01: Toda infraestrutura containerizada (Docker Compose)
- RNF02: Automação via Makefile
- RNF03: API documentada com contrato OpenAPI
- RNF04: Documentação arquitetural completa
- RNF05: LLM local (sem dependência de APIs externas)
- RNF06: Dados versionados com rastreabilidade

---

## Sprint 2 — Arquitetura e Infraestrutura Base ✅

| ID | User Story | Prioridade | Pontos | Status |
|----|-----------|-----------|--------|--------|
| US07 | Como dev, quero o diagrama arquitetural do sistema para guiar o desenvolvimento | Must | 5 | ✅ Done |
| US08 | Como dev, quero um Docker Compose funcional com MinIO e PostgreSQL | Must | 8 | ✅ Done |
| US09 | Como dev, quero um Makefile com comandos padronizados | Must | 5 | ✅ Done |
| US10 | Como dev, quero o Milvus configurado no Docker Compose | Should | 5 | ✅ Done |
| US11 | Como dev, quero variáveis de ambiente centralizadas (.env) | Must | 2 | ✅ Done |
| US12 | Como dev, quero health checks em todos os serviços | Should | 3 | ✅ Done |

**Velocity Sprint 2:** 28 pontos

### Entregáveis Sprint 2
- `docker-compose.yml` com MinIO, PostgreSQL, Milvus, MLflow, Ollama
- `Makefile` com 25+ comandos padronizados
- `.env` com configurações centralizadas
- Health checks em todos os serviços
- Rede Docker isolada (`petrosafe-net`)

---

## Sprint 3 — Governança e Medallion ✅

| ID | User Story | Prioridade | Pontos | Status |
|----|-----------|-----------|--------|--------|
| US13 | Como eng. dados, quero buckets Bronze/Silver/Gold com versionamento no MinIO | Must | 5 | ✅ Done |
| US14 | Como eng. dados, quero um pipeline de ingestão Bronze (dados brutos) | Must | 8 | ✅ Done |
| US15 | Como eng. dados, quero um pipeline Silver (limpeza e padronização) | Must | 8 | ✅ Done |
| US16 | Como eng. dados, quero um pipeline Gold (curadoria para RAG) | Must | 8 | ✅ Done |
| US17 | Como eng. dados, quero documentação de governança de dados | Must | 3 | ✅ Done |
| US18 | Como eng. dados, quero checksum MD5 em todos os uploads | Should | 2 | ✅ Done |
| US19 | Como eng. dados, quero metadados automáticos em cada upload | Should | 3 | ✅ Done |

**Velocity Sprint 3:** 37 pontos

### Entregáveis Sprint 3
- Pipeline Bronze: `src/pipelines/bronze_ingestion.py`
- Pipeline Silver: `src/pipelines/silver_transform.py`
- Pipeline Gold: `src/pipelines/gold_curate.py`
- Cliente MinIO: `src/utils/datalake.py`
- Buckets com versionamento habilitado
- Documentação de governança

---

## Sprint 4 — Modelagem de Metadados ✅

| ID | User Story | Prioridade | Pontos | Status |
|----|-----------|-----------|--------|--------|
| US20 | Como DBA, quero schema PostgreSQL com catálogo de datasets | Must | 8 | ✅ Done |
| US21 | Como DBA, quero controle de versões de datasets no banco | Must | 5 | ✅ Done |
| US22 | Como DBA, quero tabela de pipelines e execuções (linhagem) | Must | 5 | ✅ Done |
| US23 | Como DBA, quero sistema de auditoria com triggers automáticos | Must | 5 | ✅ Done |
| US24 | Como DBA, quero views de consulta (última versão, linhagem) | Should | 3 | ✅ Done |
| US25 | Como DBA, quero dados seed iniciais (domínios, pipelines, datasets) | Should | 3 | ✅ Done |
| US26 | Como dev, quero cliente Python para operações de metadados | Must | 5 | ✅ Done |
| US27 | Como DBA, quero regras de qualidade e validação no schema | Should | 3 | ✅ Done |

**Velocity Sprint 4:** 37 pontos

### Entregáveis Sprint 4
- Schema `metadata` com 7 tabelas
- Schema `audit` com log completo
- Triggers de auditoria automática
- Triggers de atualização de timestamp
- 2 views (última versão, linhagem)
- Dados seed (domínios, pipelines, datasets 3W)
- Cliente Python: `src/utils/metadata.py`

---

## Sprint 5 — Pipeline de Embeddings ✅

| ID | User Story | Prioridade | Pontos | Status |
|----|-----------|-----------|--------|--------|
| US28 | Como eng. IA, quero pipeline de chunking de documentos Gold para chunks de 500 tokens | Must | 8 | ✅ Done |
| US29 | Como eng. IA, quero geração de embeddings com Ollama (nomic-embed-text 768d) | Must | 8 | ✅ Done |
| US30 | Como eng. IA, quero indexação de embeddings no Milvus com índice IVF_FLAT COSINE | Must | 5 | ✅ Done |
| US31 | Como eng. IA, quero retry com backoff no cliente de embeddings | Should | 3 | ✅ Done |

**Velocity Sprint 5:** 24 pontos

### Entregáveis Sprint 5
- `src/utils/embedding.py` — cliente Ollama nomic-embed-text (768d)
- `src/utils/milvus_client.py` — cliente Milvus com collection `petrosafe_documents`
- `src/pipelines/embedding_pipeline.py` — Gold → chunks → embeddings → Milvus
- 33 chunks indexados de 9 documentos RAG
- Busca por similaridade testada (COSINE, IVF_FLAT, nlist=128)

---

## Sprint 6 — Construção do RAG Core ✅

| ID | User Story | Prioridade | Pontos | Status |
|----|-----------|-----------|--------|--------|
| US32 | Como eng. IA, quero pipeline de retrieval vetorial (top_k documentos similares) | Must | 8 | ✅ Done |
| US33 | Como eng. IA, quero integração com Ollama llama3.2:3b para geração de respostas | Must | 8 | ✅ Done |
| US34 | Como eng. IA, quero prompt engineering com contexto e instrução de grounding | Must | 5 | ✅ Done |
| US35 | Como eng. IA, quero CLI interativa para consultas RAG com tempos de resposta | Should | 3 | ✅ Done |

**Velocity Sprint 6:** 24 pontos

### Entregáveis Sprint 6
- `src/pipelines/rag_pipeline.py` — query → embedding → Milvus → prompt → Ollama
- `src/pipelines/rag_query.py` — CLI com modo argumento e modo interativo
- Resposta estruturada: texto + fontes + tempos (retrieval_ms, geração_ms)
- Template de prompt com grounding no contexto

---

## Sprint 7 — API FastAPI ✅

| ID | User Story | Prioridade | Pontos | Status |
|----|-----------|-----------|--------|--------|
| US36 | Como dev, quero endpoint POST /query que chama o RAG pipeline | Must | 8 | ✅ Done |
| US37 | Como dev, quero endpoints GET /metadata/* para catálogo e linhagem | Must | 5 | ✅ Done |
| US38 | Como dev, quero endpoint GET /health verificando todos os serviços | Must | 3 | ✅ Done |
| US39 | Como dev, quero Swagger UI automático com todos os endpoints documentados | Must | 2 | ✅ Done |
| US40 | Como dev, quero CORS habilitado na API | Should | 1 | ✅ Done |

**Velocity Sprint 7:** 19 pontos

### Entregáveis Sprint 7
- `src/api/main.py` — FastAPI com 5 endpoints + CORS + Swagger
- `src/api/models.py` — modelos Pydantic de request/response
- `docs/api_contract.md` — contrato completo com exemplos curl
- Swagger UI: http://localhost:8000/docs

---

## Backlog Futuro (Sprints 8+)

| ID | User Story | Épico | Prioridade | Pontos |
|----|-----------|-------|-----------|--------|
| US41 | Como usuário, quero interface Gradio para consultas visuais | E5 | Must | 5 |
| US42 | Como eng. MLOps, quero tracking de avaliação do RAG no MLflow | E6 | Should | 5 |
| US43 | Como PO, quero demonstração final ponta a ponta para o professor | — | Must | 3 |

---

## Métricas do Projeto

| Métrica | Sprint 1 | Sprint 2 | Sprint 3 | Sprint 4 | Sprint 5 | Sprint 6 | Sprint 7 | Total |
|---------|----------|----------|----------|----------|----------|----------|----------|-------|
| Pontos Planejados | 18 | 28 | 37 | 37 | 24 | 24 | 19 | 187 |
| Pontos Entregues | 18 | 28 | 37 | 37 | 24 | 24 | 19 | 187 |
| User Stories | 6 | 6 | 7 | 8 | 4 | 4 | 5 | 40 |
| Velocity Média | — | — | — | — | — | — | — | 27 |
