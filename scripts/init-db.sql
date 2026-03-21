-- ============================================================
-- PetroSafe Energia - Schema de Metadados (Sprint 4)
-- Controle de Datasets, Versionamento e Auditoria
-- ============================================================

-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Schema principal ─────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS metadata;
CREATE SCHEMA IF NOT EXISTS audit;

-- ============================================================
-- TABELAS DE METADADOS DE DATASETS
-- ============================================================

-- Domínios de dados
CREATE TABLE metadata.dominios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nome VARCHAR(100) NOT NULL UNIQUE,
    descricao TEXT,
    responsavel VARCHAR(200),
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Datasets catalogados
CREATE TABLE metadata.datasets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    dominio_id UUID REFERENCES metadata.dominios(id),
    formato_origem VARCHAR(50) NOT NULL, -- csv, json, parquet, pdf, txt
    fonte VARCHAR(500),                   -- URL ou caminho de origem
    licenca VARCHAR(200),
    tags TEXT[],
    schema_info JSONB,                    -- Schema dos dados (colunas, tipos)
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    criado_por VARCHAR(200) DEFAULT 'system'
);

-- Versões dos datasets (rastreabilidade)
CREATE TABLE metadata.dataset_versoes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dataset_id UUID NOT NULL REFERENCES metadata.datasets(id) ON DELETE CASCADE,
    versao VARCHAR(20) NOT NULL,          -- semver: 1.0.0, 1.1.0
    camada VARCHAR(10) NOT NULL CHECK (camada IN ('bronze', 'silver', 'gold')),
    caminho_minio VARCHAR(500) NOT NULL,  -- path completo no MinIO
    minio_version_id VARCHAR(200),        -- version ID do MinIO
    tamanho_bytes BIGINT,
    num_registros BIGINT,
    checksum_md5 VARCHAR(32),
    status VARCHAR(20) DEFAULT 'ativo' CHECK (status IN ('ativo', 'arquivado', 'deprecado')),
    metadados_qualidade JSONB,            -- métricas de qualidade
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    criado_por VARCHAR(200) DEFAULT 'system',
    UNIQUE(dataset_id, versao, camada)
);

-- ============================================================
-- TABELAS DE PIPELINE / LINHAGEM
-- ============================================================

-- Pipelines de transformação
CREATE TABLE metadata.pipelines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    tipo VARCHAR(50) NOT NULL CHECK (tipo IN ('ingestao', 'transformacao', 'embedding', 'indexacao')),
    camada_origem VARCHAR(10) CHECK (camada_origem IN ('raw', 'bronze', 'silver', 'gold')),
    camada_destino VARCHAR(10) CHECK (camada_destino IN ('bronze', 'silver', 'gold')),
    script_path VARCHAR(500),
    parametros JSONB,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Execuções de pipeline (data lineage)
CREATE TABLE metadata.pipeline_execucoes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pipeline_id UUID NOT NULL REFERENCES metadata.pipelines(id),
    dataset_versao_origem_id UUID REFERENCES metadata.dataset_versoes(id),
    dataset_versao_destino_id UUID REFERENCES metadata.dataset_versoes(id),
    status VARCHAR(20) DEFAULT 'executando' CHECK (status IN ('executando', 'sucesso', 'falha', 'cancelado')),
    inicio TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    fim TIMESTAMP WITH TIME ZONE,
    duracao_segundos NUMERIC(10,2),
    registros_processados BIGINT,
    registros_rejeitados BIGINT,
    erro_mensagem TEXT,
    log_path VARCHAR(500),
    metricas JSONB
);

-- ============================================================
-- TABELAS DE GOVERNANÇA
-- ============================================================

-- Regras de qualidade de dados
CREATE TABLE metadata.regras_qualidade (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dataset_id UUID NOT NULL REFERENCES metadata.datasets(id),
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    tipo VARCHAR(50) NOT NULL CHECK (tipo IN ('completude', 'unicidade', 'formato', 'range', 'custom')),
    expressao TEXT NOT NULL,              -- SQL ou expressão de validação
    severidade VARCHAR(20) DEFAULT 'warning' CHECK (severidade IN ('info', 'warning', 'error', 'critical')),
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Resultados de validação
CREATE TABLE metadata.validacao_resultados (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    regra_id UUID NOT NULL REFERENCES metadata.regras_qualidade(id),
    dataset_versao_id UUID NOT NULL REFERENCES metadata.dataset_versoes(id),
    passou BOOLEAN NOT NULL,
    total_registros BIGINT,
    registros_validos BIGINT,
    registros_invalidos BIGINT,
    percentual_conformidade NUMERIC(5,2),
    detalhes JSONB,
    executado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- TABELAS DE AUDITORIA
-- ============================================================

-- Log de auditoria geral
CREATE TABLE audit.log (
    id BIGSERIAL PRIMARY KEY,
    tabela VARCHAR(100) NOT NULL,
    operacao VARCHAR(10) NOT NULL CHECK (operacao IN ('INSERT', 'UPDATE', 'DELETE')),
    registro_id UUID,
    dados_anteriores JSONB,
    dados_novos JSONB,
    usuario VARCHAR(200) DEFAULT current_user,
    ip_address INET,
    executado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- FUNÇÕES E TRIGGERS
-- ============================================================

-- Função para atualizar timestamp
CREATE OR REPLACE FUNCTION metadata.atualizar_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger de atualização automática
CREATE TRIGGER trg_datasets_atualizar
    BEFORE UPDATE ON metadata.datasets
    FOR EACH ROW EXECUTE FUNCTION metadata.atualizar_timestamp();

CREATE TRIGGER trg_dominios_atualizar
    BEFORE UPDATE ON metadata.dominios
    FOR EACH ROW EXECUTE FUNCTION metadata.atualizar_timestamp();

CREATE TRIGGER trg_pipelines_atualizar
    BEFORE UPDATE ON metadata.pipelines
    FOR EACH ROW EXECUTE FUNCTION metadata.atualizar_timestamp();

-- Função de auditoria genérica
CREATE OR REPLACE FUNCTION audit.registrar_alteracao()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit.log (tabela, operacao, registro_id, dados_anteriores)
        VALUES (TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME, TG_OP, OLD.id, to_jsonb(OLD));
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit.log (tabela, operacao, registro_id, dados_anteriores, dados_novos)
        VALUES (TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME, TG_OP, NEW.id, to_jsonb(OLD), to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit.log (tabela, operacao, registro_id, dados_novos)
        VALUES (TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME, TG_OP, NEW.id, to_jsonb(NEW));
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Triggers de auditoria
CREATE TRIGGER trg_audit_datasets
    AFTER INSERT OR UPDATE OR DELETE ON metadata.datasets
    FOR EACH ROW EXECUTE FUNCTION audit.registrar_alteracao();

CREATE TRIGGER trg_audit_dataset_versoes
    AFTER INSERT OR UPDATE OR DELETE ON metadata.dataset_versoes
    FOR EACH ROW EXECUTE FUNCTION audit.registrar_alteracao();

CREATE TRIGGER trg_audit_pipeline_execucoes
    AFTER INSERT OR UPDATE OR DELETE ON metadata.pipeline_execucoes
    FOR EACH ROW EXECUTE FUNCTION audit.registrar_alteracao();

-- ============================================================
-- VIEWS ÚTEIS
-- ============================================================

-- Visão consolidada dos datasets com última versão
CREATE VIEW metadata.vw_datasets_ultima_versao AS
SELECT
    d.id AS dataset_id,
    d.nome AS dataset_nome,
    d.descricao,
    dom.nome AS dominio,
    dv.versao,
    dv.camada,
    dv.caminho_minio,
    dv.tamanho_bytes,
    dv.num_registros,
    dv.status,
    dv.criado_em AS versao_criada_em
FROM metadata.datasets d
JOIN metadata.dominios dom ON d.dominio_id = dom.id
JOIN metadata.dataset_versoes dv ON d.id = dv.dataset_id
WHERE dv.criado_em = (
    SELECT MAX(dv2.criado_em)
    FROM metadata.dataset_versoes dv2
    WHERE dv2.dataset_id = d.id
      AND dv2.camada = dv.camada
      AND dv2.status = 'ativo'
);

-- Visão de linhagem (data lineage)
CREATE VIEW metadata.vw_linhagem AS
SELECT
    pe.id AS execucao_id,
    p.nome AS pipeline,
    p.tipo AS tipo_pipeline,
    p.camada_origem,
    p.camada_destino,
    dvo.caminho_minio AS origem_path,
    dvd.caminho_minio AS destino_path,
    pe.status,
    pe.inicio,
    pe.fim,
    pe.registros_processados,
    pe.registros_rejeitados
FROM metadata.pipeline_execucoes pe
JOIN metadata.pipelines p ON pe.pipeline_id = p.id
LEFT JOIN metadata.dataset_versoes dvo ON pe.dataset_versao_origem_id = dvo.id
LEFT JOIN metadata.dataset_versoes dvd ON pe.dataset_versao_destino_id = dvd.id;

-- ============================================================
-- DADOS INICIAIS (SEED)
-- ============================================================

-- Domínios
INSERT INTO metadata.dominios (nome, descricao, responsavel) VALUES
    ('falhas_industriais', 'Dados de falhas e anomalias em poços de petróleo', 'Equipe de Engenharia de Confiabilidade'),
    ('manutencao', 'Relatórios e procedimentos de manutenção', 'Equipe de Manutenção Preventiva'),
    ('documentacao_tecnica', 'Manuais, normas e documentação técnica', 'Equipe de Engenharia de Projetos'),
    ('sensores', 'Dados de séries temporais de sensores IoT', 'Equipe de Automação Industrial');

-- Pipelines padrão
INSERT INTO metadata.pipelines (nome, descricao, tipo, camada_origem, camada_destino, script_path) VALUES
    ('ingestao_raw_bronze', 'Ingestão de dados brutos para camada Bronze', 'ingestao', 'raw', 'bronze', 'src/pipelines/bronze_ingestion.py'),
    ('transformacao_bronze_silver', 'Limpeza e padronização Bronze → Silver', 'transformacao', 'bronze', 'silver', 'src/pipelines/silver_transform.py'),
    ('curadoria_silver_gold', 'Enriquecimento e curadoria Silver → Gold', 'transformacao', 'silver', 'gold', 'src/pipelines/gold_curate.py'),
    ('embedding_gold', 'Geração de embeddings dos documentos Gold', 'embedding', 'gold', 'gold', 'src/pipelines/embedding_pipeline.py'),
    ('indexacao_milvus', 'Indexação dos embeddings no Milvus', 'indexacao', 'gold', 'gold', 'src/pipelines/indexing_pipeline.py');

-- Datasets exemplo
INSERT INTO metadata.datasets (nome, descricao, dominio_id, formato_origem, fonte, licenca, tags, schema_info) VALUES
    (
        '3W Dataset - Falhas em Poços',
        'Dataset público da Petrobras com dados reais de falhas em poços de petróleo, incluindo séries temporais de sensores e classificação de eventos',
        (SELECT id FROM metadata.dominios WHERE nome = 'falhas_industriais'),
        'csv',
        'https://github.com/petrobras/3W',
        'CC BY 4.0',
        ARRAY['petrobras', '3w', 'falhas', 'poços', 'séries_temporais'],
        '{"colunas": ["timestamp", "P-PDG", "P-TPT", "T-TPT", "P-MON-CKP", "T-JUS-CKP", "P-JUS-CKGL", "QGL", "class"], "tipo_dados": "série temporal", "frequencia": "1s"}'::jsonb
    ),
    (
        'Procedimentos Operacionais',
        'Documentos de procedimentos operacionais padrão para manutenção e operação de poços',
        (SELECT id FROM metadata.dominios WHERE nome = 'manutencao'),
        'pdf',
        'interno',
        'Proprietário',
        ARRAY['procedimentos', 'SOP', 'manutenção', 'operação'],
        '{"tipo_documento": "PDF", "idioma": "pt-BR"}'::jsonb
    ),
    (
        'Manuais Técnicos de Equipamentos',
        'Documentação técnica de bombas, válvulas, sensores e equipamentos de poço',
        (SELECT id FROM metadata.dominios WHERE nome = 'documentacao_tecnica'),
        'pdf',
        'interno',
        'Proprietário',
        ARRAY['manuais', 'equipamentos', 'bombas', 'válvulas'],
        '{"tipo_documento": "PDF", "idioma": "pt-BR"}'::jsonb
    );

RAISE NOTICE 'Schema de metadados PetroSafe criado com sucesso!';
