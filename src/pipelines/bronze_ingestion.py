"""
PetroSafe Energia - Pipeline Bronze (Ingestão)
Sprint 3 - Governança e Medallion

Ingestão de dados brutos para a camada Bronze do Data Lake.
Bronze = dados brutos, sem transformação, como chegaram da fonte.
"""

import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path

import pandas as pd
import structlog

# Adicionar raiz do projeto ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.config import get_settings
from src.utils.datalake import DataLakeClient
from src.utils.metadata import MetadataClient

logger = structlog.get_logger()


class BronzeIngestionPipeline:
    """
    Pipeline de ingestão para a camada Bronze.

    Responsabilidades:
    - Ler dados brutos de diversas fontes (CSV, JSON, PDF, TXT)
    - Armazenar no MinIO bucket 'bronze' sem transformação
    - Registrar metadados no PostgreSQL
    - Manter versionamento dos dados ingeridos
    """

    def __init__(self):
        self.datalake = DataLakeClient()
        self.metadata = MetadataClient()
        self.settings = get_settings()
        self.timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    def ingerir_csv(self, filepath: str, dataset_nome: str, versao: str = "1.0.0") -> dict:
        """Ingere um arquivo CSV para a camada Bronze."""
        logger.info("bronze_csv_inicio", arquivo=filepath, dataset=dataset_nome)

        # Ler arquivo original (sem transformação)
        with open(filepath, "rb") as f:
            raw_data = f.read()

        # Contar registros para metadados
        df = pd.read_csv(filepath)
        num_registros = len(df)

        # Definir path no Data Lake
        nome_arquivo = Path(filepath).name
        minio_path = f"{dataset_nome}/{self.timestamp}/{nome_arquivo}"

        # Upload para Bronze
        result = self.datalake.upload(
            camada="bronze",
            path=minio_path,
            data=raw_data,
            content_type="text/csv",
            metadata={
                "dataset": dataset_nome,
                "versao": versao,
                "fonte": filepath,
                "num_registros": str(num_registros),
                "colunas": ",".join(df.columns.tolist()),
            },
        )

        # Registrar metadados
        versao_id = self.metadata.registrar_versao_dataset(
            dataset_nome=dataset_nome,
            versao=versao,
            camada="bronze",
            caminho_minio=f"bronze/{minio_path}",
            minio_version_id=result.get("version_id"),
            tamanho_bytes=result["tamanho_bytes"],
            num_registros=num_registros,
            checksum_md5=result["checksum_md5"],
            metadados_qualidade={
                "colunas": df.columns.tolist(),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "nulos_por_coluna": df.isnull().sum().to_dict(),
                "shape": list(df.shape),
            },
        )

        logger.info(
            "bronze_csv_concluido",
            dataset=dataset_nome,
            registros=num_registros,
            versao_id=versao_id,
        )

        return {
            "versao_id": versao_id,
            "minio_path": minio_path,
            "num_registros": num_registros,
            **result,
        }

    def ingerir_documento(self, filepath: str, dataset_nome: str, versao: str = "1.0.0") -> dict:
        """Ingere um documento (PDF, TXT, MD) para a camada Bronze."""
        logger.info("bronze_doc_inicio", arquivo=filepath, dataset=dataset_nome)

        with open(filepath, "rb") as f:
            raw_data = f.read()

        ext = Path(filepath).suffix.lower()
        content_types = {
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".json": "application/json",
        }

        nome_arquivo = Path(filepath).name
        minio_path = f"{dataset_nome}/{self.timestamp}/{nome_arquivo}"

        result = self.datalake.upload(
            camada="bronze",
            path=minio_path,
            data=raw_data,
            content_type=content_types.get(ext, "application/octet-stream"),
            metadata={
                "dataset": dataset_nome,
                "versao": versao,
                "tipo_documento": ext,
                "fonte": filepath,
            },
        )

        versao_id = self.metadata.registrar_versao_dataset(
            dataset_nome=dataset_nome,
            versao=versao,
            camada="bronze",
            caminho_minio=f"bronze/{minio_path}",
            minio_version_id=result.get("version_id"),
            tamanho_bytes=result["tamanho_bytes"],
            checksum_md5=result["checksum_md5"],
        )

        logger.info("bronze_doc_concluido", dataset=dataset_nome, versao_id=versao_id)

        return {"versao_id": versao_id, "minio_path": minio_path, **result}

    def ingerir_diretorio(self, dirpath: str, dataset_nome: str, versao: str = "1.0.0") -> list[dict]:
        """Ingere todos os arquivos de um diretório."""
        resultados = []
        dirpath = Path(dirpath)

        for arquivo in sorted(dirpath.rglob("*")):
            if arquivo.is_file() and not arquivo.name.startswith("."):
                ext = arquivo.suffix.lower()
                try:
                    if ext == ".csv":
                        r = self.ingerir_csv(str(arquivo), dataset_nome, versao)
                    else:
                        r = self.ingerir_documento(str(arquivo), dataset_nome, versao)
                    resultados.append(r)
                except Exception as e:
                    logger.error("bronze_erro_arquivo", arquivo=str(arquivo), erro=str(e))

        logger.info(
            "bronze_diretorio_concluido",
            diretorio=str(dirpath),
            total_arquivos=len(resultados),
        )
        return resultados


# ── Execução direta ──────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pipeline Bronze - Ingestão de dados")
    parser.add_argument("--source", required=True, help="Caminho do arquivo ou diretório")
    parser.add_argument("--dataset", required=True, help="Nome do dataset no catálogo")
    parser.add_argument("--versao", default="1.0.0", help="Versão do dataset (semver)")
    args = parser.parse_args()

    pipeline = BronzeIngestionPipeline()

    source = Path(args.source)
    if source.is_dir():
        results = pipeline.ingerir_diretorio(str(source), args.dataset, args.versao)
        print(f"\n✓ {len(results)} arquivos ingeridos na camada Bronze")
    elif source.suffix.lower() == ".csv":
        result = pipeline.ingerir_csv(str(source), args.dataset, args.versao)
        print(f"\n✓ CSV ingerido: {result['num_registros']} registros")
    else:
        result = pipeline.ingerir_documento(str(source), args.dataset, args.versao)
        print(f"\n✓ Documento ingerido: {result['minio_path']}")
