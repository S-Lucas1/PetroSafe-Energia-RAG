# 📋 Product Backlog — PetroSafe Energia

> Plataforma RAG Enterprise com Governança de Dados
> Última atualização: Sprint 4

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

## Backlog Futuro (Sprints 5+)

| ID | User Story | Épico | Prioridade | Pontos |
|----|-----------|-------|-----------|--------|
| US28 | Como eng. IA, quero pipeline de chunking de documentos | E3 | Must | 8 |
| US29 | Como eng. IA, quero geração de embeddings com Ollama | E3 | Must | 8 |
| US30 | Como eng. IA, quero indexação de embeddings no Milvus | E3 | Must | 5 |
| US31 | Como eng. IA, quero pipeline de busca vetorial (retrieval) | E3 | Must | 8 |
| US32 | Como eng. IA, quero integração com Ollama para geração de respostas | E4 | Must | 8 |
| US33 | Como eng. IA, quero prompt engineering otimizado para o domínio | E4 | Should | 5 |
| US34 | Como dev, quero API FastAPI com endpoints de consulta RAG | E5 | Must | 8 |
| US35 | Como dev, quero documentação OpenAPI da API | E5 | Must | 3 |
| US36 | Como dev, quero interface Gradio para consultas | E5 | Must | 5 |
| US37 | Como eng. MLOps, quero tracking de experimentos RAG no MLflow | E6 | Should | 5 |
| US38 | Como eng. MLOps, quero métricas de avaliação do RAG | E6 | Should | 5 |
| US39 | Como PO, quero demonstração final ponta a ponta | — | Must | 3 |

---

## Métricas do Projeto

| Métrica | Sprint 1 | Sprint 2 | Sprint 3 | Sprint 4 | Total |
|---------|----------|----------|----------|----------|-------|
| Pontos Planejados | 18 | 28 | 37 | 37 | 120 |
| Pontos Entregues | 18 | 28 | 37 | 37 | 120 |
| User Stories | 6 | 6 | 7 | 8 | 27 |
| Velocity Média | — | — | — | — | 30 |
