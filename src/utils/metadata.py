"""
PetroSafe Energia - Cliente de Metadados (PostgreSQL)
Gerencia catálogo de datasets, versionamento e linhagem.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import structlog

from src.utils.config import get_settings

logger = structlog.get_logger()


class MetadataClient:
    """Cliente para operações de metadados no PostgreSQL."""

    def __init__(self):
        settings = get_settings()
        self.engine = create_engine(settings.postgres_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)

    def registrar_versao_dataset(
        self,
        dataset_nome: str,
        versao: str,
        camada: str,
        caminho_minio: str,
        minio_version_id: Optional[str] = None,
        tamanho_bytes: Optional[int] = None,
        num_registros: Optional[int] = None,
        checksum_md5: Optional[str] = None,
        metadados_qualidade: Optional[dict] = None,
    ) -> str:
        """Registra uma nova versão de dataset no catálogo."""
        with self.Session() as session:
            # Buscar dataset_id pelo nome
            result = session.execute(
                text("SELECT id FROM metadata.datasets WHERE nome = :nome"),
                {"nome": dataset_nome},
            )
            row = result.fetchone()
            if not row:
                raise ValueError(f"Dataset '{dataset_nome}' não encontrado no catálogo")

            dataset_id = row[0]
            versao_id = str(uuid.uuid4())

            session.execute(
                text("""
                    INSERT INTO metadata.dataset_versoes
                        (id, dataset_id, versao, camada, caminho_minio, minio_version_id,
                         tamanho_bytes, num_registros, checksum_md5, metadados_qualidade)
                    VALUES
                        (:id, :dataset_id, :versao, :camada, :caminho_minio, :minio_version_id,
                         :tamanho_bytes, :num_registros, :checksum_md5, :metadados_qualidade::jsonb)
                """),
                {
                    "id": versao_id,
                    "dataset_id": dataset_id,
                    "versao": versao,
                    "camada": camada,
                    "caminho_minio": caminho_minio,
                    "minio_version_id": minio_version_id,
                    "tamanho_bytes": tamanho_bytes,
                    "num_registros": num_registros,
                    "checksum_md5": checksum_md5,
                    "metadados_qualidade": str(metadados_qualidade) if metadados_qualidade else None,
                },
            )
            session.commit()

            logger.info(
                "versao_registrada",
                dataset=dataset_nome,
                versao=versao,
                camada=camada,
            )
            return versao_id

    def registrar_execucao_pipeline(
        self,
        pipeline_nome: str,
        versao_origem_id: Optional[str] = None,
        versao_destino_id: Optional[str] = None,
    ) -> str:
        """Registra o início de uma execução de pipeline."""
        with self.Session() as session:
            result = session.execute(
                text("SELECT id FROM metadata.pipelines WHERE nome = :nome"),
                {"nome": pipeline_nome},
            )
            row = result.fetchone()
            if not row:
                raise ValueError(f"Pipeline '{pipeline_nome}' não encontrado")

            execucao_id = str(uuid.uuid4())
            session.execute(
                text("""
                    INSERT INTO metadata.pipeline_execucoes
                        (id, pipeline_id, dataset_versao_origem_id, dataset_versao_destino_id, status)
                    VALUES (:id, :pipeline_id, :origem_id, :destino_id, 'executando')
                """),
                {
                    "id": execucao_id,
                    "pipeline_id": row[0],
                    "origem_id": versao_origem_id,
                    "destino_id": versao_destino_id,
                },
            )
            session.commit()
            return execucao_id

    def finalizar_execucao_pipeline(
        self,
        execucao_id: str,
        status: str,
        registros_processados: Optional[int] = None,
        registros_rejeitados: Optional[int] = None,
        erro_mensagem: Optional[str] = None,
    ):
        """Finaliza uma execução de pipeline."""
        with self.Session() as session:
            session.execute(
                text("""
                    UPDATE metadata.pipeline_execucoes
                    SET status = :status,
                        fim = NOW(),
                        duracao_segundos = EXTRACT(EPOCH FROM (NOW() - inicio)),
                        registros_processados = :processados,
                        registros_rejeitados = :rejeitados,
                        erro_mensagem = :erro
                    WHERE id = :id
                """),
                {
                    "id": execucao_id,
                    "status": status,
                    "processados": registros_processados,
                    "rejeitados": registros_rejeitados,
                    "erro": erro_mensagem,
                },
            )
            session.commit()

    def listar_datasets(self) -> list[dict]:
        """Lista todos os datasets do catálogo."""
        with self.Session() as session:
            result = session.execute(
                text("""
                    SELECT d.nome, d.descricao, dom.nome as dominio,
                           d.formato_origem, d.tags, d.criado_em
                    FROM metadata.datasets d
                    JOIN metadata.dominios dom ON d.dominio_id = dom.id
                    ORDER BY d.nome
                """)
            )
            return [
                {
                    "nome": r[0],
                    "descricao": r[1],
                    "dominio": r[2],
                    "formato": r[3],
                    "tags": r[4],
                    "criado_em": r[5].isoformat() if r[5] else None,
                }
                for r in result.fetchall()
            ]

    def obter_linhagem(self, dataset_nome: str) -> list[dict]:
        """Obtém a linhagem completa de um dataset."""
        with self.Session() as session:
            result = session.execute(
                text("""
                    SELECT * FROM metadata.vw_linhagem
                    WHERE origem_path LIKE :pattern OR destino_path LIKE :pattern
                    ORDER BY inicio DESC
                """),
                {"pattern": f"%{dataset_nome}%"},
            )
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]
