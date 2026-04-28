# 🛢️ PetroSafe Energia — RAG Enterprise Platform

> Plataforma de Retrieval-Augmented Generation (RAG) com Governança de Dados para análise inteligente de falhas industriais em poços de petróleo.

---

## 📋 Visão Geral

A **PetroSafe Energia** é uma empresa fictícia do setor de Energia (Óleo & Gás) que enfrenta desafios críticos na análise de falhas em poços de petróleo. Esta plataforma RAG Enterprise permite que engenheiros de confiabilidade consultem, em linguagem natural, dados históricos de falhas, procedimentos operacionais e manuais técnicos — tudo com governança de dados completa.

### Domínio
**Energia — Falhas Industriais em Poços de Petróleo**

### Dataset Base
[3W Dataset (Petrobras)](https://github.com/petrobras/3W) — Dataset público com dados reais de 8 tipos de falhas em poços, incluindo séries temporais de sensores (pressão, temperatura, vazão).

### Problema de Negócio
Engenheiros de confiabilidade da PetroSafe precisam:
1. **Diagnosticar falhas rapidamente** consultando dados históricos de eventos similares
2. **Acessar procedimentos operacionais** relevantes para cada tipo de falha
3. **Correlacionar dados de sensores** com padrões conhecidos de degradação
4. **Tomar decisões baseadas em dados** com rastreabilidade completa

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                        PETROSAFE ENERGIA                        │
│                   RAG Enterprise Platform                       │
├──────────────┬──────────────┬───────────────┬──────────────────┤
│  Camada de   │  Camada de   │   Camada de   │   Camada de      │
│    Dados     │     IA       │    MLOps      │   Aplicação      │
├──────────────┼──────────────┼───────────────┼──────────────────┤
│              │              │               │                  │
│  MinIO       │  Ollama      │  MLflow       │  FastAPI         │
│  ┌────────┐  │  • LLM local │  • Tracking   │  • REST API      │
│  │Bronze  │  │  • Embedding │  • Versão de  │  • Contrato      │
│  │Silver  │  │              │    modelo     │    documentado   │
│  │Gold    │  │  Pipeline    │  • Métricas   │                  │
│  └────────┘  │  RAG:        │               │  Gradio          │
│              │  • Chunking  │               │  • Interface     │
│  PostgreSQL  │  • Embedding │               │    de consulta   │
│  • Metadados │  • Indexação │               │                  │
│  • Versões   │  • Busca     │               │                  │
│  • Auditoria │  • Geração   │               │                  │
│              │              │               │                  │
│  Milvus      │              │               │                  │
│  • Vetores   │              │               │                  │
│  • Índices   │              │               │                  │
└──────────────┴──────────────┴───────────────┴──────────────────┘
│                     Infraestrutura                              │
│  Docker Compose │ Makefile │ Versionamento │ Documentação       │
└─────────────────────────────────────────────────────────────────┘
```

### Componentes

| Componente | Tecnologia | Função |
|---|---|---|
| Data Lake | MinIO | Armazenamento Medallion (Bronze/Silver/Gold) com versionamento |
| Banco Relacional | PostgreSQL 16 | Metadados, catálogo de datasets, auditoria, linhagem |
| Banco Vetorial | Milvus | Armazenamento e busca de embeddings |
| LLM Local | Ollama (Llama 3.2) | Geração de respostas e embeddings |
| Experiment Tracking | MLflow | Versionamento de modelos, tracking de experimentos |
| API | FastAPI | Endpoints REST documentados |
| Interface | Gradio | Frontend para consultas em linguagem natural |
| Orquestração | Docker Compose | Containerização completa |
| Automação | Makefile | Comandos padronizados |

---

## 🚀 Quick Start

### Pré-requisitos
- Docker e Docker Compose v2+
- Python 3.11+
- Make
- 8GB+ RAM disponível

### Setup

```bash
# 1. Clonar repositório
git clone https://github.com/S-Lucas1/PetroSafe-Energia-RAG.git

cd rag-platform

# 2. Copiar variáveis de ambiente
cp .env.example .env

# 3. Setup completo (infra + dependências)
make setup

# 4. Verificar status
make status
```

### Comandos Principais

```bash
make help           # Lista todos os comandos disponíveis
make up             # Inicia todos os serviços
make up-core        # Inicia apenas MinIO + PostgreSQL
make down           # Para todos os serviços
make status         # Status dos serviços
make db-shell       # Abre shell PostgreSQL
make db-check       # Verifica schema do banco
make pipeline-all   # Executa pipeline completo (Bronze → Silver → Gold)
make clean          # Remove containers e volumes
```

### URLs dos Serviços

| Serviço | URL |
|---|---|
| MinIO Console | http://localhost:9001 |
| PostgreSQL | localhost:5432 |
| MLflow | http://localhost:5000 |
| Milvus | localhost:19530 |
| Ollama | http://localhost:11434 |
| API (futuro) | http://localhost:8000 |

---

## 📁 Estrutura do Projeto

```
rag-platform/
├── docker-compose.yml          # Orquestração de serviços
├── Makefile                    # Automação de comandos
├── requirements.txt            # Dependências Python
├── .env                        # Variáveis de ambiente
├── .gitignore
│
├── docs/                       # Documentação
│   ├── arquitetura.md          # Documentação arquitetural
│   ├── governanca.md           # Política de governança de dados
│   ├── product_backlog.md      # Product Backlog (Scrum)
│   └── decisoes_tecnicas.md    # Justificativas técnicas
│
├── scripts/
│   └── init-db.sql             # Schema PostgreSQL (metadados + auditoria)
│
├── src/
│   ├── api/                    # FastAPI endpoints
│   ├── pipelines/
│   │   ├── bronze_ingestion.py # Pipeline Bronze (ingestão)
│   │   ├── silver_transform.py # Pipeline Silver (transformação)
│   │   └── gold_curate.py      # Pipeline Gold (curadoria)
│   ├── models/                 # Modelos de dados
│   └── utils/
│       ├── config.py           # Configurações centralizadas
│       ├── datalake.py         # Cliente MinIO
│       └── metadata.py         # Cliente PostgreSQL (metadados)
│
├── data/                       # Dados locais (não versionado)
│   ├── bronze/
│   ├── silver/
│   └── gold/
│
├── configs/                    # Configurações adicionais
├── tests/                      # Testes automatizados
└── frontend/                   # Interface Gradio
```

---

## 🏛️ Arquitetura Medallion (Governança)

### Bronze — Dados Brutos
- Dados como chegaram da fonte, sem transformação
- CSV, PDF, JSON, TXT originais
- Versionamento habilitado no MinIO
- Metadados registrados (checksum, tamanho, fonte)

### Silver — Dados Limpos
- Remoção de duplicatas
- Padronização de tipos e nomes de colunas
- Tratamento de valores nulos
- Validação de qualidade
- Formato: Parquet (otimizado para consultas)

### Gold — Dados Prontos para Consumo
- Documentos textuais estruturados para RAG
- Estatísticas agregadas por tipo de evento
- Enriquecimento com campos calculados
- Pronto para embedding e indexação no Milvus

---

## 🗄️ Schema de Metadados (PostgreSQL)

### Schema `metadata`
- **dominios** — Domínios de dados (falhas, manutenção, docs técnicos, sensores)
- **datasets** — Catálogo de datasets com tags, schema info e fonte
- **dataset_versoes** — Controle de versões por camada com checksum e métricas de qualidade
- **pipelines** — Definição dos pipelines de transformação
- **pipeline_execucoes** — Log de execuções com linhagem (data lineage)
- **regras_qualidade** — Regras de validação por dataset
- **validacao_resultados** — Resultados das validações

### Schema `audit`
- **log** — Auditoria completa (INSERT/UPDATE/DELETE) com dados anteriores e novos

### Views
- **vw_datasets_ultima_versao** — Visão consolidada com última versão ativa
- **vw_linhagem** — Rastreabilidade completa dos dados (data lineage)

---

## 👥 Equipe

| Papel | Responsabilidade | Integrante 
|---|---| --- |
| Product Owner | Define prioridades e aceita entregas | Lucas Carvalho de Souza - 212169 |
| Scrum Master | Facilita cerimônias e remove impedimentos | Yasmin de Oliveira Teixeira - 212183 |
| Dev Team - Backend | Pipelines, API, infraestrutura | Ricardo Leporo Holtz - 212064, Breno de Pádua Soares - 222500, João Pedro de Oliveira Grangeiro - 222507 |
| Dev Team - Data | Governança, pipelines Medallion, metadados | Matheus Francisco Telini Maldonado - 222253,  Gabriel Amadio de Lima - 190099, Felipe Bettoni - 214365, | 
| Dev Team - IA | RAG pipeline, embeddings, LLM | Lucas Miranda - 223350, Pedro Henrique Fescina Almeida - 223348, Guilherme Grossi de Almeida - 222707, Sergio Samuel Godinho Sandes - 211989 |

---

## 📅 Sprints ( Separado por Entrega)

| Sprint | Foco | Status |
|---|---|---|
| AC1 - Sprint 1 | Definição do Produto | ✅ Concluída |
| AC1 - Sprint 2 | Arquitetura e Infraestrutura Base | ✅ Concluída |
| AC1 - Sprint 3 | Governança e Medallion | ✅ Concluída |
| AC1 - Sprint 4 | Modelagem e Treinamento de Modelos (ML + MLflow) | ✅ Concluída |
| AC2 - Sprint 5 | Pipeline de Embeddings | Em Andamento |
| AC2 - Sprint 6 | Construção do RAG Core | Não Iniciada |
| AC2 - Sprint 7 | API | Não Iniciada |
| AF - Sprint 8 | Interface | Não Iniciada |
| AF - Sprint 9 | MLflow e Avaliação | Não Iniciada |
| AF - Sprint 10 | Automação | Não Iniciada |
| AF - Sprint 11 | Validação, Avaliação e Preparação do Pitch | Não Iniciada |
| AF - Sprint 12 | Validação, Avaliação e Preparação do Pitch | Não Iniciada |

---

## 📄 Licença

Projeto acadêmico — uso educacional.

Dataset 3W: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — Petrobras.
