# 🏛️ Documentação de Governança de Dados — PetroSafe Energia

> Políticas, processos e controles para gestão de dados na plataforma RAG Enterprise.

---

## 1. Arquitetura Medallion

A plataforma utiliza a arquitetura Medallion (Bronze / Silver / Gold) para organizar os dados em camadas progressivas de qualidade e transformação.

### 1.1 Camada Bronze — Dados Brutos

**Objetivo:** Preservar os dados exatamente como foram recebidos da fonte.

| Aspecto | Especificação |
|---------|--------------|
| Bucket MinIO | `bronze` |
| Formato | Original (CSV, PDF, JSON, TXT) |
| Transformação | Nenhuma |
| Versionamento | Habilitado (MinIO versioning) |
| Retenção | Indefinida |
| Acesso | Equipe de Engenharia de Dados |

**Metadados capturados na ingestão:**
- Checksum MD5 do arquivo original
- Timestamp de upload
- Fonte de origem
- Número de registros (quando aplicável)
- Schema dos dados (colunas e tipos)
- Contagem de nulos por coluna

**Organização de paths:**
```
bronze/
  └── {dataset_nome}/
      └── {timestamp}/
          └── {arquivo_original}
```

### 1.2 Camada Silver — Dados Limpos

**Objetivo:** Dados limpos, padronizados e validados, prontos para análise.

| Aspecto | Especificação |
|---------|--------------|
| Bucket MinIO | `silver` |
| Formato | Parquet (colunar, otimizado) |
| Transformações | Limpeza, padronização, validação |
| Versionamento | Habilitado |
| Retenção | Indefinida |
| Acesso | Equipe de Dados + Engenharia |

**Transformações aplicadas:**
1. Remoção de registros duplicados
2. Padronização de nomes de colunas (snake_case)
3. Tratamento de valores nulos (string vazia, "N/A", "null" → NULL)
4. Inferência e conversão de tipos (numérico, datetime)
5. Validação de qualidade com score

**Métricas de qualidade registradas:**
- Completude (% de campos preenchidos)
- Score de qualidade geral
- Contagem de nulos por coluna
- Registros rejeitados durante transformação

### 1.3 Camada Gold — Dados Prontos para Consumo

**Objetivo:** Dados enriquecidos e estruturados para alimentar o pipeline RAG.

| Aspecto | Especificação |
|---------|--------------|
| Bucket MinIO | `gold` |
| Formato | JSON (documentos RAG) |
| Transformações | Enriquecimento, agregação, chunking |
| Versionamento | Habilitado |
| Retenção | Indefinida |
| Acesso | Pipeline RAG + API |

**Artefatos gerados:**
- Documentos textuais estruturados (prontos para embedding)
- Estatísticas agregadas por classe/evento
- Metadados enriquecidos para busca

---

## 2. Versionamento de Dados

### 2.1 Versionamento no MinIO
- Todos os buckets (bronze, silver, gold) têm versionamento habilitado
- Cada upload gera um `version_id` único do MinIO
- Arquivos nunca são sobrescritos — novas versões são criadas
- Possível acessar qualquer versão anterior

### 2.2 Versionamento no PostgreSQL
- Tabela `metadata.dataset_versoes` registra cada versão
- Semântica Semver (1.0.0, 1.1.0, 2.0.0)
- Constraint `UNIQUE(dataset_id, versao, camada)` garante unicidade
- Status: `ativo`, `arquivado`, `deprecado`
- `minio_version_id` vincula ao versionamento do MinIO

### 2.3 Política de Versionamento
| Mudança | Incremento | Exemplo |
|---------|-----------|---------|
| Nova ingestão sem mudança de schema | Patch (x.x.+1) | 1.0.0 → 1.0.1 |
| Mudança de transformação/limpeza | Minor (x.+1.0) | 1.0.0 → 1.1.0 |
| Mudança de schema/estrutura | Major (+1.0.0) | 1.0.0 → 2.0.0 |

---

## 3. Catálogo de Dados

### 3.1 Tabela `metadata.datasets`
Registro central de todos os datasets com:
- Nome e descrição
- Domínio (falhas, manutenção, documentação técnica, sensores)
- Formato de origem
- Fonte (URL ou referência interna)
- Licença
- Tags para busca
- Schema info (colunas, tipos) em JSONB

### 3.2 Domínios Cadastrados
| Domínio | Descrição | Responsável |
|---------|-----------|-------------|
| falhas_industriais | Dados de falhas e anomalias em poços | Eng. Confiabilidade |
| manutencao | Relatórios e procedimentos de manutenção | Manutenção Preventiva |
| documentacao_tecnica | Manuais, normas e documentação técnica | Eng. Projetos |
| sensores | Séries temporais de sensores IoT | Automação Industrial |

---

## 4. Linhagem de Dados (Data Lineage)

### 4.1 Rastreabilidade
Toda transformação de dados é rastreada via:
- **Tabela `metadata.pipelines`:** Definição dos pipelines
- **Tabela `metadata.pipeline_execucoes`:** Cada execução com:
  - Versão de origem e destino
  - Status (executando, sucesso, falha)
  - Timestamps de início e fim
  - Contagem de registros processados/rejeitados
  - Mensagens de erro (quando aplicável)

### 4.2 View `vw_linhagem`
Consulta consolidada que mostra o caminho completo dos dados:
```
Fonte → Bronze → Silver → Gold
```

---

## 5. Auditoria

### 5.1 Log de Auditoria
- Schema dedicado: `audit`
- Tabela `audit.log` captura automaticamente via triggers:
  - INSERT, UPDATE, DELETE em tabelas de metadados
  - Dados anteriores (para UPDATE/DELETE)
  - Dados novos (para INSERT/UPDATE)
  - Usuário e timestamp

### 5.2 Triggers Automáticos
Tabelas monitoradas:
- `metadata.datasets`
- `metadata.dataset_versoes`
- `metadata.pipeline_execucoes`

---

## 6. Qualidade de Dados

### 6.1 Regras de Qualidade
- Tabela `metadata.regras_qualidade` define validações por dataset
- Tipos: completude, unicidade, formato, range, custom
- Severidade: info, warning, error, critical

### 6.2 Resultados de Validação
- Tabela `metadata.validacao_resultados` registra cada execução
- Percentual de conformidade calculado automaticamente
- Detalhes em JSONB para análise

---

## 7. Controle de Acesso (Planejado)

| Camada | Leitura | Escrita |
|--------|---------|---------|
| Bronze | Eng. Dados | Pipeline de Ingestão |
| Silver | Eng. Dados + Analistas | Pipeline de Transformação |
| Gold | Todos (via API) | Pipeline de Curadoria |
| Metadados | Todos | Eng. Dados + DBA |
| Auditoria | DBA + Compliance | Sistema (triggers) |
