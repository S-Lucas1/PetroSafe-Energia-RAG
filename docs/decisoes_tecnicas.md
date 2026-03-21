# 🔧 Justificativa das Decisões Técnicas — PetroSafe Energia

---

## 1. Escolha do Domínio e Dataset

### Decisão: Energia — Falhas Industriais (Dataset 3W da Petrobras)

**Justificativa:**
- **Relevância real:** O 3W é um dataset público com dados reais de operação de poços de petróleo, não dados sintéticos
- **Riqueza de dados:** Combina séries temporais de sensores (dados estruturados) com a possibilidade de documentos técnicos (dados não-estruturados), ideal para demonstrar RAG
- **Complexidade adequada:** 8 classes de falhas com padrões distintos permitem consultas ricas em linguagem natural
- **Licença aberta:** CC BY 4.0 permite uso acadêmico
- **Domínio crítico:** Falhas em poços de petróleo têm impacto econômico e ambiental significativo, justificando uma plataforma de governança

**Alternativas consideradas:**
- Saúde: Restrições de privacidade dificultariam demonstração com dados reais
- Finanças: Dados públicos geralmente são agregados, limitando RAG
- Agricultura: Menos complexidade nos padrões de falha

---

## 2. Arquitetura Medallion (Bronze / Silver / Gold)

### Decisão: Implementar 3 camadas no MinIO com versionamento

**Justificativa:**
- **Padrão de mercado:** Arquitetura Medallion é o padrão estabelecido por Databricks e amplamente adotado em Data Lakehouses
- **Rastreabilidade:** Cada camada preserva um estágio dos dados, permitindo reprocessamento a partir de qualquer ponto
- **Separação de responsabilidades:** Bronze (ingestão), Silver (qualidade), Gold (consumo) — cada pipeline tem escopo definido
- **Versionamento nativo:** MinIO suporta versionamento de objetos nativamente, sem necessidade de ferramentas adicionais

**Alternativas consideradas:**
- Camada única com tags: Menor complexidade, mas sem rastreabilidade
- Delta Lake: Exigiria Spark, aumentando significativamente os requisitos de infraestrutura

---

## 3. MinIO como Data Lake

### Decisão: MinIO para armazenamento de objetos

**Justificativa:**
- **Compatível com S3:** API 100% compatível com Amazon S3, facilitando migração futura para cloud
- **Self-hosted:** Roda localmente em Docker, sem dependência de cloud
- **Versionamento:** Suporte nativo a versionamento de objetos
- **Leve:** Imagem Docker pequena, baixo consumo de recursos
- **Console web:** Interface gráfica para visualização dos dados
- **Integração MLflow:** MLflow suporta MinIO como artifact store via protocolo S3

**Alternativas consideradas:**
- AWS S3: Custo e dependência de cloud
- HDFS: Complexidade excessiva para o escopo do projeto
- Sistema de arquivos local: Sem versionamento, sem API padrão

---

## 4. PostgreSQL para Metadados

### Decisão: PostgreSQL 16 com schemas dedicados (metadata, audit)

**Justificativa:**
- **Maturidade:** Banco relacional mais robusto do ecossistema open-source
- **JSONB:** Suporte nativo a JSON binário para metadados flexíveis (schema_info, métricas de qualidade)
- **Extensões:** uuid-ossp para IDs únicos, pgcrypto para segurança
- **Triggers:** Suporte nativo a triggers para auditoria automática
- **Integração MLflow:** MLflow usa PostgreSQL como backend store nativamente
- **Schema separation:** Schemas `metadata` e `audit` organizam logicamente as tabelas

**Alternativas consideradas:**
- MySQL: Suporte inferior a JSONB e extensões
- MongoDB: Desnecessário para metadados estruturados, adicionaria complexidade
- SQLite: Sem suporte a concorrência, inadequado para produção

---

## 5. Milvus como Banco Vetorial

### Decisão: Milvus standalone com etcd + MinIO dedicado

**Justificativa:**
- **Performance:** Otimizado para busca vetorial em larga escala (milhões de vetores)
- **Índices:** Suporte a IVF_FLAT, HNSW e outros índices de busca aproximada
- **Escalável:** Arquitetura que escala de standalone para cluster distribuído
- **Open-source:** Projeto CNCF com comunidade ativa
- **Metadados:** Suporte a filtragem por metadados junto com busca vetorial (hybrid search)

**Alternativas consideradas:**
- ChromaDB: Mais simples, mas menos performático em escala
- Pinecone: Managed service, sem opção self-hosted
- pgvector: Funcional, mas performance inferior para volume alto de vetores
- FAISS: Biblioteca, não servidor — sem persistência nativa

---

## 6. Ollama para LLM Local

### Decisão: Ollama com Llama 3.2 (3B) e nomic-embed-text

**Justificativa:**
- **Privacidade:** Dados industriais sensíveis processados localmente, sem enviar para APIs externas
- **Custo zero:** Sem custos de API por token
- **Simplicidade:** Ollama abstrai a complexidade de servir modelos LLM
- **Modelos:** Llama 3.2 3B oferece boa relação qualidade/tamanho para RAG
- **Embeddings:** nomic-embed-text é otimizado para embedding de documentos, com 768 dimensões
- **Docker-native:** Imagem Docker oficial, fácil integração com Docker Compose

**Alternativas consideradas:**
- OpenAI API: Custo por token e dependência de serviço externo
- Hugging Face local: Mais complexo de configurar e servir
- LM Studio: Sem API programática adequada

---

## 7. MLflow para Experiment Tracking

### Decisão: MLflow com PostgreSQL backend e MinIO artifact store

**Justificativa:**
- **Padrão de mercado:** Ferramenta mais adotada para MLOps
- **Integração natural:** Usa PostgreSQL (já existente) como backend e MinIO como artifact store
- **Tracking completo:** Registra parâmetros, métricas, artefatos e modelos
- **UI web:** Dashboard para visualização de experimentos
- **Model registry:** Versionamento de modelos para futuras iterações do RAG

**Alternativas consideradas:**
- Weights & Biases: Requer conta online (embora tenha self-hosted)
- Neptune.ai: SaaS, não self-hosted
- Planilha manual: Sem automação nem reprodutibilidade

---

## 8. FastAPI para API

### Decisão: FastAPI com documentação OpenAPI automática

**Justificativa:**
- **Performance:** Framework ASGI assíncrono, ideal para I/O-bound (consultas RAG)
- **Documentação automática:** Gera Swagger UI e ReDoc a partir do código
- **Tipagem:** Integração nativa com Pydantic para validação de dados
- **Padrão de mercado:** Framework Python mais adotado para APIs modernas
- **Async:** Suporte nativo a async/await para chamadas a Ollama e Milvus

**Alternativas consideradas:**
- Flask: Síncrono, sem tipagem nativa, sem docs automáticas
- Django REST Framework: Overhead excessivo para uma API focada
- gRPC: Complexidade desnecessária para o escopo

---

## 9. Docker Compose para Orquestração

### Decisão: Docker Compose v2 com healthchecks e dependências

**Justificativa:**
- **Reprodutibilidade:** Qualquer pessoa inicia todo o ambiente com `make up`
- **Isolamento:** Rede dedicada `petrosafe-net` isola os serviços
- **Healthchecks:** Dependências aguardam serviços ficarem saudáveis antes de iniciar
- **Simplicidade:** Um único arquivo define toda a infraestrutura
- **Volumes nomeados:** Dados persistem entre restarts

**Alternativas consideradas:**
- Kubernetes: Complexidade excessiva para ambiente de desenvolvimento/acadêmico
- Docker manual: Sem orquestração de dependências
- Podman Compose: Menor adoção, possíveis incompatibilidades

---

## 10. Makefile para Automação

### Decisão: Makefile com comandos coloridos e categorizados

**Justificativa:**
- **Universal:** Make está disponível em todos os sistemas Unix-like
- **Autodocumentação:** `make help` lista todos os comandos com descrições
- **Composabilidade:** Comandos podem chamar outros comandos (ex: `setup` chama `up`)
- **Padronização:** Time inteiro usa os mesmos comandos
- **Zero dependências:** Não requer instalação de ferramentas adicionais

**Alternativas consideradas:**
- Task (Taskfile): Mais moderno, mas requer instalação
- Scripts bash: Menos organizados, sem autodocumentação
- Just: Menos universal que Make

---

## 11. Formato Parquet na Camada Silver

### Decisão: Parquet como formato padrão da camada Silver

**Justificativa:**
- **Colunar:** Leitura eficiente de subconjuntos de colunas
- **Compressão:** Redução significativa de tamanho vs CSV
- **Tipagem:** Preserva tipos de dados (datetime, numeric) sem ambiguidade
- **Padrão:** Formato padrão em pipelines de dados modernos
- **Compatível:** pandas, Spark, DuckDB leem Parquet nativamente

---

## 12. Schema PostgreSQL com Schemas Separados

### Decisão: `metadata` para catálogo e `audit` para auditoria

**Justificativa:**
- **Separação lógica:** Metadados de negócio vs logs de auditoria têm ciclos de vida diferentes
- **Controle de acesso:** Possibilidade de permissões distintas por schema
- **Organização:** `\dt metadata.*` lista apenas tabelas de metadados
- **Escalabilidade:** Auditoria pode crescer indefinidamente sem impactar queries de metadados
