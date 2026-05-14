# ============================================================
# PetroSafe Energia - RAG Enterprise Platform
# Makefile - Comandos Padronizados
# ============================================================

.PHONY: help up down restart logs status clean \
        init-buckets db-shell db-migrate \
        bronze silver gold pipeline-all \
        train evaluate train-all \
        pull-model pull-embedding \
        embed rag-query api api-docs \
        test lint format

# ── Variáveis ──────────────────────────────────────────────
COMPOSE = docker compose
PYTHON = python3
ENV_FILE = .env

# Cores para output
GREEN  = \033[0;32m
YELLOW = \033[0;33m
RED    = \033[0;31m
CYAN   = \033[0;36m
NC     = \033[0m

# ── Help ───────────────────────────────────────────────────
help: ## Mostra esta ajuda
	@echo ""
	@echo "$(CYAN)╔══════════════════════════════════════════════════╗$(NC)"
	@echo "$(CYAN)║   PetroSafe Energia - RAG Enterprise Platform   ║$(NC)"
	@echo "$(CYAN)╚══════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ── Infraestrutura ─────────────────────────────────────────
up: ## Inicia todos os serviços
	@echo "$(CYAN)▶ Iniciando infraestrutura PetroSafe...$(NC)"
	$(COMPOSE) --env-file $(ENV_FILE) up -d
	@echo "$(GREEN)✓ Serviços iniciados$(NC)"
	@$(MAKE) status

up-core: ## Inicia apenas MinIO + PostgreSQL (Sprint 2)
	@echo "$(CYAN)▶ Iniciando serviços core...$(NC)"
	$(COMPOSE) --env-file $(ENV_FILE) up -d minio minio-init postgres
	@echo "$(GREEN)✓ MinIO e PostgreSQL iniciados$(NC)"

up-vector: ## Inicia Milvus (banco vetorial)
	@echo "$(CYAN)▶ Iniciando Milvus...$(NC)"
	$(COMPOSE) --env-file $(ENV_FILE) up -d milvus-etcd milvus-minio milvus
	@echo "$(GREEN)✓ Milvus iniciado$(NC)"

up-mlops: ## Inicia MLflow
	@echo "$(CYAN)▶ Iniciando MLflow...$(NC)"
	$(COMPOSE) --env-file $(ENV_FILE) up -d mlflow
	@echo "$(GREEN)✓ MLflow iniciado na porta 5000$(NC)"

up-ollama: ## Inicia Ollama (LLM local)
	@echo "$(CYAN)▶ Iniciando Ollama...$(NC)"
	$(COMPOSE) --env-file $(ENV_FILE) up -d ollama
	@echo "$(GREEN)✓ Ollama iniciado$(NC)"

down: ## Para todos os serviços
	@echo "$(YELLOW)▶ Parando serviços...$(NC)"
	$(COMPOSE) down
	@echo "$(GREEN)✓ Serviços parados$(NC)"

restart: down up ## Reinicia todos os serviços

status: ## Status dos serviços
	@echo "$(CYAN)── Status dos Serviços ──$(NC)"
	@$(COMPOSE) ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

logs: ## Mostra logs de todos os serviços
	$(COMPOSE) logs -f --tail=50

logs-minio: ## Logs do MinIO
	$(COMPOSE) logs -f minio

logs-postgres: ## Logs do PostgreSQL
	$(COMPOSE) logs -f postgres

# ── Data Lake (MinIO) ─────────────────────────────────────
init-buckets: ## Cria buckets Medallion no MinIO
	@echo "$(CYAN)▶ Criando buckets Medallion...$(NC)"
	$(COMPOSE) run --rm minio-init
	@echo "$(GREEN)✓ Buckets bronze/silver/gold criados$(NC)"

# ── Banco de Dados ─────────────────────────────────────────
db-shell: ## Abre shell do PostgreSQL
	@echo "$(CYAN)▶ Conectando ao PostgreSQL...$(NC)"
	$(COMPOSE) exec postgres psql -U petrosafe -d petrosafe

db-migrate: ## Aplica migrations no PostgreSQL
	@echo "$(CYAN)▶ Aplicando migrations...$(NC)"
	$(COMPOSE) exec postgres psql -U petrosafe -d petrosafe -f /docker-entrypoint-initdb.d/01-init.sql
	@echo "$(GREEN)✓ Migrations aplicadas$(NC)"

db-check: ## Verifica schema do banco
	@echo "$(CYAN)── Tabelas no Schema metadata ──$(NC)"
	@$(COMPOSE) exec postgres psql -U petrosafe -d petrosafe -c "\dt metadata.*"
	@echo ""
	@echo "$(CYAN)── Tabelas no Schema audit ──$(NC)"
	@$(COMPOSE) exec postgres psql -U petrosafe -d petrosafe -c "\dt audit.*"

# ── Pipelines Medallion ────────────────────────────────────
bronze: ## Executa pipeline Bronze (ingestão)
	@echo "$(CYAN)▶ Executando pipeline Bronze...$(NC)"
	$(PYTHON) src/pipelines/bronze_ingestion.py
	@echo "$(GREEN)✓ Pipeline Bronze concluído$(NC)"

silver: ## Executa pipeline Silver (transformação)
	@echo "$(CYAN)▶ Executando pipeline Silver...$(NC)"
	$(PYTHON) src/pipelines/silver_transform.py
	@echo "$(GREEN)✓ Pipeline Silver concluído$(NC)"

gold: ## Executa pipeline Gold (curadoria)
	@echo "$(CYAN)▶ Executando pipeline Gold...$(NC)"
	$(PYTHON) src/pipelines/gold_curate.py
	@echo "$(GREEN)✓ Pipeline Gold concluído$(NC)"

pipeline-all: bronze silver gold ## Executa pipeline completo (Bronze → Silver → Gold)
	@echo "$(GREEN)✓ Pipeline Medallion completo$(NC)"

# ── ML / Treinamento ───────────────────────────────────────
train: ## Treina modelos e registra no MLflow
	@echo "$(CYAN)▶ Treinando modelos de classificação...$(NC)"
	$(PYTHON) -m src.models.train
	@echo "$(GREEN)✓ Treinamento concluído - verifique http://localhost:5000$(NC)"

evaluate: ## Avalia melhor modelo
	@echo "$(CYAN)▶ Avaliando melhor modelo...$(NC)"
	$(PYTHON) -m src.models.evaluate
	@echo "$(GREEN)✓ Avaliação concluída$(NC)"

train-all: train evaluate ## Pipeline completo (treino + avaliação)
	@echo "$(GREEN)✓ Pipeline ML completo$(NC)"

# ── Ollama / LLM ──────────────────────────────────────────
pull-model: ## Baixa modelo LLM no Ollama
	@echo "$(CYAN)▶ Baixando modelo llama3.2:3b...$(NC)"
	docker exec petrosafe-ollama ollama pull llama3.2:3b
	@echo "$(GREEN)✓ Modelo baixado$(NC)"

pull-embedding: ## Baixa modelo de embedding
	@echo "$(CYAN)▶ Baixando modelo nomic-embed-text...$(NC)"
	docker exec petrosafe-ollama ollama pull nomic-embed-text
	@echo "$(GREEN)✓ Modelo de embedding baixado$(NC)"

# ── Sprint 5: Embeddings ───────────────────────────────────
embed: ## Gera embeddings e indexa no Milvus
	@echo "$(CYAN)▶ Executando pipeline de embeddings...$(NC)"
	$(PYTHON) -m src.pipelines.embedding_pipeline
	@echo "$(GREEN)✓ Embeddings gerados e indexados$(NC)"

# ── Sprint 6: RAG ──────────────────────────────────────────
rag-query: ## Consulta RAG interativa
	@echo "$(CYAN)▶ Iniciando RAG query...$(NC)"
	$(PYTHON) -m src.pipelines.rag_query $(QUERY)

# ── Sprint 7: API ──────────────────────────────────────────
api: ## Inicia a API FastAPI (porta 8000)
	@echo "$(CYAN)▶ Iniciando API PetroSafe na porta 8000...$(NC)"
	$(PYTHON) -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

api-docs: ## Abre docs da API no navegador
	@echo "$(CYAN)▶ Abrindo Swagger UI...$(NC)"
	@xdg-open http://localhost:8000/docs 2>/dev/null || echo "  Acesse: http://localhost:8000/docs"

# ── Qualidade ──────────────────────────────────────────────
test: ## Roda testes
	@echo "$(CYAN)▶ Executando testes...$(NC)"
	$(PYTHON) -m pytest tests/ -v
	@echo "$(GREEN)✓ Testes concluídos$(NC)"

lint: ## Verifica qualidade do código
	$(PYTHON) -m ruff check src/ tests/

format: ## Formata código
	$(PYTHON) -m ruff format src/ tests/

# ── Limpeza ────────────────────────────────────────────────
clean: ## Remove containers e volumes
	@echo "$(RED)▶ Removendo containers e volumes...$(NC)"
	$(COMPOSE) down -v --remove-orphans
	@echo "$(GREEN)✓ Ambiente limpo$(NC)"

clean-data: ## Remove apenas dados (volumes)
	@echo "$(RED)▶ Removendo volumes de dados...$(NC)"
	$(COMPOSE) down -v
	@echo "$(GREEN)✓ Dados removidos$(NC)"

# ── Setup Inicial ──────────────────────────────────────────
setup: ## Setup completo do projeto (primeira vez)
	@echo "$(CYAN)╔══════════════════════════════════════════╗$(NC)"
	@echo "$(CYAN)║   Setup Inicial - PetroSafe Energia      ║$(NC)"
	@echo "$(CYAN)╚══════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(CYAN)1/4 Instalando dependências Python...$(NC)"
	pip install -r requirements.txt
	@echo "$(CYAN)2/4 Subindo infraestrutura...$(NC)"
	@$(MAKE) up
	@echo "$(CYAN)3/4 Aguardando serviços...$(NC)"
	sleep 15
	@echo "$(CYAN)4/4 Verificando serviços...$(NC)"
	@$(MAKE) status
	@echo ""
	@echo "$(GREEN)╔══════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║   ✓ Setup concluído com sucesso!         ║$(NC)"
	@echo "$(GREEN)║                                          ║$(NC)"
	@echo "$(GREEN)║   MinIO Console:  http://localhost:9001   ║$(NC)"
	@echo "$(GREEN)║   PostgreSQL:     localhost:5432           ║$(NC)"
	@echo "$(GREEN)║   MLflow:         http://localhost:5000   ║$(NC)"
	@echo "$(GREEN)║   Milvus:         localhost:19530          ║$(NC)"
	@echo "$(GREEN)║   Ollama:         http://localhost:11434  ║$(NC)"
	@echo "$(GREEN)╚══════════════════════════════════════════╝$(NC)"
